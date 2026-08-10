"""Tests for the rules the whole product rests on."""
from datetime import datetime, timedelta, timezone

import pytest

from app.models import ConvState, Direction, Message, Outcome
from app.state import apply_message, close, is_overdue, reopen, waiting_for
from app.webhook import parse_messages, parse_read_receipts, verify_signature

T0 = datetime(2026, 8, 1, 9, 0, tzinfo=timezone.utc)


def msg(direction, at, mid="m1", wa_id="971569961630"):
    return Message(wa_message_id=mid, wa_id=wa_id, direction=direction, timestamp=at)


def test_customer_speaks_last_means_we_owe_a_reply():
    conv = apply_message(None, msg(Direction.INBOUND, T0))
    assert conv.state is ConvState.AWAITING_REPLY


def test_we_speak_last_means_they_owe_us():
    conv = apply_message(None, msg(Direction.INBOUND, T0))
    conv = apply_message(conv, msg(Direction.OUTBOUND, T0 + timedelta(hours=1), "m2"))
    assert conv.state is ConvState.AWAITING_CUSTOMER


def test_inbound_message_reopens_a_closed_conversation():
    """The headline promise: nothing to un-archive."""
    conv = apply_message(None, msg(Direction.OUTBOUND, T0))
    close(conv, Outcome.WON)
    assert conv.state is ConvState.CLOSED

    conv = apply_message(conv, msg(Direction.INBOUND, T0 + timedelta(days=30), "m2"))
    assert conv.state is ConvState.AWAITING_REPLY
    assert conv.outcome is None
    assert conv.closed_at is None


def test_outbound_message_does_not_reopen_a_closed_conversation():
    """Only the customer coming back reopens it. Us sending something (a
    seasonal greeting, say) must not resurrect a won deal."""
    conv = apply_message(None, msg(Direction.OUTBOUND, T0))
    close(conv, Outcome.WON)
    conv = apply_message(conv, msg(Direction.OUTBOUND, T0 + timedelta(days=5), "m2"))
    assert conv.state is ConvState.CLOSED


def test_out_of_order_delivery_does_not_rewrite_state():
    conv = apply_message(None, msg(Direction.INBOUND, T0))
    conv = apply_message(conv, msg(Direction.OUTBOUND, T0 + timedelta(hours=2), "m2"))
    # a late-arriving older inbound must not flip us back
    conv = apply_message(conv, msg(Direction.INBOUND, T0 + timedelta(minutes=5), "m3"))
    assert conv.state is ConvState.AWAITING_CUSTOMER
    assert conv.last_message_at == T0 + timedelta(hours=2)


@pytest.mark.parametrize("hours,expected", [(23, False), (24, True), (300, True)])
def test_overdue_is_a_threshold_on_elapsed_time(hours, expected):
    conv = apply_message(None, msg(Direction.OUTBOUND, T0))
    assert is_overdue(conv, now=T0 + timedelta(hours=hours)) is expected


def test_overdue_applies_to_both_open_states():
    """A quote the customer ignored for 12 days is as much a problem as one we
    never answered - urgency is not the same axis as direction."""
    ours = apply_message(None, msg(Direction.INBOUND, T0))
    theirs = apply_message(None, msg(Direction.OUTBOUND, T0))
    later = T0 + timedelta(days=12)
    assert is_overdue(ours, now=later) and is_overdue(theirs, now=later)


def test_closed_conversations_are_never_overdue():
    conv = apply_message(None, msg(Direction.OUTBOUND, T0))
    close(conv, Outcome.LOST)
    assert is_overdue(conv, now=T0 + timedelta(days=99)) is False


def test_reopen_restores_the_state_implied_by_the_last_message():
    conv = apply_message(None, msg(Direction.OUTBOUND, T0))
    close(conv, Outcome.NO_DEAL)
    reopen(conv)
    assert conv.state is ConvState.AWAITING_CUSTOMER


def test_wait_copy_always_names_the_silent_party():
    """A bare duration never says whose reply is missing."""
    ours = apply_message(None, msg(Direction.INBOUND, T0))
    theirs = apply_message(None, msg(Direction.OUTBOUND, T0))
    assert waiting_for(ours) == "no reply from you"
    assert waiting_for(theirs) == "no customer reply"


# ---- webhook parsing ----

def test_parses_inbound_and_echoed_outbound():
    payload = {"entry": [{"changes": [
        {"field": "messages", "value": {"messages": [
            {"id": "wamid.in", "from": "971569961630", "timestamp": "1754038800",
             "type": "text", "text": {"body": "Can you quote this?"}}]}},
        {"field": "smb_message_echoes", "value": {"message_echoes": [
            {"id": "wamid.out", "to": "971569961630", "timestamp": "1754042400",
             "type": "text", "text": {"body": "AED 44,500"}}]}},
    ]}]}
    out = list(parse_messages(payload))
    assert [m.direction for m in out] == [Direction.INBOUND, Direction.OUTBOUND]
    assert out[0].text == "Can you quote this?"


def test_malformed_nodes_are_skipped_not_raised():
    """A 500 makes Meta retry the whole batch; drop bad nodes instead."""
    payload = {"entry": [{"changes": [{"field": "messages", "value": {
        "messages": [{"timestamp": "1754038800"}, {"id": "x", "from": "971500000000",
                                                   "timestamp": "1754038800"}]}}]}]}
    assert len(list(parse_messages(payload))) == 1


def test_read_receipts_parse_but_only_read_status():
    payload = {"entry": [{"changes": [{"value": {"statuses": [
        {"id": "wamid.out", "status": "delivered", "timestamp": "1754042400"},
        {"id": "wamid.out2", "status": "read", "timestamp": "1754046000"},
    ]}}]}]}
    got = list(parse_read_receipts(payload))
    assert [g[0] for g in got] == ["wamid.out2"]


def test_signature_verification_rejects_forgery():
    body = b'{"entry":[]}'
    assert verify_signature("secret", body, "sha256=deadbeef") is False
    assert verify_signature("secret", body, None) is False
