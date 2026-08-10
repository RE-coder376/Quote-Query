"""End-to-end: signed webhook in -> stored -> state engine -> read API out."""
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app import config


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Fresh database per test, signed in — the data routes are behind auth."""
    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setattr(config, "ADMIN_PASSWORD", "test-pw")
    monkeypatch.setattr(config, "SESSION_SECRET", "test-secret")
    import importlib
    from app import auth, main
    importlib.reload(main)
    auth._failures.clear()
    c = TestClient(main.app)
    c.post("/login", data={"password": "test-pw"})
    return c


NOW = datetime.now(timezone.utc)


def ts(hours_ago):
    return str(int((NOW - timedelta(hours=hours_ago)).timestamp()))


def sign(body: bytes) -> str:
    return "sha256=" + hmac.new(config.APP_SECRET.encode(), body, hashlib.sha256).hexdigest()


def send(client, changes):
    body = json.dumps({"object": "whatsapp_business_account",
                       "entry": [{"id": "W", "changes": changes}]}).encode()
    return client.post("/webhook", content=body,
                       headers={"X-Hub-Signature-256": sign(body),
                                "Content-Type": "application/json"})


def inbound(wa_id, mid, hours_ago, text="hello"):
    return {"field": "messages", "value": {"messages": [
        {"from": wa_id, "id": mid, "timestamp": ts(hours_ago),
         "type": "text", "text": {"body": text}}]}}


def echo(wa_id, mid, hours_ago, text="quoted AED 44,500"):
    return {"field": "smb_message_echoes", "value": {"message_echoes": [
        {"to": wa_id, "id": mid, "timestamp": ts(hours_ago),
         "type": "text", "text": {"body": text}}]}}


def test_unsigned_webhook_is_rejected(client):
    body = json.dumps({"entry": []}).encode()
    assert client.post("/webhook", content=body).status_code == 403
    assert client.post("/webhook", content=body,
                       headers={"X-Hub-Signature-256": "sha256=bad"}).status_code == 403


def test_inbound_message_creates_a_conversation_awaiting_our_reply(client):
    assert send(client, [inbound("971500000001", "m1", 2, "Can you quote this?")]).json()["applied"] == 1
    data = client.get("/api/conversations").json()
    conv = data["conversations"][0]
    assert conv["state"] == "awaiting_reply"
    assert conv["status"] == "You need to reply"
    assert conv["wait_text"].startswith("no reply from you for")


def test_our_echo_flips_it_to_awaiting_customer(client):
    send(client, [inbound("971500000002", "m1", 5)])
    send(client, [echo("971500000002", "m2", 4)])
    conv = client.get("/api/conversations").json()["conversations"][0]
    assert conv["state"] == "awaiting_customer"
    assert conv["wait_text"].startswith("no customer reply for")


def test_replayed_delivery_is_idempotent(client):
    """Meta retries. A retry must not double-count or re-fold state."""
    changes = [inbound("971500000003", "m1", 3), echo("971500000003", "m2", 2)]
    assert send(client, changes).json()["applied"] == 2
    assert send(client, changes).json()["applied"] == 0
    assert len(client.get("/api/conversations").json()["conversations"]) == 1


def test_overdue_flag_and_denominator_math(client):
    # two overdue with amounts, one overdue without
    for i, hours in enumerate([100, 200, 300]):
        send(client, [inbound(f"9715000001{i}", f"a{i}", hours + 1),
                      echo(f"9715000001{i}", f"b{i}", hours)])
    client.post("/api/conversations/97150000010/amount", json={"amount": 40000})
    client.post("/api/conversations/97150000011/amount", json={"amount": 60000})

    s = client.get("/api/conversations").json()["summary"]
    assert s["at_risk_total"] == 100000
    assert s["at_risk_counted"] == 2
    assert s["at_risk_overdue"] == 3
    assert s["at_risk_untracked"] == 1     # the total must always show its denominator


def test_close_then_customer_message_reopens_automatically(client):
    send(client, [inbound("971500000020", "m1", 50), echo("971500000020", "m2", 49)])
    client.post("/api/conversations/971500000020/outcome", json={"outcome": "won"})
    assert client.get("/api/conversations/971500000020").json()["status"] == "Won"

    send(client, [inbound("971500000020", "m3", 0.1, "One more thing")])
    conv = client.get("/api/conversations/971500000020").json()
    assert conv["state"] == "awaiting_reply"
    assert conv["outcome"] is None


def test_won_reuses_quoted_amount_and_has_no_paid_field(client):
    send(client, [echo("971500000030", "m1", 300)])
    client.post("/api/conversations/971500000030/amount", json={"amount": 61000})
    client.post("/api/conversations/971500000030/outcome", json={"outcome": "won"})
    s = client.get("/api/conversations").json()["summary"]
    assert s["won_total"] == 61000 and s["won_counted"] == 1
    assert "paid_amount" not in json.dumps(client.get("/api/conversations/971500000030").json())


def test_read_receipt_is_display_only_and_absence_shows_nothing(client):
    send(client, [inbound("971500000040", "m1", 10), echo("971500000040", "m2", 9)])
    before = client.get("/api/conversations/971500000040").json()
    assert all(m["seen"] is False for m in before["messages"])

    body = json.dumps({"entry": [{"changes": [{"value": {"statuses": [
        {"id": "m2", "status": "read", "timestamp": ts(8)}]}}]}]}).encode()
    client.post("/webhook", content=body, headers={"X-Hub-Signature-256": sign(body)})

    after = client.get("/api/conversations/971500000040").json()
    assert any(m["seen"] for m in after["messages"])
    assert after["state"] == before["state"]   # a receipt must never move a state


def test_there_is_no_send_endpoint(client):
    """Read-only is a product guarantee, not an omission."""
    paths = client.get("/api/openapi.json").json()["paths"]
    assert not any("send" in p or "reply" in p for p in paths)


def test_urgent_and_ours_sorts_first(client):
    send(client, [echo("971500000050", "x1", 400)])                      # very stale, theirs
    send(client, [inbound("971500000051", "y1", 30)])                    # overdue, ours
    order = [c["wa_id"] for c in client.get("/api/conversations").json()["conversations"]]
    assert order[0] == "971500000051"


def test_customer_profile_name_is_used_and_kept_updated(client):
    """Meta sends the sender's WhatsApp profile name with inbound messages -
    it is the only name we ever get, so use it instead of showing a raw number."""
    body = json.dumps({"entry": [{"changes": [{"field": "messages", "value": {
        "contacts": [{"wa_id": "971500000060", "profile": {"name": "Halo Interiors"}}],
        "messages": [{"from": "971500000060", "id": "n1", "timestamp": ts(3),
                      "type": "text", "text": {"body": "Quote please"}}]}}]}]}).encode()
    client.post("/webhook", content=body, headers={"X-Hub-Signature-256": sign(body)})
    assert client.get("/api/conversations/971500000060").json()["name"] == "Halo Interiors"


def test_missing_profile_name_falls_back_to_the_number(client):
    send(client, [inbound("971500000061", "n2", 1)])
    assert client.get("/api/conversations/971500000061").json()["name"] == "+971500000061"
