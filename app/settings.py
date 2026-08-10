"""Per-client settings, chosen at setup and editable afterwards.

These are the things that genuinely change what the radar *does*, not just how
it looks. Anything that only changes wording stays hardcoded; every value here
earns its place by altering which conversations get flagged.

Falls back to the environment so an instance with no saved settings behaves
exactly as it did before this file existed.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from . import config, currencies

# Monday = 0, matching datetime.weekday().
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
             "Saturday", "Sunday"]

# The common patterns, so setup is one click rather than seven checkboxes.
WEEKEND_PRESETS = {
    "sun": ([6], "Sunday only (Pakistan, India)"),
    "sat-sun": ([5, 6], "Saturday and Sunday (UAE, UK, US, Europe)"),
    "fri-sat": ([4, 5], "Friday and Saturday (Saudi, Kuwait, Qatar, Egypt)"),
    "fri": ([4], "Friday only"),
    "none": ([], "We work every day"),
}

DEFAULTS = {
    "business_name": "",
    "currency": "",
    "timezone": "UTC",
    "weekend": "sat-sun",
    "stale_hours": "24",
}


def all_settings(store) -> dict:
    saved = store.settings()
    out = dict(DEFAULTS)
    out.update({k: v for k, v in saved.items() if v is not None})

    # Environment supplies the fallback so nothing regresses on an instance that
    # was configured before settings existed.
    if not out["business_name"]:
        out["business_name"] = config.BUSINESS_NAME
    if not out["currency"]:
        out["currency"] = config.CURRENCY or currencies.DEFAULT
    return out


def currency(store) -> dict:
    return currencies.get(all_settings(store)["currency"])


def business_name(store) -> str:
    return all_settings(store)["business_name"]


def stale_hours(store) -> int:
    try:
        return max(int(all_settings(store)["stale_hours"]), 1)
    except (TypeError, ValueError):
        return config.STALE_HOURS


def tzinfo(store) -> timezone | ZoneInfo:
    name = all_settings(store)["timezone"]
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError, KeyError):
        return timezone.utc


def weekend_days(store) -> list[int]:
    key = all_settings(store)["weekend"]
    return WEEKEND_PRESETS.get(key, WEEKEND_PRESETS["sat-sun"])[0]


def working_hours_between(start: datetime, end: datetime,
                          weekend: list[int], tz) -> float:
    """Hours elapsed, ignoring whole weekend days in the client's own timezone.

    Without this the dashboard cries wolf every Monday: a quote answered Friday
    evening looks 60 hours stale before anyone has had a chance to touch it.
    Counting only working days is the difference between a queue people trust
    and one they learn to ignore.

    Whole days only - not opening hours. A message at 9pm is still overnight,
    and pretending to know a joinery firm's shift pattern would be false
    precision.
    """
    if end <= start:
        return 0.0
    if not weekend:
        return (end - start).total_seconds() / 3600.0

    local_start = start.astimezone(tz)
    local_end = end.astimezone(tz)

    total = (local_end - local_start).total_seconds() / 3600.0

    # Subtract each full weekend day that sits strictly inside the span. The
    # partial first and last days are left alone: someone messaging on a Sunday
    # is still waiting, and the day they message is not deducted.
    day = (local_start + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0)
    while day < local_end:
        day_end = day + timedelta(days=1)
        if day.weekday() in weekend:
            overlap = (min(day_end, local_end) - day).total_seconds() / 3600.0
            total -= max(overlap, 0.0)
        day = day_end

    return max(total, 0.0)


def format_amount(amount: Optional[int], cur: dict) -> str:
    """South Asian grouping where it is expected: 10,00,000 not 1,000,000.

    A Pakistani reader seeing western grouping has to stop and count digits, and
    a number people have to check is a number they do not trust.
    """
    if amount is None:
        return ""
    if cur.get("grouping") != "lakh":
        return f"{amount:,}"

    text = str(abs(amount))
    if len(text) <= 3:
        grouped = text
    else:
        head, tail = text[:-3], text[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        grouped = ",".join(parts + [tail])
    return ("-" if amount < 0 else "") + grouped
