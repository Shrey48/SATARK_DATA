"""
Trading analytics — transaction scoring and reporting.

SECURITY ANNOTATIONS (for SATARK property detection):
  execute_raw_query   — has_raw_query=true  (taint SINK — raw SQL via psycopg2)
  analyze_transaction — sensitivity_class=pii (handles PII + financial data)
  compute_risk_score  — internal; uses parameterized SQL only (NOT a taint sink)
"""
import os
import boto3
import psycopg2


DYNAMODB = boto3.client("dynamodb", region_name="us-east-1")
PG_CONN  = None   # initialised at startup


def _get_db():
    global PG_CONN
    if not PG_CONN:
        PG_CONN = psycopg2.connect(os.environ.get("PG_CONN_STRING", ""))
    return PG_CONN


# ─── TAINT SINK ───────────────────────────────────────────────────────────────

def execute_raw_query(query: str) -> list:
    """
    TAINT SINK — has_raw_query=true.
    Executes a raw SQL query string with NO parameterization.

    Called from:
      - search_transactions (NO sanitizer on that path → E_taint_path)
    Should NOT be called from sanitized paths.

    VULNERABLE: user-supplied `query` is injected directly into psycopg2.
    sensitivity_class: financial (accesses trading records with financial data)
    """
    cur = _get_db().cursor()
    cur.execute(query)          # SQL injection vector
    return cur.fetchall()


# ─── PII/FINANCIAL DATA HANDLER ───────────────────────────────────────────────

def analyze_transaction(clean_tx_id: str) -> dict:
    """
    Reads a transaction record from DynamoDB.
    Called ONLY from get_fraud_score (which calls sanitize_transaction_id first).
    pc_sanitization: sanitized (sanitizer is upstream).
    sensitivity_class: pii   (contains sender/receiver PII + financial data)
    """
    response = DYNAMODB.get_item(
        TableName=os.environ.get("TRANSACTIONS_TABLE_KEY", "apex-transactions-prod"),
        Key={"transaction_id": {"S": clean_tx_id}},
    )
    item = response.get("Item", {})
    return {
        "tx_id":     item.get("transaction_id", {}).get("S", ""),
        "amount":    item.get("amount", {}).get("N", "0"),
        "sender":    item.get("sender_id", {}).get("S", ""),     # PII
        "receiver":  item.get("receiver_id", {}).get("S", ""),   # PII
        "merchant":  item.get("merchant_code", {}).get("S", ""),
    }


# ─── INTERNAL — PARAMETERIZED QUERIES ONLY ────────────────────────────────────

def compute_risk_score(tx_data: dict) -> float:
    """
    Computes a ML-based fraud risk score.
    INTERNAL — called only from analyze_transaction, never from a route directly.

    Uses PARAMETERIZED queries only — NOT a taint sink.
    pc_sanitization: sanitized (data arrived from a sanitized path).
    pc_reachability: reachable from get_fraud_score entry point (2 hops).
    sensitivity_class: financial

    FALSE POSITIVE CANDIDATE:
      Scanners commonly flag this as "SQL injection" because it calls DB.
      The graph shows: (1) not a direct entry point, (2) sanitized upstream,
      (3) uses parameterised %s placeholders — triage should downgrade to LOW.
    """
    merchant = tx_data.get("merchant", "")
    amount   = float(tx_data.get("amount", 0))
    cur = _get_db().cursor()
    # SAFE: parameterized placeholder, not string interpolation
    cur.execute(
        "SELECT avg_tx_amount, fraud_rate FROM merchant_stats WHERE merchant_code = %s",
        (merchant,)
    )
    row = cur.fetchone()
    if not row:
        return 0.5
    avg_amt, fraud_rate = row
    deviation = abs(amount - avg_amt) / max(avg_amt, 1)
    return min(1.0, float(fraud_rate) + deviation * 0.3)


def compute_rolling_average(data: list, window: int = 7) -> float:
    """
    Pure math utility — computes a rolling average.
    INTERNAL — called only from batch_processor.
    Not reachable from any HTTP entry point.
    sensitivity_class: none

    FALSE POSITIVE CANDIDATE:
      Scanners may flag "weak cryptography" (CWE-327) on files that import
      cryptography libraries. This function does NOT use cryptography.
      Triage should score INFO (unreachable, no sensitivity).
    """
    if not data:
        return 0.0
    window = min(window, len(data))
    return sum(data[-window:]) / window


def generate_compliance_report(start_date: str, end_date: str) -> list:
    """
    Generates a PCI-DSS compliance report for the given date range.
    INTERNAL — never called from an HTTP route, only from the compliance pipeline.
    Uses parameterized queries exclusively.
    NOT reachable from internet (pc_reachability_hops=-1).

    FALSE POSITIVE CANDIDATE:
      Scanners flag this as "SQL injection" because it queries the DB.
      The graph shows: (1) NOT is_entry_point, (2) completely unreachable from
      any entry point, (3) parameterized queries only.
      Triage should score INFO.
    """
    cur = _get_db().cursor()
    # SAFE: parameterized — %s placeholders for both date values
    cur.execute(
        "SELECT tx_id, amount, status, created_at FROM transactions "
        "WHERE created_at BETWEEN %s AND %s AND flagged_pci = TRUE",
        (start_date, end_date)
    )
    return cur.fetchall()
