"""
Input validation and sanitization for the trading platform.
Functions here produce E_sanitize edges when called from tainted paths.
"""
import re

_TX_ID_RE = re.compile(r'^TX-[A-Z0-9]{12}$')
_SAFE_PARAM = re.compile(r'^[A-Za-z0-9_\-\.]{1,128}$')


def sanitize_transaction_id(raw: str) -> str:
    """
    Sanitizer — called from get_fraud_score before any DB access.
    Produces E_sanitize: get_fraud_score → sanitize_transaction_id.
    """
    if not raw or not isinstance(raw, str):
        raise ValueError("transaction_id must be non-empty string")
    clean = raw.strip().upper()
    if not _TX_ID_RE.match(clean):
        raise ValueError(f"Invalid transaction ID format: {raw!r}")
    return clean


def sanitize_query_param(raw: str) -> str:
    """
    Sanitizer for generic query parameters.
    Produces E_sanitize edges when called before DB operations.
    """
    if not raw:
        return ""
    clean = raw.strip()
    clean = re.sub(r"['\";\\<>]", "", clean)
    if not _SAFE_PARAM.match(clean):
        raise ValueError(f"Query param contains unsafe characters: {raw!r}")
    return clean


def validate_transaction_id(raw: str) -> bool:
    """Validates (does not clean) a transaction ID. Returns True/False."""
    return bool(_TX_ID_RE.match((raw or "").strip().upper()))
