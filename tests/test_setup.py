"""First-time setup and number + password login.

The client picks their own password through a link that works once. That link
is the entire proof of ownership - there is no OTP, because the product never
sends WhatsApp messages - so the tests here are mostly about the ways a claim
link can be abused.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import auth, config, main
from app.store import Store


@pytest.fixture
def client(tmp_path, monkeypatch):
    store = Store(str(tmp_path / "t.db"))
    monkeypatch.setattr(main, "store", store)
    monkeypatch.setattr(config, "ADMIN_PASSWORD", "owner-override")
    monkeypatch.setattr(auth, "_failures", {})
    with TestClient(main.app, follow_redirects=False) as c:
        yield c
    store.close()


def mint(client) -> str:
    code = auth.new_setup_code()
    main.store.add_setup_code(auth.hash_setup_code(code))
    return code


def do_setup(client, code, number="+971 50 123 4567", password="correct-horse",
             confirm=None):
    return client.post("/setup", data={"code": code, "number": number,
                                       "password": password,
                                       "confirm": confirm or password})


# ---- password hashing ----

def test_password_round_trips_and_rejects_the_wrong_one():
    stored = auth.hash_password("correct-horse")
    assert auth.verify_password("correct-horse", stored)
    assert not auth.verify_password("Correct-horse", stored)
    assert "correct-horse" not in stored, "the password must not be recoverable"


def test_same_password_hashes_differently_each_time():
    """Per-account salt: two clients with the same password must not collide."""
    assert auth.hash_password("same") != auth.hash_password("same")


def test_verify_survives_a_corrupt_stored_value():
    for junk in ("", "nonsense", "pbkdf2_sha256$notanint$aa$bb", None):
        assert not auth.verify_password("x", junk)


@pytest.mark.parametrize("typed,expected", [
    ("+971 50 123 4567", "971501234567"),
    ("00971501234567", "971501234567"),
    ("971-50-123-4567", "971501234567"),
])
def test_numbers_are_normalised_however_they_are_typed(typed, expected):
    assert auth.normalise_number(typed) == expected


# ---- the claim link ----

def test_setup_creates_the_account_and_signs_them_in(client):
    r = do_setup(client, mint(client))
    assert r.status_code == 303 and r.headers["location"] == "/"
    assert auth.SESSION_COOKIE in r.cookies
    assert main.store.account()["wa_number"] == "971501234567"


def test_a_link_works_exactly_once(client):
    code = mint(client)
    assert do_setup(client, code).status_code == 303
    main.store.conn.execute("DELETE FROM account")   # simulate a second claimant
    main.store.conn.commit()
    assert "expired" in do_setup(client, code).text


def test_an_invented_code_is_refused(client):
    mint(client)
    assert "expired" in do_setup(client, "guessed-it").text
    assert main.store.account() is None


def test_setup_is_closed_once_an_account_exists(client):
    """A forwarded link must not let anyone re-register over a live client."""
    do_setup(client, mint(client))
    second = mint(client)
    r = client.post("/setup", data={"code": second, "number": "923000000000",
                                    "password": "another-one",
                                    "confirm": "another-one"})
    assert r.status_code == 303 and r.headers["location"] == "/login"
    assert main.store.account()["wa_number"] == "971501234567"


def test_mismatched_and_short_passwords_are_rejected(client):
    code = mint(client)
    assert "do not match" in do_setup(client, code, confirm="something-else").text
    assert "at least" in do_setup(client, code, password="short", confirm="short").text
    assert main.store.account() is None, "a rejected attempt must not burn the link"
    assert do_setup(client, code).status_code == 303


def test_the_code_is_stored_hashed(client):
    code = mint(client)
    rows = main.store.conn.execute("SELECT code_hash FROM setup_codes").fetchall()
    assert code not in [r["code_hash"] for r in rows]


# ---- login ----

def test_login_needs_both_the_number_and_the_password(client):
    do_setup(client, mint(client))
    client.cookies.clear()

    bad_number = client.post("/login", data={"number": "923999999999",
                                             "password": "correct-horse"})
    assert bad_number.headers["location"] == "/login?bad=1"

    bad_pass = client.post("/login", data={"number": "971501234567",
                                           "password": "wrong"})
    assert bad_pass.headers["location"] == "/login?bad=1"

    good = client.post("/login", data={"number": "+971 50 123 4567",
                                       "password": "correct-horse"})
    assert good.headers["location"] == "/"


def test_owner_override_still_works(client):
    """Support access has to survive a client forgetting their password."""
    do_setup(client, mint(client))
    client.cookies.clear()
    r = client.post("/login", data={"number": "", "password": "owner-override"})
    assert r.headers["location"] == "/"


def test_data_stays_locked_until_login(client):
    do_setup(client, mint(client))
    client.cookies.clear()
    assert client.get("/api/conversations").status_code == 401


def test_brute_force_is_throttled(client):
    do_setup(client, mint(client))
    client.cookies.clear()
    for _ in range(8):
        client.post("/login", data={"number": "971501234567", "password": "no"})
    assert client.post("/login", data={"number": "971501234567",
                                       "password": "correct-horse"}).status_code == 429
