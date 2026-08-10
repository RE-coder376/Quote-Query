"""Session auth for the dashboard.

The webhook endpoint is deliberately NOT behind this - Meta cannot log in. That
endpoint authenticates differently and just as strictly, by verifying Meta's
X-Hub-Signature-256 against the app secret.

Everything a human can read (conversations, message text, amounts) is behind a
login, because it is our clients' customers' private messages. Meta's Platform
Terms require protecting data obtained through the API, and an open dashboard
would breach that no matter how obscure the URL.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from typing import Optional

from . import config

SESSION_COOKIE = "qr_session"
SESSION_TTL = 60 * 60 * 12          # 12 hours

# Brute-force damping. Single-tenant, so an in-memory counter is enough; it
# resets on restart, which is acceptable for the threat it addresses.
_failures: dict[str, list[float]] = {}
_MAX_FAILURES = 8
_WINDOW = 15 * 60


def password_ok(supplied: str) -> bool:
    """Constant-time compare so response timing cannot leak the password."""
    expected = config.ADMIN_PASSWORD
    if not expected:
        return False
    return hmac.compare_digest(supplied.encode(), expected.encode())


def rate_limited(ip: str, now: Optional[float] = None) -> bool:
    now = now or time.time()
    hits = [t for t in _failures.get(ip, []) if now - t < _WINDOW]
    _failures[ip] = hits
    return len(hits) >= _MAX_FAILURES


def record_failure(ip: str, now: Optional[float] = None) -> None:
    _failures.setdefault(ip, []).append(now or time.time())


def clear_failures(ip: str) -> None:
    _failures.pop(ip, None)


def issue_session(now: Optional[float] = None) -> str:
    """expiry.nonce.signature — stateless, so restarts don't log everyone out
    (as long as QR_SESSION_SECRET is set) and there is no session store to leak."""
    expiry = int((now or time.time()) + SESSION_TTL)
    nonce = secrets.token_urlsafe(8)
    payload = f"{expiry}.{nonce}"
    sig = hmac.new(config.SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).digest()
    return f"{payload}.{base64.urlsafe_b64encode(sig).decode().rstrip('=')}"


def valid_session(token: Optional[str], now: Optional[float] = None) -> bool:
    if not token:
        return False
    parts = token.split(".")
    if len(parts) != 3:
        return False
    expiry, nonce, sig = parts

    payload = f"{expiry}.{nonce}"
    expected = hmac.new(config.SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).digest()
    expected_b64 = base64.urlsafe_b64encode(expected).decode().rstrip("=")
    if not hmac.compare_digest(expected_b64, sig):
        return False

    try:
        return int(expiry) > (now or time.time())
    except ValueError:
        return False
