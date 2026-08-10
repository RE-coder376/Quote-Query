"""FastAPI app: Meta webhook in, read-only dashboard out.

There is no send endpoint, deliberately. Staff keep replying in the WhatsApp
Business app; QuoteRadar only observes. That removes template approval, the
24-hour window, per-message fees, and any chance of the product saying something
wrong to a real client.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from html import escape as html_escape
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Form, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel

from . import auth, config, service
from .models import Outcome
from .store import Store
from .webhook import verify_signature

STATIC = Path(__file__).parent / "static"

app = FastAPI(title="QuoteRadar", docs_url=None, redoc_url=None, openapi_url="/api/openapi.json")
store = Store(config.DB_PATH)


def now() -> datetime:
    return datetime.now(timezone.utc)


def require_auth(request: Request) -> None:
    """Guard for anything that exposes customer data."""
    if not auth.valid_session(request.cookies.get(auth.SESSION_COOKIE)):
        raise HTTPException(status_code=401, detail="not signed in")


PAGE = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>QuoteRadar</title>
<style>
 body{margin:0;min-height:100vh;display:grid;place-items:center;background:#EEF1F2;
      font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:#141D22}
 @media(prefers-color-scheme:dark){body{background:#121A1E;color:#E6EDF0}
   form{background:#1A2429!important;border-color:#2D3B42!important}
   input{background:#121A1E!important;color:#E6EDF0!important;border-color:#2D3B42!important}}
 form{background:#fff;border:1px solid #D3DBDE;border-radius:8px;padding:1.75rem;
      width:min(360px,92vw);display:flex;flex-direction:column;gap:.75rem}
 h1{margin:0 0 .25rem;font-size:1.15rem;letter-spacing:-.015em}
 p{margin:0;font-size:.82rem;color:#566871}
 input{font:inherit;padding:.65rem .7rem;border:1px solid #D3DBDE;border-radius:5px}
 button{font:inherit;font-weight:600;padding:.7rem;border:0;border-radius:5px;
        background:#2C5F7C;color:#fff;cursor:pointer}
 .err{color:#B4402C;font-size:.82rem}
 .ok{color:#2C5F7C;font-size:.82rem}
</style></head><body>
__FORM__
</body></html>"""

LOGIN_FORM = """<form method="post" action="/login">
  <h1>QuoteRadar</h1>
  <p>Sign in to see your quote queue.</p>
  __ERROR__
  <input name="number" placeholder="Your WhatsApp number" autocomplete="username"
         inputmode="tel" autofocus required>
  <input type="password" name="password" placeholder="Password"
         autocomplete="current-password" required>
  <button type="submit">Sign in</button>
</form>"""

SETUP_FORM = """<form method="post" action="/setup">
  <h1>Set up QuoteRadar</h1>
  <p>Choose your own password. Nobody else ever sees it — not even us.</p>
  __ERROR__
  <input type="hidden" name="code" value="__CODE__">
  <input name="number" placeholder="Your WhatsApp Business number"
         autocomplete="username" inputmode="tel" autofocus required>
  <input type="password" name="password" placeholder="Choose a password"
         autocomplete="new-password" minlength="8" required>
  <input type="password" name="confirm" placeholder="Confirm password"
         autocomplete="new-password" minlength="8" required>
  <button type="submit">Create account</button>
</form>"""

DEAD_LINK = """<form>
  <h1>This link has expired</h1>
  <p>Setup links work once. Ask for a new one, or sign in if your account
     already exists.</p>
</form>"""


def _page(form: str, error: str = "") -> str:
    return PAGE.replace("__FORM__", form).replace(
        "__ERROR__", f'<p class="err">{error}</p>' if error else "")


def _sign_in(request: Request) -> RedirectResponse:
    resp = RedirectResponse("/", status_code=303)
    resp.set_cookie(auth.SESSION_COOKIE, auth.issue_session(),
                    httponly=True, samesite="lax",
                    secure=config.SECURE_COOKIES, max_age=auth.SESSION_TTL)
    return resp


