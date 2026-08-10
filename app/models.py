"""Core objects.

Deliberately small. The whole engine rests on two facts per conversation:
who spoke last, and how long ago. Everything else is enrichment that must
never drive a state — see system_design/webhook_signal_verification_2026-08-06.md
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Direction(str, Enum):
    """Who sent a message. This is the only signal Coexistence delivers 100%
    of the time, so it is the only signal the state machine is allowed to use."""

    INBOUND = "in"    # the customer
    OUTBOUND = "out"  # the business (app echo or API send)


class ConvState(str, Enum):
    """Three states. Not five.

    'Read but not replied' is unbuildable: no webhook reports that staff opened
    an incoming message, so it cannot be told apart from 'unread'. They collapse
    into AWAITING_REPLY, and the required action is identical either way.
    """

    AWAITING_REPLY = "awaiting_reply"        # customer spoke last; we owe them
    AWAITING_CUSTOMER = "awaiting_customer"  # we spoke last; they owe us
    CLOSED = "closed"                        # won / lost / no deal


class Outcome(str, Enum):
    WON = "won"
    LOST = "lost"
    NO_DEAL = "no_deal"


@dataclass
class Contact:
    wa_id: str                      # E.164 digits, no '+'
    display_name: Optional[str] = None
    first_seen_at: datetime = field(default_factory=utcnow)


@dataclass
class Message:
    wa_message_id: str
    wa_id: str
    direction: Direction
    timestamp: datetime
    text: Optional[str] = None
    # Enrichment only. A missing read receipt is NOT evidence of anything:
    # recipients can disable receipts, and the status simply never arrives.
    read_at: Optional[datetime] = None


@dataclass
class Conversation:
    wa_id: str
    last_message_at: datetime
    last_direction: Direction
    state: ConvState = ConvState.AWAITING_REPLY
    outcome: Optional[Outcome] = None
    quoted_amount: Optional[int] = None   # minor-unit-free whole currency; optional by design
    quoted_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    @property
    def is_open(self) -> bool:
        return self.state is not ConvState.CLOSED
