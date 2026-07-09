"""
Data access layer.
execute_raw_order — has_raw_query=true   (TAINT SINK — unsafe raw SQL)
get_order_by_id_safe — parameterized     (SAFE — false positive target)
get_portfolio_data   — parameterized     (SAFE — internal, sanitized upstream)
"""
import os
import psycopg2
import boto3

_CONN = None
DYNAMO = boto3.client("dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1"))
ORDERS_TABLE = os.environ.get("ORDERS_TABLE", "meridian-orders-prod")
PORTFOLIO_TABLE = os.environ.get("PORTFOLIO_TABLE", "meridian-portfolio-prod")


def _get_conn():
    global _CONN
    if not _CONN:
        _CONN = psycopg2.connect(os.environ.get("PG_CONN", ""))
    return _CONN


def execute_raw_order(query: str) -> list:
    """
    TAINT SINK — has_raw_query=true.
    Executes a raw SQL query directly — NO parameterization.
    Called unsanitized from submit_order → E_taint_path.
    sensitivity_class: financial (accesses live order book data).

    BUG H PROBE: Mode 2 should report exactly 1 structural taint path
    pointing to this function. E_taint_path edge count in KG = 1.
    """
    cur = _get_conn().cursor()
    cur.execute(query)           # SQL injection vector — raw string
    return cur.fetchall()


def get_order_by_id_safe(order_id: str) -> dict | None:
    """
    SAFE — parameterized PreparedStatement equivalent via %s.
    Called from cancel_order and get_order_history (sanitized paths).
    pc_sanitization: sanitized (sanitize_order_id called upstream).

    FALSE POSITIVE TARGET (F-015 CWE-89): scanner flags cursor.execute
    without distinguishing parameterized from raw. System should score LOW.
    """
    cur = _get_conn().cursor()
    cur.execute(
        "SELECT id, symbol, qty, side, status FROM orders WHERE id = %s",
        (order_id,)
    )
    row = cur.fetchone()
    return dict(zip(["id", "symbol", "qty", "side", "status"], row)) if row else None


def get_portfolio_data(clean_account_id: str) -> list:
    """
    Reads portfolio positions from DynamoDB using parameterized SDK call.
    Called ONLY from compute_portfolio_risk (which is itself called from
    cancel_order — a sanitized path).
    pc_sanitization: sanitized.
    E_data_flow_read: this function → meridian-portfolio-prod DynamoDB.
    """
    response = DYNAMO.query(
        TableName=PORTFOLIO_TABLE,
        KeyConditionExpression="account_id = :aid",
        ExpressionAttributeValues={":aid": {"S": clean_account_id}},
    )
    return response.get("Items", [])


def write_order_audit(order_id: str, action: str, user_id: str) -> None:
    """
    Writes an immutable audit record to S3.
    E_data_flow_write: this function → meridian-audit-logs S3 bucket.
    """
    import boto3
    s3 = boto3.client("s3")
    bucket = os.environ.get("AUDIT_BUCKET", "meridian-audit-logs-prod")
    key = f"orders/{order_id}/{action}.json"
    s3.put_object(
        Bucket=bucket, Key=key,
        Body=f'{{"order_id":"{order_id}","action":"{action}","user":"{user_id}"}}'.encode()
    )
