"""
Meridian Order Execution API — Flask HTTP layer.

SECURITY PROBES:
  submit_order        — CRITICAL: no auth, taint path to execute_raw_order
  get_order_history   — BUG D: has inline auth check (declared_restrictive after fix)
  cancel_order        — BUG D: has inline auth check, calls sanitizer
  health_check        — BUG G: no auth, no data, returns {"status":"ok"} only
  process_batch_settlement — UNREACHABLE: CronJob only, FP target
  compute_portfolio_risk   — INTERNAL: sanitized upstream, FP target
"""
from flask import Flask, request, jsonify
from models import execute_raw_order, get_order_by_id_safe, get_portfolio_data, write_order_audit
from utils import sanitize_order_id, validate_token

app = Flask(__name__)


# ── CRITICAL FINDING TARGET ───────────────────────────────────────────────────

@app.route("/api/v1/orders", methods=["POST"])
def submit_order():
    """
    POST /api/v1/orders
    is_entry_point=true
    taint_class=user_input
    firewall_posture=declared_permissive (NO auth check)

    VULNERABILITY: request.json["raw_filter"] goes directly to execute_raw_order
    with NO sanitizer call on this path.
    → E_taint_path: submit_order → execute_raw_order

    FINDING F-001 (CWE-89 SQL Injection): expected CRITICAL.
    D1=1.0 (entry), D6=1.0 (internet-facing, permissive),
    D4=0.8 (financial sensitivity + taint path), D5=1.0 (no mitigations).
    """
    data = request.json or {}
    symbol     = data.get("symbol", "")
    quantity   = data.get("quantity", 0)
    raw_filter = data.get("raw_filter", "")   # taint source: user-controlled

    # NO sanitizer — deliberate vulnerability
    results = execute_raw_order(raw_filter)    # taint SINK: has_raw_query=true
    write_order_audit("new", "submit", "anon")
    return jsonify({"order": results, "symbol": symbol, "qty": quantity})


# ── BUG D PROBE — has inline auth check ──────────────────────────────────────

@app.route("/api/v1/orders/history", methods=["GET"])
def get_order_history():
    """
    GET /api/v1/orders/history?account_id=<id>
    is_entry_point=true
    firewall_posture=declared_permissive (WRONG — should be declared_restrictive)

    BUG D: This function has an explicit in-code auth guard:
      if not request.headers.get("Authorization"): return ..., 401
    After Bug D fix, posture engine should detect this and set
    firewall_posture=declared_restrictive, reducing D6.

    FINDING F-013 (CWE-639 IDOR): scanner flags as IDOR. Currently scores
    incorrectly HIGH (permissive). After Bug D fix: scores LOW (restricted).
    """
    if not request.headers.get("Authorization"):          # in-code auth check
        return jsonify({"error": "unauthorized"}), 401

    raw_account = request.args.get("account_id", "")
    clean_id    = sanitize_order_id(raw_account)          # E_sanitize
    orders      = get_order_by_id_safe(clean_id)
    return jsonify({"orders": orders})


@app.route("/api/v1/orders/<order_id>/cancel", methods=["POST"])
def cancel_order(order_id):
    """
    POST /api/v1/orders/<order_id>/cancel
    is_entry_point=true
    BUG D: Has in-code auth check — should be declared_restrictive.

    SANITIZED PATH: sanitize_order_id called before get_order_by_id_safe.
    Downstream functions (compute_portfolio_risk) inherit pc_sanitization=sanitized.

    FINDING F-008 (CWE-89 FP): tool flags this as SQL injection.
    System should recognise sanitized path → score LOW.
    """
    if not request.headers.get("Authorization"):          # in-code auth check
        return jsonify({"error": "unauthorized"}), 401

    clean_id = sanitize_order_id(order_id)                # E_sanitize
    order    = get_order_by_id_safe(clean_id)
    if not order:
        return jsonify({"error": "order not found"}), 404

    risk = compute_portfolio_risk(clean_id)
    write_order_audit(clean_id, "cancel", "system")
    return jsonify({"cancelled": clean_id, "risk": risk})


# ── BUG G PROBE — health check, no data, no auth ─────────────────────────────

@app.route("/api/v1/health", methods=["GET"])
def health_check():
    """
    GET /api/v1/health
    is_entry_point=true
    firewall_posture=declared_permissive (public endpoint — intentional)
    sensitivity_class: NONE — returns ONLY {"status": "ok"}
    NO DB calls, NO auth, NO data access.

    BUG G: Must NOT be classified sensitivity_class=pii.
    FINDING F-010 (CWE-200 FP): scanner flags all public endpoints.
    System should score INFO (no sensitive data, no taint).
    """
    return jsonify({"status": "ok", "service": "order-execution-api", "version": "3.0.0"})


# ── INTERNAL / UNREACHABLE — FALSE POSITIVE TARGETS ──────────────────────────

def compute_portfolio_risk(clean_order_id: str) -> float:
    """
    Computes portfolio risk for a given order.
    INTERNAL — called ONLY from cancel_order (sanitized path).
    NOT is_entry_point. pc_sanitization=sanitized.

    FINDING F-011 (CWE-89 FP): scanner flags because it accesses DB.
    System should score INFO (1 hop from entry, sanitized path, D5=0.5).
    """
    positions = get_portfolio_data(clean_order_id)
    return sum(
        float(p.get("value", {}).get("N", "0")) for p in positions
    )


def process_batch_settlement() -> dict:
    """
    Runs end-of-day settlement batch.
    NOT an HTTP route — called ONLY from __main__ / K8s CronJob.
    pc_reachability_hops=-1 (completely unreachable from internet).

    FINDING F-012 (CWE-200 FP): scanner flags sensitive data access.
    System should score INFO (unreachable, D1=0.1, D6=0.1).
    """
    from datetime import date
    today = date.today().isoformat()
    results = execute_raw_order(
        f"SELECT * FROM settlements WHERE date = '{today}' AND status = 'pending'"
    )
    return {"settled": len(results), "date": today}


if __name__ == "__main__":
    process_batch_settlement()
    app.run(host="0.0.0.0", port=8080)
