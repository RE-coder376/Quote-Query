"""Parsing and verification for Meta WhatsApp webhooks.

Handles five payload shapes we actually depend on:
  messages          - inbound customer messages           (100% reliable)
  smb_message_echoes - outbound sent from the Business app (100% reliable)
  statuses          - sent/delivered/read on our outbound  (enrichment ONLY)
  history           - Coexistence backfill, ~6 months of prior threads
  smb_app_state_sync - the Business app's own contact list (names only)

`statuses` is parsed but must never drive a state: if the recipient disables
read receipts the 'read' status never fires, so absent-read and unread are
indistinguishable. See system_design/webhook_signal_verification_2026-08-06.md
"""
from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timezone
from typing import Iterator, Optional

from .models import Direction, Message


def verify_signature(app_secret: str, raw_body: bytes, header: Optional[str]) -> bool:
    """Meta signs each delivery with X-Hub-Signature-256. Reject anything that
    does not match - an unauthenticated webhook lets anyone forge conversations."""
    if not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(app_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header[7:])


def _ts(value) -> datetime:
    return datetime.fromtimestamp(int(value), tz=timezone.utc)


def _text_of(node: dict) -> Optional[str]:
    if node.get("type") == "text":
        return (node.get("text") or {}).get("body")
    # Non-text messages still count as activity; the body is not needed, and we
    # deliberately do not inspect content anywhere in the product.
    return None


def parse_messages(payload: dict) -> Iterator[Message]:
    """Yield every message in a webhook delivery, inbound or outbound.

    A delivery can carry several entries, each with several changes, each with
    several messages. Flatten defensively - malformed shapes are skipped rather
    than raising, because a 500 makes Meta retry the whole batch.
    """
    for entry in payload.get("entry", []) or []:
        for change in entry.get("changes", []) or []:
            value = change.get("value") or {}
            field = change.get("field") or ""

            # inbound customer messages
            for node in value.get("messages", []) or []:
                wa_id = node.get("from")
                mid = node.get("id")
                if not wa_id or not mid:
                    continue
                yield Message(
                    wa_message_id=mid,
                    wa_id=wa_id,
                    direction=Direction.INBOUND,
                    timestamp=_ts(node.get("timestamp", 0)),
                    text=_text_of(node),
                )

            # outbound messages typed by staff in the WhatsApp Business app
            if field == "smb_message_echoes":
                for node in value.get("message_echoes", []) or []:
                    wa_id = node.get("to")
                    mid = node.get("id")
                    if not wa_id or not mid:
                        continue
                    yield Message(
                        wa_message_id=mid,
                        wa_id=wa_id,
                        direction=Direction.OUTBOUND,
                        timestamp=_ts(node.get("timestamp", 0)),
                        text=_text_of(node),
                    )


def parse_contacts(payload: dict) -> Iterator[tuple[str, str]]:
    """(wa_id, profile_name) from inbound deliveries.

    Meta includes the sender's WhatsApp profile name alongside inbound messages.
    It is the only name we ever get, and it can change, so it is stored as a
    best-effort display label rather than an identity.
    """
    for entry in payload.get("entry", []) or []:
        for change in entry.get("changes", []) or []:
            for node in (change.get("value") or {}).get("contacts", []) or []:
                wa_id = node.get("wa_id")
                name = ((node.get("profile") or {}).get("name") or "").strip()
                if wa_id and name:
                    yield wa_id, name


def for_phone_number(payload: dict, phone_number_id: str) -> dict:
    """Drop every change that is not for this instance's own number.

    One instance serves one client. A delivery carrying another number - a
    misconfigured subscription, a shared app, or a forged payload that somehow
    passed signature checking - must never be folded in, because there is no
    per-tenant boundary below this point to catch it.

    An empty phone_number_id disables the filter. Changes with no metadata at
    all are kept: `statuses` deliveries can omit it, and they are enrichment.
    """
    if not phone_number_id:
        return payload

    entries = []
    for entry in payload.get("entry", []) or []:
        kept = []
        for change in entry.get("changes", []) or []:
            meta = (change.get("value") or {}).get("metadata")
            if meta is None or meta.get("phone_number_id") == phone_number_id:
                kept.append(change)
        if kept:
            entries.append({**entry, "changes": kept})

    return {**payload, "entry": entries}


