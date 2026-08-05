# Auto-classification state model (replaces manual Mark-as-Quote gate)

Date: 2026-08-06

Purpose: revises the state model in [[product_system_summary]] and [[feature_plan_and_ui_spec_2026-08-06]] (F5/F6/F11). Supersedes "Mark as Quote" as a required manual gate.

## The flaw this fixes

The Aug 2 revision fixed the *entry* problem — every inbound message auto-enters as `Unanswered`, no manual step. But the *promotion* into a tracked Quote still required a human to notice the conversation and click `Mark as Quote`. That's the same failure mode the product exists to prevent, just moved one step later: an owner who misses a message will equally miss clicking a button about it. A manual gate anywhere in the pipeline reopens the exact hole the product is meant to close.

## The fix: classify every conversation automatically, from WhatsApp's own message signals

No human ever has to decide "is this a quote." Every conversation is always in exactly one state, computed purely from message direction + WhatsApp delivery/read ticks + elapsed time — the same `sent✓ / delivered✓✓ / read✓✓blue` signals WhatsApp already tracks, synced via Coexistence webhooks (`smb_message_echoes`/`smb_app_state_sync`, already confirmed available per [[whatsapp_foundation_options]]/[[market_country_retest_2026-08-06]]).

### States (auto-computed, no manual input)

1. **Unread** — new inbound message, staff hasn't opened it in the WhatsApp Business App yet (no read receipt synced back)
2. **Read, Reply Needed** — staff opened it (read tick fired) but no outbound reply sent yet
3. **Replied, Delivered** — business sent a reply, customer hasn't opened/read it yet
4. **Replied, Seen — Awaiting Customer** — customer has read the business's reply, no further response yet
5. **Needs Follow-up** — overlay flag, not a separate bucket: applies to states 1, 2, or 4 once they exceed `StaleThreshold` (same engine as F9). This is what surfaces on the Follow-ups view and drives the Daily Digest (F12).

A conversation moves between 1-4 automatically as messages/ticks arrive — no click required at any point. State 5 is just "how long has it sat in 1, 2, or 4."

### Mark as Quote — demoted to optional enrichment, not a gate

Everything above already tracks and surfaces every conversation regardless of whether anyone flags it. `Mark as Quote` still exists, but only as an *optional* annotation staff can add to a conversation that's worth tracking as a real deal — adds `quoted_amount` and enables Won/Lost/Delayed outcome logging for revenue reporting. Nothing depends on this action happening. A conversation nobody ever marks is still fully tracked and surfaced by states 1-5 alone.

## Answering the volume worry directly

100+ messages/day doesn't mean 100+ things to manually triage. Nobody works a flat list — they work **bucket counts**, same shape as the Dashboard tiles already locked in [[product_system_summary]]:

- "7 Unread" — clear these first, freshest failures
- "12 Read, Reply Needed" — staff already saw these, just didn't answer
- "4 Needs Follow-up" — customer went quiet after a reply, oldest first

This is inbox-zero triage, but the sorting is done automatically by the system, not manually by a person reading each one to decide where it goes. The manual work that remains is only "type the reply" (in the native WhatsApp app, unchanged) and "clear the bucket" — not "figure out what state this is in."

## What this changes in the earlier docs

- [[product_system_summary]] — "Main quote statuses" list and the workflow steps (4-6) describing `Mark as Quote` as the entry into tracking should be revised: tracking starts and continues automatically; `Mark as Quote` is optional value/outcome tracking layered on top.
- [[feature_plan_and_ui_spec_2026-08-06]] F5 — no longer "the stage-transition action," now an optional enrichment action, always available, never required.
- [[feature_plan_and_ui_spec_2026-08-06]] F6 Quote Queue — effectively merges with the Inbox/Follow-ups view: the "queue" becomes the 1-4 state buckets themselves, with an optional "Marked as Quote" filter for whoever wants to see just the flagged high-value ones.
- F11 state machine simplifies to the 5 states above; Won/Lost/Delayed remain but attach only to conversations someone chose to `Mark as Quote`, not to every conversation.

## Why this is still buildable on the existing foundation

No new technical dependency — this uses the same webhook/message-status plumbing already scoped from wacrm ([[codebase_fit_assessment]]), just reading the `status` field (sent/delivered/read) that Meta's Cloud API already sends per outbound message, plus the read-receipt sync Coexistence provides for inbound. The staleness engine (F9) is unchanged, just now applied to conversations directly instead of gated behind a manual Quote object first.
