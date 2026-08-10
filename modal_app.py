"""Deploy QuoteRadar to Modal.

    modal deploy modal_app.py

Design notes that matter for cost and correctness:

* **Scale to zero.** No `min_containers`, so idle costs nothing. A webhook is
  about a second of CPU; keeping a container warm would run ~$50/month and buy
  us nothing, because Meta retries deliveries and only the one-time verification
  handshake is latency-sensitive.

* **One container, always.** `max_containers=1` — SQLite on a shared Volume
  cannot take concurrent writers from separate containers. Fine at this scale:
  a fit-out firm's whole message volume is trivial for one container.

* **Volume for the database.** Modal's container filesystem is ephemeral. The
  Volume is the only place data survives a restart, and every write is committed
  before the request returns so a scale-down cannot lose a message.
"""
from __future__ import annotations

import modal

app = modal.App("quoteradar")

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("fastapi[standard]==0.133.1", "uvicorn==0.34.0")
    .add_local_dir("app", remote_path="/root/app")
)

# Survives restarts and redeploys. Without this the database is wiped every
# time the container recycles.
volume = modal.Volume.from_name("quoteradar-data", create_if_missing=True)

# Separate Volume, because a backup living inside the volume it protects is not
# a backup. Cheap: the database is kilobytes per client.
backups = modal.Volume.from_name("quoteradar-backups", create_if_missing=True)

# Secrets live in Modal, never in the image or the repo:
#   modal secret create quoteradar-secrets \
#       WA_APP_SECRET=... WA_VERIFY_TOKEN=... QR_ADMIN_PASSWORD=... \
#       QR_SESSION_SECRET=... QR_CURRENCY=AED QR_BUSINESS_NAME="..."
secrets = modal.Secret.from_name("quoteradar-secrets")


@app.function(
    image=image,
    volumes={"/data": volume},
    secrets=[secrets],
    max_containers=1,          # SQLite: exactly one writer
    scaledown_window=300,      # linger 5 min so bursts reuse a warm container
    timeout=60,
)
@modal.concurrent(max_inputs=20)
@modal.asgi_app()
def web():
    import os

    os.environ.setdefault("QR_DB_PATH", "/data/quoteradar.db")
    os.environ.setdefault("QR_SECURE_COOKIES", "true")   # Modal always serves HTTPS

    # Take the newest committed state before opening SQLite. A container that
    # starts on a stale view and then commits would overwrite writes another
    # container made after it mounted — silent, total data loss.
    volume.reload()

    from app.main import app as fastapi_app
    from starlette.middleware.base import BaseHTTPMiddleware

    class CommitVolume(BaseHTTPMiddleware):
        """Persist writes before responding.

        Modal Volumes only durably store what has been committed. Without this a
        scale-down between a webhook and the next request could lose messages
        that SQLite had already written to the container's view of the disk.
        """

        async def dispatch(self, request, call_next):
            response = await call_next(request)
            if request.method in ("POST", "PUT", "DELETE"):
                try:
                    volume.commit()
                except Exception:  # noqa: BLE001 - never fail a webhook over this
                    pass
            return response

    fastapi_app.add_middleware(CommitVolume)
    return fastapi_app


@app.function(image=image, volumes={"/data": volume}, secrets=[secrets],
              max_containers=1, timeout=60)
def setup_link(reset: bool = False):
    """Mint the one-time link a new client uses to choose their own password.

        modal run modal_app.py::setup_link
        modal run modal_app.py::setup_link --reset    # they forgot it

    Send the printed URL privately. It works once, then only /login works. The
    code is stored hashed, so this output is the only time it exists in the
    clear - if it is lost, mint another.
    """
    import os

    os.environ.setdefault("QR_DB_PATH", "/data/quoteradar.db")
    volume.reload()

    from app import auth
    from app.store import Store

    store = Store(os.environ["QR_DB_PATH"])
    existing = store.account()

    if existing and not reset:
        print(f"An account already exists for +{existing['wa_number']} "
              f"(created {existing['created_at']}).")
        print("Re-run with --reset to let them set a new password.")
        return

    if existing:
        # Only the login is cleared. Conversations, amounts and outcomes stay.
        store.conn.execute("DELETE FROM account")
        store.conn.commit()
        print(f"Cleared the login for +{existing['wa_number']}. Their data is untouched.")

    code = auth.new_setup_code()
    store.add_setup_code(auth.hash_setup_code(code))
    store.close()
    volume.commit()

    print("\nSend this link, once, privately:\n")
    print(f"  https://hamza-aiemployee--quoteradar-web.modal.run/setup?code={code}\n")


@app.function(
    image=image,
    volumes={"/data": volume, "/backups": backups},
    max_containers=1,
    timeout=300,
    schedule=modal.Cron("17 2 * * *"),   # 02:17 UTC, away from any traffic
)
def backup(keep: int = 30):
    """Nightly snapshot of the database to a second Volume.

    Uses SQLite's own backup API rather than copying the file: a plain copy taken
    mid-write produces a corrupt database, and the whole point of a backup is
    that it opens.

    Restore:  modal volume get quoteradar-backups <name>  then put it back as
              /data/quoteradar.db with `modal volume put quoteradar-data`.
    """
    import os
    import sqlite3
    from datetime import datetime, timezone

    # Without this the backup container keeps the volume's state from when it
    # mounted and silently snapshots an empty or stale database.
    volume.reload()

    src_path = "/data/quoteradar.db"
    if not os.path.exists(src_path):
        print("no database yet, nothing to back up")
        return

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    dest_path = f"/backups/quoteradar-{stamp}.db"

    src = sqlite3.connect(f"file:{src_path}?mode=ro", uri=True)
    dest = sqlite3.connect(dest_path)
    with dest:
        src.backup(dest)
    dest.close()
    src.close()

    # Prove it opens before trusting it, then prune. An unverified backup is a
    # guess.
    check = sqlite3.connect(dest_path)
    rows = check.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    check.close()

    snapshots = sorted(f for f in os.listdir("/backups") if f.endswith(".db"))
    for stale in snapshots[:-keep]:
        os.remove(f"/backups/{stale}")

    backups.commit()
    print(f"backed up {rows} messages -> {dest_path} ({len(snapshots[-keep:])} kept)")