def _digits(value: Optional[str]) -> str:
    return "".join(c for c in (value or "") if c.isdigit())


def parse_history_chunks(payload: dict) -> Iterator[tuple[dict, list[Message]]]:
    """Yield ((phase, chunk_order, progress), messages) for each history chunk.

    Chunked rather than flat because progress is reported per chunk, and the
    import indicator has to be attributed to the phase the messages came from.

    Meta hands over roughly six months of prior 1:1 conversations when a number
    connects, in three phases (0: last day, 1: day 1-90, 2: day 90-180), each
    split into chunks that can arrive in any order. Every message carries its
    original wamid, so the normal dedupe path handles overlap with live traffic.

    There is no `from_me` flag. Direction is derived by comparing the sender
    against the business's own number from `value.metadata.display_phone_number`;
    the thread id is always the customer, so it is used as the wa_id directly.
    """
    for entry in payload.get("entry", []) or []:
        for change in entry.get("changes", []) or []:
            if (change.get("field") or "") != "history":
                continue
            value = change.get("value") or {}
            business = _digits((value.get("metadata") or {}).get("display_phone_number"))

            for chunk in value.get("history", []) or []:
                messages = []
                for thread in chunk.get("threads", []) or []:
                    wa_id = thread.get("id")
                    if not wa_id:
                        continue
                    for node in thread.get("messages", []) or []:
                        mid = node.get("id")
                        if not mid:
                            continue
                        sender = _digits(node.get("from"))
                        outbound = bool(business) and sender == business
                        status = (node.get("history_context") or {}).get("status")
                        ts = _ts(node.get("timestamp", 0))
                        messages.append(Message(
                            wa_message_id=mid,
                            wa_id=_digits(wa_id) or wa_id,
                            direction=Direction.OUTBOUND if outbound else Direction.INBOUND,
                            timestamp=ts,
                            text=_text_of(node),
                            # History gives a confirmed read status but no read
                            # time, so the message's own timestamp stands in. Only
                            # the presence of a receipt is ever rendered.
                            read_at=ts if (outbound and status in ("READ", "PLAYED")) else None,
                        ))
                yield _chunk_meta(chunk.get("metadata") or {}), messages


def _chunk_meta(meta: dict) -> dict:
    """Progress is a percentage within the phase; phases are 0 (last day),
    1 (day 1-90) and 2 (day 90-180). Malformed values fall back to zero rather
    than dropping the messages the chunk carries."""
    def _int(key: str) -> int:
        try:
            return int(meta.get(key, 0))
        except (TypeError, ValueError):
            return 0

    return {"phase": _int("phase"), "chunk_order": _int("chunk_order"),
            "progress": _int("progress")}


def parse_history(payload: dict) -> Iterator[Message]:
    """Flat view of a history delivery, for callers that do not track progress."""
    for _meta, messages in parse_history_chunks(payload):
        yield from messages


def parse_state_sync_contacts(payload: dict) -> Iterator[tuple[str, str]]:
    """(wa_id, name) from the Business app's own address book.

    Better than profile names: this is what the business itself calls the
    customer, so the dashboard shows 'Ahmed - Marina kitchen' rather than a
    number. Deletions are ignored; a removed contact is not a removed thread.
    """
    for entry in payload.get("entry", []) or []:
        for change in entry.get("changes", []) or []:
            if (change.get("field") or "") != "smb_app_state_sync":
                continue
            for node in (change.get("value") or {}).get("state_sync", []) or []:
                if node.get("type") != "contact" or node.get("action") == "remove":
                    continue
                contact = node.get("contact") or {}
                wa_id = _digits(contact.get("phone_number"))
                name = (contact.get("full_name") or contact.get("first_name") or "").strip()
                if wa_id and name:
                    yield wa_id, name


def parse_read_receipts(payload: dict) -> Iterator[tuple[str, datetime]]:
    """(wa_message_id, read_at) for outbound messages confirmed read.

    Display-only. Absence of a receipt must never be rendered as 'unseen'.
    """
    for entry in payload.get("entry", []) or []:
        for change in entry.get("changes", []) or []:
            for node in (change.get("value") or {}).get("statuses", []) or []:
                if node.get("status") == "read" and node.get("id"):
                    yield node["id"], _ts(node.get("timestamp", 0))
