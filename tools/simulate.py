"""Replay realistic Meta webhook deliveries at a running QuoteRadar.

Business verification runs on Meta's clock and has not started. This lets the
whole loop - signature check, ingest, state engine, dashboard - be exercised
today with payloads shaped exactly like the real ones.

    python -m tools.simulate                      # seed a realistic day
    python -m tools.simulate --history            # replay a Coexistence backfill
    python -m tools.simulate --url http://host    # point elsewhere

Payload shapes follow Meta's documented `messages`, `smb_message_echoes`,
`statuses`, `history` and `smb_app_state_sync` webhooks.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import time
import urllib.request
from datetime import datetime, timedelta, timezone

from app import config

NOW = datetime.now(timezone.utc)


def ts(hours_ago: float) -> int:
    return int((NOW - timedelta(hours=hours_ago)).timestamp())


# (wa_id, name, [(hours_ago, direction, text)])
SCRIPT = [
    ("971569961630", "Zesto Tech Joinery", [
        (240, "in", "Please quote the full showroom fit-out - 240 sqm, handover by Oct."),
        (214, "out", "Attached: full scope + AED 132,000. Happy to walk through it."),
    ]),
    ("971588696981", "ASM Interiors", [
        (120, "in", "What are our options for the glass partitions?"),
        (74, "out", "Three options attached - single glazed, double, and acoustic."),
    ]),
    ("971509632272", "Build Craft Interiors", [
        (53, "in", "Any update on the counter joinery price? Landlord is chasing us."),
    ]),
    ("971505992786", "Al Faris Carpentry", [
        (300, "in", "Price for 6 storage cabinets for the treatment rooms?"),
        (292, "out", "AED 9,000 supplied and fitted, 2 weeks from approval."),
    ]),
    ("971559693009", "Halo Interiors", [
        (6, "in", "Morning - we need a price for re-laminating 40 corridor doors."),
    ]),
    ("971582357580", "Ideal Fitouts", [
        (0.4, "in", "Salam, are you free for a site visit Tuesday?"),
    ]),
]


BUSINESS = "97140000000"

# Coexistence hands over ~6 months on connect. These are the threads a client
# sees the moment they connect - their own quotes, already stale, with money
# attached. (wa_id, name, [(days_ago, direction, text)])
HISTORY = [
    ("971544120983", "Marina Heights - Rashid", [
        (154, "in", "We're fitting out unit 1204, can you quote the wardrobes?"),
        (153, "out", "AED 46,500 for all four rooms, 3 weeks from sign-off."),
    ]),
    ("971502238815", "Dana - Al Quoz warehouse", [
        (88, "in", "Need mezzanine office partitions priced, roughly 90 sqm."),
        (87, "out", "AED 71,200 including electrical first fix."),
        (86, "in", "Thanks, discussing with my partner."),
    ]),
    ("971557741206", "Khalid Restaurant Group", [
        (41, "in", "Quote for the counter and back bar joinery please."),
        (40, "out", "AED 118,000. Drawings attached."),
    ]),
    ("971509118834", "Sara - villa Jumeirah", [
        (12, "in", "Can you re-send the kitchen quote? Lost the message."),
        (11, "out", "Re-sent - AED 88,400 as before, valid 30 days."),
    ]),
]


def history_chunk(phase: int, chunk_order: int, progress: int,
                  threads: list[dict]) -> dict:
    """The `history` webhook Meta sends after a Coexistence connect."""
    return {"field": "history", "value": {
        "messaging_product": "whatsapp",
        "metadata": {"display_phone_number": BUSINESS, "phone_number_id": "PNID"},
        "history": [{
            "metadata": {"phase": phase, "chunk_order": chunk_order,
                         "progress": progress},
            "threads": threads,
        }]}}


def history_thread(wa_id: str, turns: list[tuple]) -> dict:
    """Direction is carried by `from` only - there is no from_me flag."""
    messages = []
    for i, (days_ago, direction, text) in enumerate(turns):
        messages.append({
            "from": BUSINESS if direction == "out" else wa_id,
            "to": wa_id if direction == "out" else BUSINESS,
            "id": f"wamid.hist.{wa_id}.{i}",
            "timestamp": str(ts(days_ago * 24)),
            "type": "text",
            "text": {"body": text},
            "history_context": {"status": "READ" if direction == "out" else "DELIVERED"},
        })
    return {"id": wa_id, "messages": messages}


def state_sync(contacts: list[tuple[str, str]]) -> dict:
    """The Business app's address book - better names than WhatsApp profiles."""
    return {"field": "smb_app_state_sync", "value": {
        "messaging_product": "whatsapp",
        "metadata": {"display_phone_number": BUSINESS, "phone_number_id": "PNID"},
        "state_sync": [
            {"type": "contact", "action": "add",
             "contact": {"full_name": name, "first_name": name.split()[0],
                         "phone_number": f"+{wa_id}"},
             "metadata": {"timestamp": str(ts(0))}}
            for wa_id, name in contacts
        ]}}