@app.get("/login", response_class=HTMLResponse)
def login_page(bad: int = 0):
    return _page(LOGIN_FORM, "Wrong number or password." if bad else "")


@app.post("/login")
def login(request: Request, password: str = Form(...), number: str = Form("")):
    ip = request.client.host if request.client else "unknown"

    if auth.rate_limited(ip):
        raise HTTPException(status_code=429, detail="too many attempts, wait 15 minutes")

    account = store.account()
    supplied = auth.normalise_number(number)

    # The client's own credentials, plus an owner override that keeps support
    # access working if they forget their password.
    ok = auth.password_ok(password) or (
        account is not None
        and supplied == account["wa_number"]
        and auth.verify_password(password, account["password_hash"])
    )

    if not ok:
        auth.record_failure(ip)
        return RedirectResponse("/login?bad=1", status_code=303)

    auth.clear_failures(ip)
    return _sign_in(request)


# ---------- first-time setup ----------

@app.get("/setup", response_class=HTMLResponse)
def setup_page(code: str = ""):
    """Reached once, by private link. Everything after this is /login."""
    if store.account() is not None:
        return RedirectResponse("/login", status_code=303)
    if not code or not store.setup_code_valid(auth.hash_setup_code(code)):
        return _page(DEAD_LINK)
    return _page(SETUP_FORM.replace("__CODE__", html_escape(code)))


@app.post("/setup")
def setup(request: Request, code: str = Form(...), number: str = Form(...),
          password: str = Form(...), confirm: str = Form(...)):
    ip = request.client.host if request.client else "unknown"
    if auth.rate_limited(ip):
        raise HTTPException(status_code=429, detail="too many attempts, wait 15 minutes")

    if store.account() is not None:
        return RedirectResponse("/login", status_code=303)

    form = SETUP_FORM.replace("__CODE__", html_escape(code))

    if not store.setup_code_valid(auth.hash_setup_code(code)):
        auth.record_failure(ip)
        return HTMLResponse(_page(DEAD_LINK))

    wa_number = auth.normalise_number(number)
    if len(wa_number) < 8:
        return HTMLResponse(_page(form, "That does not look like a phone number."))
    if password != confirm:
        return HTMLResponse(_page(form, "The two passwords do not match."))
    if len(password) < auth.MIN_PASSWORD:
        return HTMLResponse(_page(
            form, f"Use at least {auth.MIN_PASSWORD} characters."))

    # Burn first: if two people open the same link at once, exactly one wins.
    if not store.burn_setup_code(auth.hash_setup_code(code)):
        return HTMLResponse(_page(DEAD_LINK))

    store.create_account(wa_number, auth.hash_password(password))
    return _sign_in(request)


@app.post("/logout")
def logout():
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie(auth.SESSION_COOKIE)
    return resp


# ---------- Meta webhook ----------

@app.get("/webhook")
def verify(
    mode: str = Query(alias="hub.mode", default=""),
    token: str = Query(alias="hub.verify_token", default=""),
    challenge: str = Query(alias="hub.challenge", default=""),
):
    """Meta's one-time handshake. Echo the challenge only if the token matches."""
    if mode == "subscribe" and token == config.VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="verification failed")


