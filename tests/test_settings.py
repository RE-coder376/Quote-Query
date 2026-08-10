"""Per-client settings: currency, weekend, threshold, timezone.

These change which conversations get flagged, so they are engine behaviour, not
preferences. The weekend rule is the one that matters most: without it every
Monday morning shows a queue of false alarms and the client stops trusting it.
"""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from app import currencies, settings
from app.settings import format_amount, working_hours_between
from app.store import Store

KHI = ZoneInfo("Asia/Karachi")


@pytest.fixture
def store(tmp_path):
    s = Store(str(tmp_path / "t.db"))
    yield s
    s.close()


# ---- currency search ----

@pytest.mark.parametrize("query,expected", [
    ("pk", "PKR"),          # country code, the thing people actually type
    ("pakistan", "PKR"),
    ("karachi", "PKR"),
    ("dubai", "AED"),
    ("uae", "AED"),
    ("aed", "AED"),
    ("saudi", "SAR"),
    ("united kingdom", "GBP"),
    ("rupee", "PKR"),       # ambiguous, but PKR is listed first on purpose
])
def test_search_puts_the_obvious_answer_first(query, expected):
    assert currencies.search(query)[0]["code"] == expected


def test_search_returns_nothing_for_nonsense():
    assert currencies.search("zzzzz") == []


def test_every_currency_is_self_consistent():
    for entry in currencies.as_json():
        assert entry["code"] == entry["code"].upper() and len(entry["code"]) == 3
        assert entry["grouping"] in ("lakh", "thousand")
        assert entry["terms"], f"{entry['code']} has no search terms"


# ---- amount formatting ----

def test_south_asian_grouping_is_used_where_it_is_expected():
    pkr = currencies.get("PKR")
    assert format_amount(100000, pkr) == "1,00,000"
    assert format_amount(10000000, pkr) == "1,00,00,000"
    assert format_amount(999, pkr) == "999"


def test_western_grouping_elsewhere():
    assert format_amount(1000000, currencies.get("AED")) == "1,000,000"


# ---- the weekend rule ----

def test_a_friday_evening_quote_is_not_stale_on_monday_morning():
    """The whole reason this exists. Fri 6pm -> Mon 9am is 63 clock hours but
    only 15 working hours, so a 24-hour threshold must not fire."""
    friday_evening = datetime(2026, 8, 7, 18, 0, tzinfo=KHI)   # Friday
    monday_morning = datetime(2026, 8, 10, 9, 0, tzinfo=KHI)   # Monday

    clock = (monday_morning - friday_evening).total_seconds() / 3600
    assert round(clock) == 63

    working = working_hours_between(friday_evening, monday_morning, [5, 6], KHI)
    assert round(working) == 15
    assert working < 24, "would have been flagged overdue for no reason"


def test_no_weekend_configured_means_plain_elapsed_time():
    a = datetime(2026, 8, 7, 18, 0, tzinfo=KHI)
    b = datetime(2026, 8, 10, 9, 0, tzinfo=KHI)
    assert round(working_hours_between(a, b, [], KHI)) == 63


def test_pakistan_only_loses_sunday():
    a = datetime(2026, 8, 7, 18, 0, tzinfo=KHI)      # Friday
    b = datetime(2026, 8, 10, 9, 0, tzinfo=KHI)      # Monday
    assert round(working_hours_between(a, b, [6], KHI)) == 39   # 63 - 24


def test_the_day_someone_messages_is_never_deducted():
    """A customer who writes on Sunday is still waiting on Sunday."""
    sunday_9am = datetime(2026, 8, 9, 9, 0, tzinfo=KHI)
    sunday_6pm = datetime(2026, 8, 9, 18, 0, tzinfo=KHI)
    assert working_hours_between(sunday_9am, sunday_6pm, [6], KHI) == 9


def test_time_cannot_run_backwards():
    later = datetime(2026, 8, 10, 9, 0, tzinfo=KHI)
    earlier = datetime(2026, 8, 7, 18, 0, tzinfo=KHI)
    assert working_hours_between(later, earlier, [5, 6], KHI) == 0.0


# ---- persistence and fallbacks ----

def test_settings_round_trip(store):
    store.save_settings({"currency": "PKR", "timezone": "Asia/Karachi",
                         "weekend": "sun", "stale_hours": "4",
                         "business_name": "Khan Dry Fruit"})
    assert settings.currency(store)["code"] == "PKR"
    assert settings.stale_hours(store) == 4
    assert settings.weekend_days(store) == [6]
    assert settings.tzinfo(store) == ZoneInfo("Asia/Karachi")
    assert settings.business_name(store) == "Khan Dry Fruit"


def test_unsaved_settings_fall_back_instead_of_crashing(store):
    """An instance configured before settings existed must keep working."""
    assert settings.stale_hours(store) >= 1
    assert settings.currency(store)["code"]
    assert settings.weekend_days(store) is not None


def test_a_broken_timezone_falls_back_to_utc(store):
    store.save_settings({"timezone": "Mars/Olympus_Mons"})
    assert settings.tzinfo(store) == timezone.utc


def test_a_broken_threshold_falls_back(store):
    store.save_settings({"stale_hours": "not a number"})
    assert settings.stale_hours(store) >= 1