def envelope(changes: list[dict]) -> dict:
    return {"object": "whatsapp_business_account",
            "entry": [{"id": "WABA_ID", "changes": changes}]}


def inbound(wa_id: str, mid: str, at: int, text: str) -> dict:
    return {"field": "messages", "value": {
        "messaging_product": "whatsapp",
        "metadata": {"display_phone_number": "97140000000", "phone_number_id": "PNID"},
        "messages": [{"from": wa_id, "id": mid, "timestamp": str(at),
                      "type": "text", "text": {"body": text}}]}}


def echo(wa_id: str, mid: str, at: int, text: str) -> dict:
    """What Coexistence sends when staff type in the WhatsApp Business app."""
    return {"field": "smb_message_echoes", "value": {
        "messaging_product": "whatsapp",
        "metadata": {"display_phone_number": "97140000000", "phone_number_id": "PNID"},
        "message_echoes": [{"to": wa_id, "id": mid, "timestamp": str(at),
                            "type": "text", "text": {"body": text}}]}}


def read_status(mid: str, at: int) -> dict:
    return {"field": "messages", "value": {"statuses": [
        {"id": mid, "status": "read", "timestamp": str(at), "recipient_id": "x"}]}}


def post(url: str, payload: dict) -> tuple[int, str]:
    body = json.dumps(payload).encode()
    sig = hmac.new(config.APP_SECRET.encode(), body, hashlib.sha256).hexdigest()
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json",
                 "X-Hub-Signature-256": f"sha256={sig}"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.status, resp.read().decode()


def replay_history(hook: str, retry: bool = False) -> None:
    """Send the backfill the way Meta does: newest phase first, chunks that can
    arrive out of order, contacts arriving separately."""
    status, body = post(hook, envelope([state_sync([(w, n) for w, n, _ in HISTORY])]))
    print(f"contacts  -> {status} {body}")

    # phase 0: last day, 1: day 1-90, 2: day 90-180.
    by_phase = {0: [], 1: [], 2: []}
    for wa_id, _name, turns in HISTORY:
        oldest = max(d for d, _dir, _t in turns)
        phase = 0 if oldest <= 1 else (1 if oldest <= 90 else 2)
        by_phase[phase].append(history_thread(wa_id, turns))

    for phase in (0, 1, 2):
        threads = by_phase[phase]
        if not threads:
            continue
        # Two chunks per phase, second one sent first, to prove ordering is
        # irrelevant to the resulting states.
        half = max(len(threads) // 2, 1)
        for order, part in ((2, threads[half:]), (1, threads[:half])):
            if not part:
                continue
            progress = 100 if order == 1 else 50
            status, body = post(hook, envelope(
                [history_chunk(phase, order, progress, part)]))
            print(f"phase {phase}/{order} -> {status} {body}")

    if retry:
        time.sleep(0.2)
        threads = [history_thread(w, t) for w, _n, t in HISTORY]
        status, body = post(hook, envelope([history_chunk(1, 1, 100, threads)]))
        print(f"replay    -> {status} {body}   (applied should be 0)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000")
    ap.add_argument("--retry-test", action="store_true",
                    help="send everything twice to prove ingestion is idempotent")
    ap.add_argument("--history", action="store_true",
                    help="replay a Coexistence backfill instead of a live day")
    args = ap.parse_args()
    hook = args.url.rstrip("/") + "/webhook"

    if args.history:
        replay_history(hook, retry=args.retry_test)
        return

    changes, seen_ids = [], []
    for wa_id, _name, turns in SCRIPT:
        for i, (hours_ago, direction, text) in enumerate(turns):
            mid = f"wamid.{wa_id}.{i}"
            at = ts(hours_ago)
            if direction == "in":
                changes.append(inbound(wa_id, mid, at, text))
            else:
                changes.append(echo(wa_id, mid, at, text))
                seen_ids.append(mid)

    status, body = post(hook, envelope(changes))
    print(f"seed      -> {status} {body}")

    # One outbound confirmed read. The others get nothing, on purpose: a missing
    # receipt is not evidence of anything and must render as nothing.
    if seen_ids:
        status, body = post(hook, envelope([read_status(seen_ids[0], ts(200))]))
        print(f"read tick -> {status} {body}")

    if args.retry_test:
        time.sleep(0.2)
        status, body = post(hook, envelope(changes))
        print(f"replay    -> {status} {body}   (applied should be 0)")


if __name__ == "__main__":
    main()
