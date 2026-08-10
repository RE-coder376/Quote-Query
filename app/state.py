"""The state engine.

Everything here is a pure function of message direction and elapsed time. No
keyword detection, no AI, no read receipts. That is not a simplification of a
richer design - it is the only design the available webhooks can support
honestly, and it happens to also be the product's positioning.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from .models import ConvState, Conversation, Direction, Message, Outcome, utcnow

# One global default. No per-client configuration in v1.
DEFAULT_STALE_HOURS = 24


def state_for(direction: Direction) -> ConvState:
    """Who spoke last decides who owes a reply. That is the whole rule."""
    return (
        ConvState.AWAITING_REPLY
        if direction is Direction.INBOUND
        else ConvState.AWAITING_CUSTOMER
    )


def apply_message(conv: Optional[Conversation], msg: Message) -> Conversation:
    """Fold a message into a conversation.

    An inbound message on a closed conversation reopens it. That is not a
    special case bolted on - it falls out of the rule above, because the
    customer speaking last *is* AWAITING_REPLY. Nothing to un-archive.
    """
    if conv is None:
        return Conversation(
            wa_id=msg.wa_id,
            last_message_at=msg.timestamp,
            last_direction=msg.direction,
            state=state_for(msg.direction),
        )

    # Out-of-order delivery is normal on webhooks; never let an old message
    # rewrite a newer state.
    if msg.timestamp < conv.last_message_at:
        return conv

    conv.last_message_at = msg.timestamp
    conv.last_direction = msg.direction

    if conv.state is ConvState.CLOSED and msg.direction is Direction.INBOUND:
        conv.state = ConvState.AWAITING_REPLY
        conv.outcome = None
        conv.closed_at = None
    elif conv.state is not ConvState.CLOSED:
        conv.state = state_for(msg.direction)

    return conv


def close(conv: Conversation, outcome: Outcome, at: Optional[datetime] = None) -> Conversation:
    """Stop the countdown. Won reuses quoted_amount - there is deliberately no
    'paid' field, because tracking what was collected reopens the accounting
    scope this product is positioned against."""
    conv.state = ConvState.CLOSED
    conv.outcome = outcome
    conv.closed_at = at or utcnow()
    return conv


def reopen(conv: Conversation) -> Conversation:
    """Manual mirror of 'they messaged again'."""
    conv.state = state_for(conv.last_direction)
    conv.outcome = None
    conv.closed_at = None
    return conv


def is_overdue(conv: Conversation, now: Optional[datetime] = None,
               stale_hours: int = DEFAULT_STALE_HOURS) -> bool:
    """Overlay flag, not a state. Applies to either open state: a quote the
    customer has ignored for 12 days is as much a problem as one we have not
    answered."""
    if not conv.is_open:
        return False
    now = now or utcnow()
    return (now - conv.last_message_at) >= timedelta(hours=stale_hours)


def waiting_for(conv: Conversation) -> str:
    """Copy rule: never render a bare duration. It never says whose reply is
    missing. Always name the silent party."""
    if not conv.is_open:
        return "tracking stopped"
    return (
        "no reply from you"
        if conv.state is ConvState.AWAITING_REPLY
        else "no customer reply"
    )
