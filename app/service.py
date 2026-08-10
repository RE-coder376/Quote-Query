"""Ingestion and read models — the layer between webhooks and the UI."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from . import config
from .models import Contact, ConvState, Conversation, Outcome, utcnow
from .state import apply_message, close, is_overdue, reopen, state_for, waiting_for
from .store import Store
from .webhook import (for_phone_number, parse_contacts, parse_history_chunks,
                      parse_messages, parse_read_receipts,
                      parse_state_sync_contacts)


def ingest(store: Store, payload: dict) -> int:
    """Fold a webhook delivery into storage. Returns messages newly applied.

    Idempotent: Meta retries deliveries, and a retry must not re-fold a message
    that is already counted.
    """
    # Anything for another client's number is dropped before it can touch this
    # client's data.
    payload = for_phone_number(payload, config.PHONE_NUMBER_ID)
    applied = 0

    # Names first, so a conversation created below already has one.
    for wa_id, name in parse_contacts(payload):
        store.upsert_contact(Contact(wa_id=wa_id, display_name=name))

    # The Business app's own address book — what the business calls the customer.
    for wa_id, name in parse_state_sync_contacts(payload):
        store.upsert_contact(Contact(wa_id=wa_id, display_name=name))

    for msg in parse_messages(payload):
        applied += _apply(store, msg)

    # Coexistence backfill. Same path as live traffic, so states and staleness
    # derive normally and the wamid dedupe absorbs any overlap.
    for meta, messages in parse_history_chunks(payload):
        imported = sum(_apply(store, msg) for msg in messages)
        store.record_sync_chunk(meta["phase"], meta["progress"], imported)
        applied += imported

    # Display-only enrichment. Deliberately does not touch conversation state.
    for wa_message_id, read_at in parse_read_receipts(payload):
        store.mark_read(wa_message_id, read_at)

    return applied


def _apply(store: Store, msg) -> int:
    """Store one message and fold it into its conversation. 0 if already seen."""
    if not store.add_message(msg):
        return 0
    store.upsert_contact(Contact(wa_id=msg.wa_id))
    store.save_conversation(apply_message(store.get_conversation(msg.wa_id), msg))
    return 1


def sync_status(store: Store) -> dict:
    """What the dashboard shows while a freshly connected number backfills.

    'Complete' is deliberately loose: Meta sends no end-of-sync event, and a
    business with no traffic in a phase gets no chunks for it. A phase that has
    reported 100% is done; anything else is still importing.
    """
    phases = store.sync_phases()
    if not phases:
        return {"active": False, "started": False, "imported": 0, "phases": []}

    return {
        "started": True,
        "active": any(p["progress"] < 100 for p in phases),
        "imported": sum(p["imported"] for p in phases),
        "phases": phases,
    }


def set_amount(store: Store, wa_id: str, amount: Optional[int]) -> Conversation:
    """One field. No paid amount, no history, no partial payments — that is a
    deliberate v2 boundary, not an oversight."""
    conv = store.get_conversation(wa_id)
    if conv is None:
        raise KeyError(wa_id)
    conv.quoted_amount = amount if amount and amount > 0 else None
    conv.quoted_at = utcnow() if conv.quoted_amount else None
    store.save_conversation(conv)
    return conv


def set_outcome(store: Store, wa_id: str, outcome: Optional[Outcome]) -> Conversation:
    conv = store.get_conversation(wa_id)
    if conv is None:
        raise KeyError(wa_id)
    if outcome is None:
        reopen(conv)
    else:
        close(conv, outcome)
    store.save_conversation(conv)
    return conv


def _elapsed(since: datetime, now: datetime) -> str:
    mins = max(int((now - since).total_seconds() // 60), 0)
    if mins < 60:
        return f"{mins} min"
    if mins < 60 * 48:
        return f"{mins // 60} hours"
    return f"{mins // 1440} days"


def conversation_view(store: Store, conv: Conversation, now: datetime) -> dict:
    """Shape the UI consumes. All copy rules are enforced here so no client can
    accidentally render a bare duration or claim a message was unseen."""
    overdue = is_overdue(conv, now=now, stale_hours=config.STALE_HOURS)
    name = store.contact_name(conv.wa_id)
    msgs = store.messages_for(conv.wa_id, limit=3)

    if conv.state is ConvState.CLOSED:
        status = {"won": "Won", "lost": "Lost", "no_deal": "No deal"}[conv.outcome.value]
    else:
        status = ("You need to reply" if conv.state is ConvState.AWAITING_REPLY
                  else "Waiting on customer")

    return {
        "wa_id": conv.wa_id,
        "name": name or f"+{conv.wa_id}",
        "state": conv.state.value,
        "outcome": conv.outcome.value if conv.outcome else None,
        "is_open": conv.is_open,
        "status": status,
        # Always names the silent party — never a bare duration.
        "wait_text": (f"{waiting_for(conv)} for {_elapsed(conv.last_message_at, now)}"
                      if conv.is_open else "tracking stopped"),
        "overdue": overdue,
        "overdue_label": _elapsed(conv.last_message_at, now) if overdue else None,
        "hours_silent": (now - conv.last_message_at).total_seconds() / 3600.0,
        "quoted_amount": conv.quoted_amount,
        "last_message": msgs[-1].text if msgs else None,
        "messages": [
            {
                "direction": m.direction.value,
                "text": m.text,
                "at": m.timestamp.isoformat(),
                # Only ever true on a confirmed receipt. Absence renders nothing —
                # it is not evidence the customer did not read it.
                "seen": m.read_at is not None,
            }
            for m in msgs
        ],
    }


def summary(store: Store, now: datetime) -> dict:
    """The two money cards. Both carry their own denominator, always."""
    convs = store.all_conversations()
    open_convs = [c for c in convs if c.is_open]
    overdue = [c for c in open_convs if is_overdue(c, now=now, stale_hours=config.STALE_HOURS)]
    overdue_amt = [c for c in overdue if c.quoted_amount]
    won = [c for c in convs if c.outcome is Outcome.WON]
    won_amt = [c for c in won if c.quoted_amount]

    return {
        "currency": config.CURRENCY,
        "business_name": config.BUSINESS_NAME,
        "at_risk_total": sum(c.quoted_amount for c in overdue_amt),
        "at_risk_counted": len(overdue_amt),
        "at_risk_overdue": len(overdue),
        "at_risk_untracked": len(overdue) - len(overdue_amt),
        "oldest_hours": max((now - c.last_message_at).total_seconds() / 3600.0
                            for c in open_convs) if open_convs else 0,
        "won_total": sum(c.quoted_amount for c in won_amt),
        "won_counted": len(won_amt),
        "won_count": len(won),
        "counts": {
            "open": len(open_convs),
            "awaiting_reply": sum(1 for c in open_convs if c.state is ConvState.AWAITING_REPLY),
            "awaiting_customer": sum(1 for c in open_convs if c.state is ConvState.AWAITING_CUSTOMER),
            "overdue": len(overdue),
            "closed": len(convs) - len(open_convs),
        },
    }
