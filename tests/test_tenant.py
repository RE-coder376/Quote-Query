"""One instance, one number.

v1 gives each client their own instance, so there is no tenant column anywhere
below ingest. That makes this filter the entire boundary: if a delivery for
another number gets past it, one client's conversations land in another
client's dashboard.
"""
from __future__ import annotations

import time

import pytest

from app import config, service
from app.store import Store
from app.webhook import for_phone_number

OURS = "106540352242922"
THEIRS = "999999999999999"


def delivery(pnid: str, wa_id: str, mid: str) -> dict:
    return {"object": "whatsapp_business_account", "entry": [{"id": "W", "changes": [
        {"field": "messages", "value": {
            "messaging_product": "whatsapp",
            "metadata": {"display_phone_number": "97140000000", "phone_number_id": pnid},
            "messages": [{"from": wa_id, "id": mid, "timestamp": str(int(time.time())),
                          "type": "text", "text": {"body": "hello"}}]}}]}]}


@pytest.fixture
def store(tmp_path):
    s = Store(str(tmp_path / "t.db"))
    yield s
    s.close()


@pytest.fixture
def scoped(monkeypatch):
    monkeypatch.setattr(config, "PHONE_NUMBER_ID", OURS)


def test_another_clients_number_is_dropped(store, scoped):
    assert service.ingest(store, delivery(THEIRS, "971500000001", "wamid.x")) == 0
    assert store.all_conversations() == []


def test_our_own_number_still_ingests(store, scoped):
    assert service.ingest(store, delivery(OURS, "971500000002", "wamid.y")) == 1


def test_mixed_delivery_keeps_only_ours(store, scoped):
    mixed = delivery(OURS, "971500000003", "wamid.a")
    mixed["entry"][0]["changes"] += delivery(THEIRS, "971500000004", "wamid.b")["entry"][0]["changes"]
    assert service.ingest(store, mixed) == 1
    assert [c.wa_id for c in store.all_conversations()] == ["971500000003"]


def test_metadata_free_changes_survive():
    """`statuses` deliveries can arrive without metadata; they are enrichment
    keyed by message id, so dropping them would lose read ticks for no gain."""
    p = {"entry": [{"changes": [{"field": "messages", "value": {"statuses": [
        {"id": "wamid.z", "status": "read", "timestamp": "1739230955"}]}}]}]}
    assert for_phone_number(p, OURS) == p


def test_unset_filter_accepts_everything(store, monkeypatch):
    """Local simulation has no real phone_number_id and must keep working."""
    monkeypatch.setattr(config, "PHONE_NUMBER_ID", "")
    assert service.ingest(store, delivery(THEIRS, "971500000005", "wamid.c")) == 1
