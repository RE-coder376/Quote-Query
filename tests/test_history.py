"""Coexistence history backfill.

The highest-value moment the product has: a client connects and immediately
sees their own stale quotes. These tests pin the two things that can silently
ruin it - wrong direction (every thread would show the wrong party as silent)
and double-counting on Meta's retries.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.models import ConvState, Direction
from app.service import ingest, sync_status
from app.store import Store
from app.webhook import parse_history, parse_state_sync_contacts

BUSINESS = "97140000000"
CUSTOMER = "971544120983"


def ts(days_ago: float) -> str:
    return str(int((datetime.now(timezone.utc) - timedelta(days=days_ago)).timestamp()))


def msg(sender: str, mid: str, days_ago: float, text: str, status: str = "DELIVERED") -> dict:
    return {"from": sender, "to": CUSTOMER if sender == BUSINESS else BUSINESS,
            "id": mid, "timestamp": ts(days_ago), "type": "text",
            "text": {"body": text}, "history_context": {"status": status}}


def payload(messages: list[dict], phase: int = 1, chunk_order: int = 1,
            progress: int = 100, wa_id: str = CUSTOMER) -> dict:
    return {"object": "whatsapp_business_account", "entry": [{"id": "WABA", "changes": [
        {"field": "history", "value": {
            "messaging_product": "whatsapp",
            "metadata": {"display_phone_number": BUSINESS, "phone_number_id": "PNID"},
            "history": [{
                "metadata": {"phase": phase, "chunk_order": chunk_order,
                             "progress": progress},
                "threads": [{"id": wa_id, "messages": messages}],
            }]}}]}]}


@pytest.fixture
def store(tmp_path, monkeypatch):
    """These payloads declare phone_number_id "PNID", so the instance has to be
    configured for that number - otherwise for_phone_number() correctly discards
    them as belonging to a different client."""
    from app import config
    monkeypatch.setattr(config, "PHONE_NUMBER_ID", "PNID")
    s = Store(str(tmp_path / "t.db"))
    yield s
    s.close()


# ---- parsing ----

def test_direction_comes_from_the_business_number():
    """There is no from_me flag; sender vs display_phone_number is the only signal."""
    out = list(parse_history(payload([
        msg(CUSTOMER, "wamid.1", 40, "Quote for the wardrobes?"),
        msg(BUSINESS, "wamid.2", 39, "AED 46,500."),
    ])))
    assert [m.direction for m in out] == [Direction.INBOUND, Direction.OUTBOUND]
    assert all(m.wa_id == CUSTOMER for m in out), "thread id is always the customer"


def test_business_number_with_plus_prefix_still_matches():
    p = payload([msg(BUSINESS, "wamid.1", 5, "Quote attached")])
    p["entry"][0]["changes"][0]["value"]["metadata"]["display_phone_number"] = f"+{BUSINESS}"
    assert list(parse_history(p))[0].direction is Direction.OUTBOUND


def test_read_status_marks_seen_but_only_outbound():
    out = list(parse_history(payload([
        msg(BUSINESS, "wamid.1", 5, "Quote", status="READ"),
        msg(BUSINESS, "wamid.2", 4, "Following up", status="DELIVERED"),
        msg(CUSTOMER, "wamid.3", 3, "Got it", status="READ"),
    ])))
    assert [m.read_at is not None for m in out] == [True, False, False]


def test_malformed_nodes_are_skipped_not_raised():
    p = payload([{"id": "wamid.ok", "from": CUSTOMER, "timestamp": ts(1), "type": "text",
                  "text": {"body": "hi"}}, {"from": CUSTOMER}, {}])
    assert [m.wa_message_id for m in parse_history(p)] == ["wamid.ok"]


def test_state_sync_contacts_use_the_business_own_names():
    p = {"entry": [{"changes": [{"field": "smb_app_state_sync", "value": {"state_sync": [
        {"type": "contact", "action": "add",
         "contact": {"full_name": "Dana - Al Quoz", "first_name": "Dana",
                     "phone_number": f"+{CUSTOMER}"}},
        {"type": "contact", "action": "remove",
         "contact": {"full_name": "Gone", "phone_number": "971500000000"}},
    ]}}]}]}
    assert list(parse_state_sync_contacts(p)) == [(CUSTOMER, "Dana - Al Quoz")]


# ---- ingestion ----

def test_backfill_produces_a_stale_conversation(store):
    """The whole point: a five-month-old unanswered quote lands already overdue."""
    ingest(store, payload([
        msg(CUSTOMER, "wamid.1", 154, "Can you quote the wardrobes?"),
        msg(BUSINESS, "wamid.2", 153, "AED 46,500."),
    ], phase=2))
    conv = store.get_conversation(CUSTOMER)
    assert conv.state is ConvState.AWAITING_CUSTOMER
    assert (datetime.now(timezone.utc) - conv.last_message_at).days >= 150


def test_history_is_idempotent_across_retries(store):
    p = payload([msg(CUSTOMER, "wamid.1", 20, "Quote please")])
    assert ingest(store, p) == 1
    assert ingest(store, p) == 0, "Meta retries the whole batch on any non-200"


def test_chunks_arriving_out_of_order_give_the_same_state(store):
    """Chunk order is not guaranteed. The newer message must win regardless."""
    newer = payload([msg(CUSTOMER, "wamid.2", 10, "Any update?")], phase=1, chunk_order=2)
    older = payload([msg(BUSINESS, "wamid.1", 30, "AED 12,000")], phase=1, chunk_order=1)
    ingest(store, newer)
    ingest(store, older)
    assert store.get_conversation(CUSTOMER).state is ConvState.AWAITING_REPLY


def test_history_overlapping_live_traffic_is_not_double_counted(store):
    """Phase 0 covers the last day, which the live webhook already delivered."""
    live = {"entry": [{"changes": [{"field": "messages", "value": {
        "messages": [{"from": CUSTOMER, "id": "wamid.dup", "timestamp": ts(0.5),
                      "type": "text", "text": {"body": "hello"}}]}}]}]}
    assert ingest(store, live) == 1
    assert ingest(store, payload([msg(CUSTOMER, "wamid.dup", 0.5, "hello")], phase=0)) == 0


# ---- progress ----

def test_sync_status_reports_import_in_flight(store):
    assert sync_status(store) == {"active": False, "started": False,
                                  "imported": 0, "phases": []}

    ingest(store, payload([msg(CUSTOMER, "wamid.1", 100, "hi")], phase=2, progress=40))
    mid = sync_status(store)
    assert mid["started"] and mid["active"] and mid["imported"] == 1

    ingest(store, payload([msg(CUSTOMER, "wamid.2", 99, "hi again")],
                          phase=2, chunk_order=2, progress=100))
    done = sync_status(store)
    assert not done["active"] and done["imported"] == 2


def test_progress_never_goes_backwards(store):
    """A late chunk from early in a phase must not reopen a finished import."""
    ingest(store, payload([msg(CUSTOMER, "wamid.1", 50, "a")], progress=100))
    ingest(store, payload([msg(CUSTOMER, "wamid.2", 49, "b")], chunk_order=2, progress=20))
    assert not sync_status(store)["active"]


def test_history_for_another_number_is_discarded(store, monkeypatch):
    """One instance serves one client. A backfill for someone else's number must
    never be folded in - there is no per-tenant boundary below ingest to catch it."""
    from app import config
    monkeypatch.setattr(config, "PHONE_NUMBER_ID", "SOMEONE-ELSE")
    assert ingest(store, payload([msg(CUSTOMER, "wamid.x", 5, "hello")])) == 0
    assert store.get_conversation(CUSTOMER) is None
