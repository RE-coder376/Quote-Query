"""The dashboard exposes clients' customers' private messages. It must not be open."""
import hashlib, hmac, json
import pytest
from fastapi.testclient import TestClient
from app import auth, config


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setattr(config, "ADMIN_PASSWORD", "correct-horse")
    monkeypatch.setattr(config, "SESSION_SECRET", "test-secret")
    import importlib
    from app import main
    importlib.reload(main)
    auth._failures.clear()
    return TestClient(main.app, follow_redirects=False)


DATA_ROUTES = ["/api/conversations", "/api/conversations/971500000001"]


@pytest.mark.parametrize("path", DATA_ROUTES)
def test_customer_data_requires_a_session(client, path):
    assert client.get(path).status_code == 401


def test_dashboard_redirects_to_login_when_signed_out(client):
    r = client.get("/")
    assert r.status_code == 303 and r.headers["location"] == "/login"


def test_login_then_data_is_reachable(client):
    r = client.post("/login", data={"password": "correct-horse"})
    assert r.status_code == 303
    assert client.get("/api/conversations").status_code == 200


def test_wrong_password_grants_nothing(client):
    client.post("/login", data={"password": "nope"})
    assert client.get("/api/conversations").status_code == 401


def test_forged_or_tampered_cookie_is_rejected(client):
    client.cookies.set(auth.SESSION_COOKIE, "9999999999.abc.forged")
    assert client.get("/api/conversations").status_code == 401


def test_expired_session_is_rejected(client):
    import time
    token = auth.issue_session(now=time.time() - auth.SESSION_TTL - 60)
    assert auth.valid_session(token) is False


def test_repeated_failures_are_rate_limited(client):
    for _ in range(8):
        client.post("/login", data={"password": "wrong"})
    r = client.post("/login", data={"password": "correct-horse"})
    assert r.status_code == 429   # correct password still blocked while throttled


def test_webhook_stays_open_because_meta_cannot_log_in(client):
    """It authenticates by signature instead, which we still enforce."""
    body = json.dumps({"entry": []}).encode()
    sig = "sha256=" + hmac.new(config.APP_SECRET.encode(), body, hashlib.sha256).hexdigest()
    assert client.post("/webhook", content=body,
                       headers={"X-Hub-Signature-256": sig}).status_code == 200
    assert client.post("/webhook", content=body).status_code == 403


def test_health_leaks_nothing(client):
    """Counts and timestamps are fine — they are what the nightly check reads.
    Anything identifying a customer is not."""
    body = client.get("/api/health").json()
    assert set(body) == {"ok", "errors_recent", "messages", "last_message_at"}
    assert body["ok"] is True
