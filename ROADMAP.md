# What's left to be genuinely end-to-end

Written 2026-08-10. Status today: **the engine works and is live.** A real
WhatsApp message from Hamza's phone flowed through Meta → webhook → state engine
→ authenticated dashboard on Modal. What does not yet exist is everything needed
for *somebody else's* number to connect.

**The gap in one sentence:** if a client said yes tomorrow, we could not onboard
them. Closing that is the whole list below.

---

## 1. Tech Provider verification — START FIRST, blocks everything

**Why:** Embedded Signup — the flow where a client authorises their own WhatsApp
Business number — requires Tech Provider status and App Review. Without it there
is no way for any business except us to connect.

**Why first:** it runs on Meta's clock, not ours. Everything else can be built
while it is pending, so any day it is not submitted is a wasted day.

**Steps:**
- App Dashboard → *Become a Tech Provider* (seen on the WhatsApp Business Platform page)
- Complete access verification / App Review for `whatsapp_business_management`
  and `whatsapp_business_messaging`
- Business verification is likely required at this stage (it is NOT required for
  the receive-only test setup we run today — different thing, do not confuse them)

**Blocked by:** needs business documents. Hamza has no registered entity yet —
resolve this before submitting, or the application stalls.

---

## 2. History sync on connect — BUILT 2026-08-10

**Why:** Coexistence hands over roughly 6 months of prior 1:1 conversations when
a number connects. A client who connects and immediately sees *their own* stale
quotes, with real money attached, is sold in ten seconds. A client who connects
and sees an empty screen has to wait days to feel anything.

This cannot be faked in a demo, and it is the strongest moment the product will
ever have.

**Build:** on connect, page the history endpoint, feed each message through the
existing `service.ingest` path so states and amounts derive normally. Everything
downstream already works — `apply_message` handles out-of-order and duplicates.

**Watch for:** the backfill will be thousands of messages. Batch it, commit the
Modal Volume periodically, and do not block the connect response on it.

**Built:** `webhook.parse_history_chunks` / `parse_state_sync_contacts`,
`service.sync_status`, `store.sync_phases`, `GET /api/sync`, an import banner on
the dashboard, and `tools/simulate.py --history`. 11 tests in
`tests/test_history.py`; 49 green overall.

Two things the docs do not say clearly and that cost time:
- **There is no `from_me` flag.** Direction is `from` compared against
  `value.metadata.display_phone_number`. Get this wrong and every thread names
  the wrong silent party.
- **`smb_app_state_sync` is worth having.** It carries the Business app's own
  address book, so the dashboard shows "Dana - Al Quoz warehouse" rather than a
  number. Better labels than WhatsApp profile names.

Still untested against real Meta history — that needs a Coexistence connect,
which needs #1. Verified against Meta's documented payload shape.

---

## 3. Embedded Signup — onboarding becomes a link, not a conversation

**Why:** today connecting a number is a manual Graph API dance (see
`tools/subscribe_waba.py`). A client cannot do that. They need one button.

**Build:** Facebook Login for Business configuration → JS SDK launch → exchange
the returned code for the client's WABA + phone number ID → run the two
subscriptions (app→object, WABA→app: **both**, see `SETUP.md`) → kick off history sync.

**Blocked by:** #1.

---

## 4. Multi-tenant

**Why:** one instance currently serves one client — one set of secrets, one
SQLite file, one password. Fine for the first 2-3 clients, and arguably better
(their data is physically isolated). Breaks around five.

**Build when the third client appears, not before.** Needs: tenant table keyed by
`phone_number_id`, per-tenant login, and routing on the webhook's
`metadata.phone_number_id`, which is already in every payload.

---

## 5. Follow-ups view

The staleness logic already exists (`is_overdue`). This is a filtered list, an
hour of work. Deferred until someone actually uses the product daily.

---

## 6. Operational, before a real client's data lands

- **Change the dashboard password.** `iaah2006` is short and guessable, and it
  stands between the internet and a client's customer messages.
- **Per-client credentials** rather than one shared password.
- ~~**Backups** of the Modal Volume.~~ **DONE 2026-08-10.** `modal_app.py::backup`
  runs nightly at 02:17 UTC, snapshots via SQLite's backup API (a plain file copy
  taken mid-write is corrupt), verifies the snapshot opens, keeps 30, and writes
  to a *separate* Volume `quoteradar-backups`.
  Restore: `modal volume get quoteradar-backups <file>` then
  `modal volume put quoteradar-data <file> quoteradar.db --force`.

- ⚠️ **Data loss happened once, cause not established.** On 2026-08-10 the live
  database was found empty — the real WhatsApp message verified the day before
  was gone, and a stale `quoteradar.db-journal` was sitting next to it (an
  unclean shutdown mid-transaction). Persistence was then re-tested end to end
  and works: a signed webhook survived a redeploy and a fresh container.
  Hardening added: `volume.reload()` at container start, so a container that
  mounted an old view cannot commit over newer writes. **Do not treat this as
  solved** — if it recurs, the nightly backup now bounds the loss to one day.
- **Error alerting.** If ingestion breaks, nobody finds out until a client
  notices missing conversations.
- **Data deletion path.** Meta's Platform Terms and UAE PDPL both expect one.

---

## Deliberately NOT building yet

Daily digest, trend reporting, response-time benchmarks, staff attribution
(unbuildable — no per-staff signal exists). All wait until a real user asks.

## Sequencing note

If only one thing gets done: **#1**, because it is the only item with an external
clock. If two: **#1 and #2**.
