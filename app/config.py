"""Settings, read from the environment.

Nothing secret is ever committed. Copy .env.example to .env and fill it in.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _env(name: str, default: str = "") -> str:
    """Read from the process env, falling back to a .env file next to the repo."""
    if name in os.environ:
        return os.environ[name]
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and line.split("=", 1)[0] == name:
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return default


# Meta app secret — used to verify X-Hub-Signature-256 on every delivery.
APP_SECRET = _env("WA_APP_SECRET", "dev-secret")

# Token echoed back during Meta's webhook verification handshake.
VERIFY_TOKEN = _env("WA_VERIFY_TOKEN", "dev-verify-token")

DB_PATH = _env("QR_DB_PATH", str(ROOT / "quoteradar.db"))

STALE_HOURS = int(_env("QR_STALE_HOURS", "24"))

# Display only. The product never converts or does arithmetic across currencies.
CURRENCY = _env("QR_CURRENCY", "AED")

BUSINESS_NAME = _env("QR_BUSINESS_NAME", "Your business")

# Dashboard login. Everything a human can read is behind this — the data is our
# clients' customers' private messages.
ADMIN_PASSWORD = _env("QR_ADMIN_PASSWORD", "")

# Signs session cookies. If unset, a random one is generated per process, which
# works but logs everyone out on restart. Set it in .env for stable sessions.
SESSION_SECRET = _env("QR_SESSION_SECRET", "") or __import__("secrets").token_urlsafe(32)

# Set true when served over HTTPS so the session cookie carries the Secure flag.
SECURE_COOKIES = _env("QR_SECURE_COOKIES", "false").lower() in ("1", "true", "yes")
