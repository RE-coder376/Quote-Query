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

**Phase:** Not started. No code exists yet.

**Active agent:** none

**Last updated by:** Claude Code (Aug 6, 2026) — file created

---

## Done

(nothing yet)

---

## In progress

(nothing yet)

---

## Next step

Codex to deliver the WhatsApp integration research/spec doc
(see `CODEX_HANDOFF_2026-08-05.md` §7 and §8 for the exact task and constraints).
Claude Code builds against that spec once it lands.

---

## Decisions made mid-build (not yet folded into system_design docs)

(none yet)

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
