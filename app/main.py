"""FastAPI app: Meta webhook in, read-only dashboard out.

There is no send endpoint, deliberately. Staff keep replying in the WhatsApp
Business app; QuoteRadar only observes. That removes template approval, the
24-hour window, per-message fees, and any chance of the product saying something
wrong to a real client.
"""
from __future__ import annotations

from datetime import datetime, timezone
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


LOGIN_PAGE = """<!doctype html><html><head><meta charset="utf-8">
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
</style></head><body>
<form method="post" action="/login">
  <h1>QuoteRadar</h1>
  <p>Sign in to see your quote queue.</p>
  __ERROR__
  <input type="password" name="password" placeholder="Password" autofocus required>
  <button type="submit">Sign in</button>
</form></body></html>"""


@app.get("/login", response_class=HTMLResponse)
def login_page(bad: int = 0):
    err = '<p class="err">Wrong password.</p>' if bad else ""
    return LOGIN_PAGE.replace("__ERROR__", err)


@app.post("/login")
def login(request: Request, password: str = Form(...)):
    ip = request.client.host if request.client else "unknown"

    if auth.rate_limited(ip):
        raise HTTPException(status_code=429, detail="too many attempts, wait 15 minutes")

    if not auth.password_ok(password):
        auth.record_failure(ip)
        return RedirectResponse("/login?bad=1", status_code=303)

    auth.clear_failures(ip)
    resp = RedirectResponse("/", status_code=303)
    resp.set_cookie(auth.SESSION_COOKIE, auth.issue_session(),
                    httponly=True, samesite="lax",
                    secure=config.SECURE_COOKIES, max_age=auth.SESSION_TTL)
    return resp


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


@app.get("/api/health")
def health():
    """Unauthenticated on purpose (uptime checks), so it leaks nothing."""
    return {"ok": True}


# ---------- dashboard ----------

@app.get("/")
def dashboard(request: Request):
    if not auth.valid_session(request.cookies.get(auth.SESSION_COOKIE)):
        return RedirectResponse("/login", status_code=303)
    index = STATIC / "index.html"
    if not index.exists():
        return JSONResponse({"detail": "dashboard not built yet"}, status_code=404)
    return FileResponse(index)
