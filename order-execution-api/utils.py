"""
Utility functions — sanitizers and validators.
sanitize_order_id and sanitize_symbol produce E_sanitize edges
when called before DB access on tainted paths.
"""
import re

_ORDER_RE = re.compile(r'^ORD-[A-Z0-9]{10}$')
_SYMBOL_RE = re.compile(r'^[A-Z]{1,5}$')


def sanitize_order_id(raw: str) -> str:
    """
    Sanitizer — produces E_sanitize on paths through here.
    Called from: get_order_history, cancel_order BEFORE any DB access.
    """
    if not raw or not isinstance(raw, str):
        raise ValueError("order_id must be a non-empty string")
    clean = raw.strip().upper()
    if not _ORDER_RE.match(clean):
        raise ValueError(f"Invalid order ID format: {raw!r}")
    return clean


def sanitize_symbol(raw: str) -> str:
    """
    Sanitizer for market ticker symbols.
    Produces E_sanitize on paths from GetFeedStatus.
    """
    clean = (raw or "").strip().upper()
    if not _SYMBOL_RE.match(clean):
        raise ValueError(f"Invalid symbol: {raw!r}")
    return clean


def validate_token(token: str) -> dict | None:
    """
    Validates a Bearer JWT token. Returns payload dict or None.
    Used by auth-protected routes to satisfy BUG D posture check.
    """
    if not token or len(token) < 20:
        return None
    # Simplified: real impl would verify signature
    return {"sub": "user-001", "role": "trader"}
