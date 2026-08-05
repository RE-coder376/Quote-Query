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

**Phase:** Research/spec active. No app code exists yet.

**Active agent:** none

**Last updated by:** Codex (Aug 6, 2026) - market retest report added

---

## Done

- Added `system_design/market_country_retest_2026-08-06.md`.
- Retested US vs UK vs UAE/Gulf after finding direct WhatsApp CRM competition.
- Verdict: UAE/Gulf remains best first-client market, but only with sharper "simple quote radar" positioning and lower v1 pricing than the old AED 300-500 guess.

---

## In progress

(nothing yet)

---

## Next step

Codex to deliver the WhatsApp integration research/spec doc
(see `CODEX_HANDOFF_2026-08-05.md` section 7 and section 8 for the exact task and constraints).
Claude Code builds against that spec once it lands.

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
