"""Deletion and failure visibility.

Both exist because of things that are invisible until they matter: a customer
asking to be forgotten, and a parsing bug that the webhook deliberately hides
by answering 200 so Meta does not retry-storm.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app import auth, config, main
from app.store import Store

WA = "971544120983"


def delivery(wa_id: str, mid: str) -> dict:
    return {"object": "whatsapp_business_account", "entry": [{"id": "W", "changes": [
        {"field": "messages", "value": {
            "contacts": [{"wa_id": wa_id, "profile": {"name": "Dana"}}],
            "messages": [{"from": wa_id, "id": mid, "timestamp": str(int(time.time())),
                          "type": "text", "text": {"body": "quote please"}}]}}]}]}


@pytest.fixture
def client(tmp_path, monkeypatch):
    store = Store(str(tmp_path / "t.db"))
    monkeypatch.setattr(main, "store", store)
    monkeypatch.setattr(config, "ADMIN_PASSWORD", "owner")
    monkeypatch.setattr(config, "PHONE_NUMBER_ID", "")
    monkeypatch.setattr(auth, "_failures", {})
    with TestClient(main.app, follow_redirects=False) as c:
        c.post("/login", data={"number": "", "password": "owner"})
        yield c
    store.close()


# ---- deletion ----

def test_deleting_a_customer_removes_everything_about_them(client):
    main.service.ingest(main.store, delivery(WA, "wamid.1"))
    main.service.ingest(main.store, delivery("923000000000", "wamid.2"))

    r = client.request("DELETE", f"/api/conversations/{WA}")
    assert r.status_code == 200 and r.json()["deleted"]["messages"] == 1

    assert main.store.get_conversation(WA) is None
    assert main.store.messages_for(WA) == []
    assert main.store.contact_name(WA) is None
    assert main.store.get_conversation("923000000000") is not None, "only the one asked for"


def test_deleting_an_unknown_customer_is_a_404_not_a_silent_success(client):
    assert client.request("DELETE", "/api/conversations/999").status_code == 404


def test_deletion_needs_a_login(client):
    main.service.ingest(main.store, delivery(WA, "wamid.1"))
    client.cookies.clear()
    assert client.request("DELETE", f"/api/conversations/{WA}").status_code == 401
    assert main.store.get_conversation(WA) is not None


def test_erase_all_clears_customers_but_not_the_login(client):
    main.service.ingest(main.store, delivery(WA, "wamid.1"))
    main.store.create_account("971500000000", auth.hash_password("keep-me"))

    counts = main.store.erase_all()

    assert counts["messages"] == 1
    assert main.store.all_conversations() == []
    assert main.store.account() is not None, "a wiped client must still be able to log in"


# ---- failure visibility ----

def test_a_broken_payload_is_recorded_not_swallowed(client, monkeypatch):
    """The 200 is what stops Meta retrying. The record is what stops it being
    invisible."""
    def boom(*_args, **_kwargs):
        raise ValueError("unexpected shape")

    monkeypatch.setattr(main.service, "ingest", boom)
    body = b'{"entry": []}'      # sign the exact bytes; re-serialising breaks the hmac
    r = client.post("/webhook", content=body,
                    headers={"Content-Type": "application/json",
                             "X-Hub-Signature-256": _sig(body)})

    assert r.status_code == 200, "a non-200 makes Meta retry the whole batch"
    errors = main.store.errors_since(datetime.now(timezone.utc) - timedelta(hours=1))
    assert len(errors) == 1 and errors[0]["kind"] == "ValueError"


def test_health_reports_counts_without_leaking_anything(client):
    main.service.ingest(main.store, delivery(WA, "wamid.1"))
    body = client.get("/api/health").json()

    assert body["ok"] is True and body["messages"] == 1
    assert body["errors_recent"] == 0 and body["last_message_at"]
    leaked = str(body)
    assert WA not in leaked and "Dana" not in leaked and "quote please" not in leaked


def test_health_stays_open_without_a_login(client):
    client.cookies.clear()
    assert client.get("/api/health").status_code == 200


def test_old_errors_fall_out_of_the_window(client):
    main.store.record_error("ValueError", "ancient")
    main.store.conn.execute(
        "UPDATE ingest_errors SET at = ?",
        ((datetime.now(timezone.utc) - timedelta(days=9)).isoformat(),))
    main.store.conn.commit()
    assert client.get("/api/health").json()["errors_recent"] == 0


def _sig(body: bytes) -> str:
    import hashlib
    import hmac
    return "sha256=" + hmac.new(config.APP_SECRET.encode(), body, hashlib.sha256).hexdigest()


def test_dashboard_javascript_parses():
    """A `\n` typed as a real newline breaks the JS literal and the whole
    dashboard silently stops loading data. Python tests cannot see that, so the
    build's own syntax check runs here too."""
    import shutil

    if not shutil.which("node"):
        pytest.skip("node not available")

    from tools import build_dashboard

    build_dashboard._check_script()   # raises SystemExit if the JS is broken
