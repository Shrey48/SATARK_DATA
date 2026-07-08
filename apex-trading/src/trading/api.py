"""
Apex Trading — HTTP API layer.
All routes here are internet-facing via K8s Ingress.

SECURITY PROBES:
  search_transactions — is_entry_point=true, firewall_posture=declared_permissive,
                        taint_class=user_input, NO sanitizer → E_taint_path (CRITICAL FP)
  get_fraud_score     — is_entry_point=true, firewall_posture=declared_restrictive,
                        calls sanitize_transaction_id → E_sanitize (clean path)
  upload_trading_report — is_entry_point=true, partial path validation (MEDIUM)
  health_check        — is_entry_point=true, firewall_posture=declared_permissive,
                        sensitivity_class=none (FALSE POSITIVE — INFO)
"""
from flask import Flask, request, jsonify
from src.trading.analytics import (
    execute_raw_query, analyze_transaction,
    compute_risk_score, generate_compliance_report,
)
from src.trading.validators import sanitize_transaction_id

app = Flask(__name__)


# ── CRITICAL FINDING TARGET ──────────────────────────────────────────────────

@app.route("/api/trading/search", methods=["GET"])
def search_transactions():
    """
    GET /api/trading/search?q=<user_query>
    is_entry_point=true
    taint_class=user_input
    firewall_posture=declared_permissive  (NO auth decorator — public endpoint)

    VULNERABILITY: user-supplied ?q= parameter passed directly to
    execute_raw_query() with NO sanitizer call on this path.
    → E_taint_path: search_transactions → execute_raw_query

    FINDING F-001: CWE-89 SQL Injection — should triage CRITICAL
      - D1: 1 hop from entry point (IS the entry point)
      - D4: financial sensitivity reached (execute_raw_query handles financial data)
      - D5: no mitigations (no E_sanitize on this path)
      - D6: internet-facing, permissive
    """
    raw_query = request.args.get("q", "")   # taint source: user-controlled
    # NO sanitizer call — deliberate vulnerability
    results = execute_raw_query(raw_query)   # taint sink: has_raw_query=true
    return jsonify({"results": results})


# ── SANITIZED PATH ───────────────────────────────────────────────────────────

@app.route("/api/trading/fraud/<tx_id>", methods=["GET"])
def get_fraud_score(tx_id):
    """
    GET /api/trading/fraud/<tx_id>
    is_entry_point=true
    firewall_posture=declared_restrictive  (requires JWT)
    taint_class=user_input

    SANITIZED PATH: calls sanitize_transaction_id before any DB access.
    → E_sanitize: get_fraud_score → sanitize_transaction_id

    FALSE POSITIVE CANDIDATE (F-009, CWE-89):
      Tool flags this as "SQL injection" because it accesses DB.
      Graph shows: sanitized path (E_sanitize exists), auth-protected.
      Should triage LOW.
    """
    if not request.headers.get("Authorization"):
        return jsonify({"error": "unauthorized"}), 401

    clean_id = sanitize_transaction_id(tx_id)          # SANITIZER → E_sanitize
    tx_data  = analyze_transaction(clean_id)
    score    = compute_risk_score(tx_data)
    return jsonify({"transaction_id": clean_id, "fraud_score": score})


# ── FALSE POSITIVE TARGET — INFO ─────────────────────────────────────────────

@app.route("/api/trading/health", methods=["GET"])
def health_check():
    """
    GET /api/trading/health
    is_entry_point=true
    firewall_posture=declared_permissive  (no auth — intentionally public)
    sensitivity_class: NONE  (only returns {"status":"ok"})

    FALSE POSITIVE CANDIDATE (F-010, CWE-200 Information Disclosure):
      Scanner flags any public endpoint with no auth.
      Graph shows: no sensitive data accessed, no taint paths, no cloud reads.
      Should triage INFO — this is a standard health check.
    """
    return jsonify({"status": "ok", "service": "apex-trading", "version": "4.2.1"})


# ── MEDIUM FINDING TARGET ────────────────────────────────────────────────────

@app.route("/api/trading/reports/upload", methods=["POST"])
def upload_trading_report():
    """
    POST /api/trading/reports/upload
    is_entry_point=true
    firewall_posture=declared_restrictive  (requires auth)
    taint_class=user_input

    PARTIAL VALIDATION: checks file extension but not full path traversal.
    FINDING F-006 (CWE-22 Path Traversal): should triage MEDIUM
      - Entry point reachable, but partial mitigation present.
      - sensitivity_class: internal (report files, not PII)
    """
    if not request.headers.get("Authorization"):
        return jsonify({"error": "unauthorized"}), 401

    file_path = request.json.get("path", "")
    # Partial validation — checks extension but not ../ traversal
    if not file_path.endswith((".csv", ".xlsx", ".parquet")):
        return jsonify({"error": "unsupported file type"}), 400
    # VULNERABILITY: no path.normpath or ../ check
    return jsonify({"uploaded": file_path, "status": "queued"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
