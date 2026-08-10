# Build State — Quote Recovery Queue

Live handoff file between Claude Code and Codex during the build.

**Rule:** whichever agent is coding right now updates this file before stopping.
Whichever agent picks up next reads this file FIRST, before touching any code —
then matches the existing code's patterns (naming, structure, error handling)
rather than writing in its own style. The codebase is shared across handoffs.

This is a sequential handoff, not parallel work: one agent codes at a time.
Claude Code is the default builder. Codex takes over only when Claude's usage
limit runs out mid-task, continuing the same task from where Claude stopped.

---

## Current status

**Phase:** LIVE on Modal. History sync built. 49 tests green.

**Active agent:** Claude Code

**Last updated by:** Claude Code (Aug 10, 2026) — Coexistence history sync +
nightly backups + volume-reload hardening

### Aug 10, 2026 — Claude Code

Done:
- **History sync (ROADMAP #2)**: `parse_history_chunks`, `parse_state_sync_contacts`,
  `sync_phases` table, `service.sync_status`, `GET /api/sync`, dashboard import
  banner, `tools/simulate.py --history`. 11 new tests.
- **Nightly backup** to a separate Modal Volume (`modal_app.py::backup`, 02:17 UTC,
  30 kept, snapshot verified before pruning).
- **`volume.reload()` on container start** — a stale mount committing over newer
  writes is the most plausible cause of the data loss below.

Gotchas:
- History has **no `from_me`**; direction = `from` vs `metadata.display_phone_number`.
- Modal Volume needs an explicit `reload()`; the backup job silently snapshotted
  an empty database until it had one.
- `modal deploy` from Git Bash on Windows dies on the ✓ glyph — prefix
  `PYTHONIOENCODING=utf-8 PYTHONUTF8=1`.

⚠️ **The live DB was found empty on Aug 10** — the real message verified Aug 9 is
gone, with a stale `-journal` beside it. Re-tested: writes now survive redeploy
and container recycling. Cause unproven; backups now bound the loss.

Also done Aug 10 (second pass):
- **Tenant guard**: `QR_PHONE_NUMBER_ID=1255446447652185` set live. Deliveries
  for any other number are dropped before ingest. Verified against the live app.
- **Client accounts**: one-time claim link → client sets their own password →
  number + password login. `account` + `setup_codes` tables, PBKDF2-SHA256,
  codes hashed and single-use. `modal run modal_app.py::setup_link [--reset]`.
- Dashboard password changed from `iaah2006` to `moral` (owner override).
- 71 tests green.

⚠️ Git Bash mangles POSIX-looking env values: `QR_DB_PATH=/tmp/x.db` reaches
Python as `C:\Users\...\Temp\x.db` from bash but `C:\tmp\x.db` from a Python
literal. Two processes silently used different databases. Use Windows paths.

Also done Aug 10 (third pass):
- **Data deletion**: `DELETE /api/conversations/{wa_id}` + a rail control behind
  a confirm; `modal run modal_app.py::erase --confirm ERASE` for a full wipe
  that keeps the login. Backups still hold copies for 30 days — tell clients.
- **Error alerting**: `ingest_errors` table, counts on `/api/health`, nightly
  `health_check` cron that raises so Modal emails. Also catches total silence.
- **`node --check` gate in `tools/build_dashboard.py`.** A `\n` typed into the
  JS templates (which are Python strings) becomes a real newline, breaks the
  literal and silently kills the entire dashboard script — the page renders and
  never loads data. Python tests cannot see it. Caught in a browser, not by the
  suite; now gated at build time and in `tests/test_ops.py`.
- 80 tests green.

Next step:
- Tech Provider verification (Hamza — needs a Meta login and, likely, a
  registered entity). Blocks Embedded Signup, which blocks every real client.
- Embedded Signup is the only build item left, and it cannot be exercised
  until Tech Provider lands.

### Working now

```
app/models.py    Contact / Message / Conversation, 3 states, Outcome
app/state.py     engine: direction + elapsed time only
app/webhook.py   Meta payload parsing + X-Hub-Signature-256 verification
app/store.py     SQLite (stdlib), dedupes on wa_message_id
app/service.py   ingest + read models; enforces the copy rules server-side
app/main.py      FastAPI: GET/POST /webhook, read API, dashboard.  NO send endpoint.
app/static/      live dashboard, built from the demo's stylesheet
tools/simulate.py       replays real-shaped Meta payloads (no Meta account needed)
tools/build_dashboard.py rebuilds static/index.html from demo/quoteradar_dashboard_aed.html
tests/           26 tests
```

Run: `uvicorn app.main:app --reload` then `python -m tools.simulate --retry-test`

Verified end-to-end: signed webhook → store → state engine → dashboard.
`applied: 4` on first delivery, `0` on replay (Meta retries are idempotent).

### Blocked on Hamza, not on code

**Meta business verification has not been started.** Everything above is
exercisable with `tools/simulate.py`, but going live needs a Meta app, a WABA and
business verification — external clock, free, and the long pole. Nothing else
gates a first client.

### Integration decision — CLOSED, do not reopen

Researched 2026-08-09. **There is no certified way to support normal/consumer
WhatsApp.** Three options exist and only two are safe:

| Option | Status |
|---|---|
| Cloud API (Meta-hosted) | Official, ToS-compliant, ban-proof. Needs WABA + business verification. |
| Coexistence (Business app + API on one number) | Official. **Requires the WhatsApp Business app** — consumer WhatsApp has no path. |
| Baileys / whatsapp-web.js / WAHA / Evolution API | **ToS violation. 68% of SMBs using these report a ban within 12 months; typically detected in 2-8 weeks.** Permanently excluded. |

So onboarding *must* start with the client on the WhatsApp Business app. If a
prospect is on consumer WhatsApp, migration (free, ~5 min, keeps number + history)
is step one. There is no workaround and we are not looking for one.

Also noted: **Jan 2026 Meta banned open-ended AI assistant bots** on the WhatsApp
Business Platform; only structured bots are allowed. QuoteRadar is read-only and
sends nothing, so it is unaffected — and this further validates the no-AI stance.

---

## Done

- Added `system_design/market_country_retest_2026-08-06.md`.
- Retested US vs UK vs UAE/Gulf after finding direct WhatsApp CRM competition.
- Verdict: UAE/Gulf remains best first-client market, but only with sharper "simple quote radar" positioning and lower v1 pricing than the old AED 300-500 guess.
- Added `outreach/gulf_fitout_targets_2026-08-06.md` with 15 vetted UAE interior fit-out / joinery / kitchen renovation candidates that visibly use WhatsApp as an enquiry or quote channel.
- Added `outreach/gulf_fitout_validation_wame_2026-08-06.md` with prefilled validation-question wa.me links for the 15 Gulf targets. No email/send action was performed.

---

## In progress

(nothing yet)

---

## Next step

Codex to deliver the WhatsApp integration research/spec doc
(see `CODEX_HANDOFF_2026-08-05.md` section 7 and section 8 for the exact task and constraints).
Claude Code builds against that spec once it lands.

Hamza can use `outreach/gulf_fitout_targets_2026-08-06.md` for the next validation-question step once the validation question itself is finalized.
Hamza can use `outreach/gulf_fitout_validation_wame_2026-08-06.md` to manually open/send the validation messages after checking each link.

---

## Decisions made mid-build (not yet folded into system_design docs)

- Do not position v1 as a generic WhatsApp CRM; Kommo/Zena/etc. already cover that and are cheap.
- Drop the old AED 300-500/month v1 price assumption. First-client pricing should likely be AED 99-199/month in UAE/Gulf.
- US is not recommended for WhatsApp-first v1 because contractor quote requests mostly come through phone/SMS/email/forms, not WhatsApp.
- UK is possible but mixed-channel; UAE/Gulf remains the best fit for the current WhatsApp Coexistence-first product.

---

## Template for each update

```
### <date> — <agent name>

Done:
- ...

In progress:
- ...

Next step:
- ...

Decisions / gotchas:
- ...
```
