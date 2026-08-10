# Meta setup — what Hamza has to do

Researched 2026-08-09. **Business verification is NOT required to start.**

Unverified accounts can respond to *unlimited* customer-initiated conversations
and register up to 2 phone numbers. QuoteRadar only receives — it never sends —
so nothing about the unverified tier limits us. Verification matters later, for
business-initiated volume we deliberately don't do.

Typical end-to-end setup is 3–5 days, and the only slow part (verification) is
one we can skip for now.

---

## The 5 things only you can do

### 1. Meta developer account — free, 5 minutes
https://developers.facebook.com → log in with a Facebook account → *My Apps*.
Use a Facebook account you don't mind being tied to this.

### 2. Create an app — 5 minutes
*Create App* → type **Business** → name it (e.g. "QuoteRadar").
When asked for a Business Account, take the **Test Business Account** option —
that avoids needing a verified Facebook Business Account at this stage.

### 3. Add the WhatsApp product — 2 minutes
In the app dashboard → *Add product* → **WhatsApp** → *Set up*.
Meta gives you a free **test phone number** immediately. That's enough to prove
the whole loop before any client is involved.

### 4. Copy two secrets into `.env`
- **App Secret** — app dashboard → *App settings → Basic → App Secret*
- **Verify token** — you invent this one; any random string, must match `.env`

```
WA_APP_SECRET=<paste from Meta>
WA_VERIFY_TOKEN=<any random string you choose>
QR_CURRENCY=AED
QR_BUSINESS_NAME=Client business name
```

### 5. Point Meta's webhook at the running app
Meta needs a **public HTTPS URL**. Locally, tunnel it:

```
cloudflared tunnel --url http://localhost:8000
```

Then in the app dashboard → *WhatsApp → Configuration → Webhook*:
- **Callback URL:** `https://<tunnel-url>/webhook`
- **Verify token:** the same string from `.env`
- **Subscribe to fields:** `messages`, `message_echoes` (and `smb_app_state_sync`
  if offered — it syncs contacts, not read state)

Meta calls `GET /webhook` once to verify. The app answers it automatically.

---

## Then: a real client's number (Coexistence)

For a client to connect **their existing WhatsApp Business app number**, they go
through Meta's **Embedded Signup** flow — they authorise, and history (up to
~6 months of 1:1 chats) syncs in.

Requirements, non-negotiable:
- The number must be on the **WhatsApp Business app**, not consumer WhatsApp.
- Consumer → Business migration is free, ~5 minutes, keeps number and history.
- There is no path for consumer WhatsApp. Do not look for one.

---

## What is already done (no action needed)

- Webhook receiver, signature verification, ingest, state engine, dashboard.
- `python -m tools.simulate` replays real-shaped payloads, so the app can be
  demoed and tested **before** any Meta account exists.
- 26 tests covering retries, out-of-order delivery, reopen-on-inbound, and the
  rule that read receipts never drive a state.

## Hosting (later, when a client is live)

Needs a public HTTPS host that stays up. Zero-budget options: Oracle Cloud free
VM, Render/Fly free tier, or Modal (already used for the chatbot). A tunnel is
fine for demos but dies when the laptop sleeps.