@app.post("/webhook")
async def receive(request: Request):
    """Every delivery is signature-checked before it is trusted.

    Always returns 200 once authenticated: a non-200 makes Meta retry the whole
    batch, and a malformed node should not cause a storm of redeliveries.
    """
    raw = await request.body()
    if not verify_signature(config.APP_SECRET, raw,
                            request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(status_code=403, detail="bad signature")

    try:
        applied = service.ingest(store, await request.json())
    except Exception as exc:  # noqa: BLE001 - never let one bad payload cause retries
        # Answering 200 is what stops a retry storm, and it is also what makes a
        # parsing bug invisible. Record it so the nightly check can shout.
        try:
            store.record_error(type(exc).__name__, str(exc))
        except Exception:  # noqa: BLE001 - a broken database must not 500 the webhook
            pass
        return JSONResponse({"status": "error", "detail": str(exc)}, status_code=200)

    return {"status": "ok", "applied": applied}


# ---------- read API ----------

@app.get("/api/conversations", dependencies=[Depends(require_auth)])
def conversations(filter: str = "all"):
    t = now()
    views = [service.conversation_view(store, c, t) for c in store.all_conversations()]

    if filter == "closed":
        views = [v for v in views if not v["is_open"]]
    else:
        views = [v for v in views if v["is_open"]]
        if filter == "overdue":
            views = [v for v in views if v["overdue"]]
        elif filter == "awaiting_reply":
            views = [v for v in views if v["state"] == "awaiting_reply"]
        elif filter == "awaiting_customer":
            views = [v for v in views if v["state"] == "awaiting_customer"]

    # Most urgent first: overdue-and-ours, then longest silence.
    views.sort(key=lambda v: (
        not (v["overdue"] and v["state"] == "awaiting_reply"),
        -v["hours_silent"],
    ))
    return {"summary": service.summary(store, t), "conversations": views,
            "sync": service.sync_status(store)}


@app.get("/api/sync", dependencies=[Depends(require_auth)])
def sync():
    """History backfill progress. Polled on connect, when the queue is empty and
    the client would otherwise be looking at a blank screen."""
    return service.sync_status(store)


@app.get("/api/conversations/{wa_id}", dependencies=[Depends(require_auth)])
def conversation(wa_id: str):
    conv = store.get_conversation(wa_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="unknown conversation")
    return service.conversation_view(store, conv, now())


class AmountIn(BaseModel):
    amount: Optional[int] = None


@app.post("/api/conversations/{wa_id}/amount", dependencies=[Depends(require_auth)])
def set_amount(wa_id: str, body: AmountIn):
    try:
        service.set_amount(store, wa_id, body.amount)
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown conversation")
    return service.conversation_view(store, store.get_conversation(wa_id), now())


class OutcomeIn(BaseModel):
    outcome: Optional[str] = None  # won | lost | no_deal | null to reopen


@app.post("/api/conversations/{wa_id}/outcome", dependencies=[Depends(require_auth)])
def set_outcome(wa_id: str, body: OutcomeIn):
    try:
        value = Outcome(body.outcome) if body.outcome else None
    except ValueError:
        raise HTTPException(status_code=400, detail="unknown outcome")
    try:
        service.set_outcome(store, wa_id, value)
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown conversation")
    return service.conversation_view(store, store.get_conversation(wa_id), now())


@app.delete("/api/conversations/{wa_id}", dependencies=[Depends(require_auth)])
def delete_conversation(wa_id: str):
    """Erase one customer entirely — messages, state, name.

    Real deletion, not archiving: Meta's Platform Terms and the UAE PDPL both
    expect it, and a customer who asks to be forgotten is not asking to be
    hidden. Note it can reappear if they message again, and that copies persist
    in nightly backups for up to 30 days.
    """
    if store.get_conversation(wa_id) is None:
        raise HTTPException(status_code=404, detail="unknown conversation")
    return {"deleted": store.delete_contact(wa_id)}


@app.get("/api/health")
def health():
    """Unauthenticated on purpose (uptime checks), so it leaks nothing.

    Counts and timestamps only — no names, no numbers, no message text. The
    error count is what the nightly check reads.
    """
    since = now() - timedelta(hours=config.ALERT_WINDOW_HOURS)
    last = store.last_message_at()
    return {
        "ok": True,
        "errors_recent": len(store.errors_since(since)),
        "messages": store.message_count(),
        "last_message_at": last.isoformat() if last else None,
    }


# ---------- dashboard ----------

@app.get("/")
def dashboard(request: Request):
    if not auth.valid_session(request.cookies.get(auth.SESSION_COOKIE)):
        return RedirectResponse("/login", status_code=303)
    index = STATIC / "index.html"
    if not index.exists():
        return JSONResponse({"detail": "dashboard not built yet"}, status_code=404)
    return FileResponse(index)
