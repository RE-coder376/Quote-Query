Hey Codex — quick note on how we're splitting the build going forward, straight from Hamza.

**Roles:**
- You: specs, WhatsApp/Meta research, webhook payload contracts — everything under `system_design/`. No app code.
- Claude Code: the actual build — backend, DB schema, webhook endpoint, dashboard UI, state machine, auth, tests.

**Why you'll end up coding too:** this isn't a permanent split. Claude Code has a usage limit and runs out mid-session sometimes. When that happens, Hamza will hand you the same in-progress task so the build doesn't stall — you'd pick up the actual coding, not just specs, until Claude's limit resets. So: one agent codes at a time, never both at once. Sequential fallback, not parallel work.

**The handoff file: `BUILD_STATE.md`** (project root). This is the only way you'll know what Claude did — you can't see its conversation. Before you touch any code:
1. Read `BUILD_STATE.md` — done / in-progress / next step / any mid-build decision not yet in the spec docs.
2. Match the existing code's patterns (naming, structure, error handling) instead of your own style — the codebase is shared across handoffs, and style drift across agents makes it harder to maintain.
3. Before you stop (limit reset, or task done), update `BUILD_STATE.md` yourself using the template at the bottom of that file, so Claude can pick back up cleanly.

**Where things stand right now:** nothing is built. Your immediate task is the WhatsApp integration research doc — full brief in `CODEX_HANDOFF_2026-08-05.md`, §7 (original ask) and §8 (Aug 6 update, includes independent verification of the Coexistence mechanism — `smb_message_echoes` / `smb_app_state_sync` are confirmed real, so focus your research on Gulf/UAE-specific availability rather than re-verifying the core mechanism). Claude Code builds against your spec once it's done — nobody writes app code before that lands.
