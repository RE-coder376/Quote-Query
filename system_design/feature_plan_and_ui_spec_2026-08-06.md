# QuoteRadar — Feature plan + UI/functional spec

Date: 2026-08-06

Purpose: turn everything locked so far ([[product_system_summary]] workflow + UI skeleton, [[competitor_feature_diff_and_build_scope_2026-08-06]] scope lock, [[whatsapp_foundation_options]] + [[codebase_fit_assessment]] foundation choice) into a single feature-by-feature functional spec a build session can work from directly. One new feature is proposed at the end, flagged as a suggestion, not a locked decision.

## Data model (sketch)

- **Contact** — phone number, name (from WA profile or manual), first-seen date. Matches wacrm's contact model, reused as-is per [[codebase_fit_assessment]].
- **Conversation** — 1:1 with a Contact, holds message thread, `last_message_at`, `state` (see state machine below). Reused from wacrm's conversation object, state field repurposed for our states instead of theirs.
- **Message** — inbound/outbound, timestamp, WA message ID, delivery/read status. Reused from wacrm as-is — this is the plumbing [[codebase_fit_assessment]] confirmed is real (webhook → contact match → conversation match → message insert → realtime push).
- **Quote** — new object, not in wacrm. Fields: linked `conversation_id`, `status`, `quoted_at`, `assigned_to`, `next_follow_up_at`, `won_lost_reason` (optional, free text). This is the custom layer.
- **StaleThreshold** — one config value (default 24h) used by both the Follow-ups view and the digest (see below). No per-client customization in v1 — one global default, editable by the account owner only.

## Core features

### F1 — WhatsApp Coexistence Connection
**What:** onboarding step where the business links their existing WhatsApp Business App number via Meta Embedded Signup, per [[whatsapp_foundation_options]] (open-bsp-api as the reference implementation).
**How it functions:** OAuth-based Embedded Signup flow → Meta issues access token + WABA ID → app stores connection → historical 1:1 messages (up to 6 months, per Meta's Coexistence limits, confirmed against Zena's implementation in [[competitor_product_analysis_2026-08-06]]) sync in.
**UI:** single setup screen, one button ("Connect your WhatsApp Business number"), progress state, success confirmation. No pipeline/field configuration screen — this is the one thing every rival makes you configure something first; we don't.

### F2 — Auto-Ingest Engine
**What:** every inbound message that isn't already tied to an open Quote automatically puts its Conversation into `Unanswered` state. No manual action, no keyword detection (explicitly rejected already in [[product_system_summary]]).
**How it functions:** webhook handler (reused wacrm plumbing) → on message insert, check Conversation state → if null/Closed, set to `Unanswered` and stamp `entered_queue_at`.
**UI:** invisible — this is the backend rule that makes the Inbox and Dashboard populate without setup.

### F3 — Inbox
**What:** list of all conversations, WhatsApp-style.
**Function:** reused wacrm conversation-list component, sorted by `last_message_at` desc, filterable by state.
**UI:** each row — avatar/initials, name or number, last message preview, relative time, state pill (Unanswered / Quoted / etc.), one action button `Mark as Quote` (only shown on non-quoted rows).

### F4 — Conversation Thread (center panel)
**What:** opens a selected conversation, full message history.
**Function:** reused wacrm thread component. **Read-only for regular messages** — per the scope lock, this is not a compose/send replacement for the native WhatsApp Business App (see [[competitor_feature_diff_and_build_scope_2026-08-06]], "Shared team inbox: No — read/status only"). Staff still type replies in their own WhatsApp app; QuoteRadar shows context, not a send box.
**UI:** WhatsApp-style bubble thread, header shows contact name/number, one button `Mark as Quote` fixed at top when conversation isn't already a Quote.

### F5 — Mark as Quote
**What:** the stage-transition action. Converts a Conversation from `Unanswered`/browsing into a tracked `Quote` object.
**Function:** creates a Quote row linked to the conversation, sets `quoted_at = now()`, default status `Waiting for Customer`. This is a new custom action, not present in wacrm.
**UI:** button click → small confirm step (optional: prompt for estimated value, purely optional field, skippable) → conversation now shows in Quote Queue.

### F6 — Quote Queue
**What:** the product's core screen — only tracked quote-stage conversations, not all chats.
**Function:** filtered list of Quote objects joined to their Conversation, sorted by staleness/urgency (`next_follow_up_at` or time since last activity).
**UI:** table/list view — customer, quote status, days since quoted, last reply, assigned to, quick-action buttons (Waiting / Replied / Team Action / Won / Lost) per [[product_system_summary]] locked UI.

### F7 — Quote Detail Panel (right side)
**What:** per-quote detail when a Quote is opened.
**Function:** reads/writes the single Quote row — status, assigned_to, quoted date, next follow-up, last reply timestamp.
**UI:** fixed right panel per the already-locked layout — Status, Assigned To, Quote Sent date, Next Follow-up, Last Reply, quick-action buttons.

### F8 — Dashboard
**What:** bird's-eye stats view, the first screen after login.
**Function:** aggregate queries over Quote + Conversation states — counts, not a feed.
**UI:** stat tiles — Waiting for Customer, Customer Replied, Team Action Needed, Won This Week, Overdue Follow-ups — per [[product_system_summary]].

### F9 — Follow-ups view + staleness engine
**What:** surfaces conversations/quotes that have gone quiet past the threshold.
**Function:** a scheduled job checks `StaleThreshold` against `last_message_at` (for Unanswered conversations) and `next_follow_up_at` (for open Quotes); anything past threshold surfaces here. Same engine also powers the "Needs First Reply" tile mentioned in [[product_system_summary]].
**UI:** list view, same row shape as Inbox/Quote Queue but filtered to overdue only, sorted oldest-first.

### F10 — Closed view
**What:** archive of Won/Lost/Delayed/Closed quotes and not-a-lead conversations.
**Function:** simple filtered list, no special logic beyond state = closed-family.
**UI:** list view, read-only, searchable by contact/date.

### F11 — Quote state machine
States, locked from [[product_system_summary]]: `Unanswered` (conversation-level, pre-quote) → `Waiting for Customer` → `Customer Replied` → `Team Action Needed` → `Needs Revision` → `Won` / `Lost` / `Delayed` / `Closed`. Transitions are manual button clicks only in v1 — no automation/rules engine (explicitly excluded per the scope lock, and reinforced by the CVE noted against wacrm's own automation module in [[codebase_fit_assessment]] — one more reason not to inherit that piece).

## Suggested new feature (not yet locked — flagging because it creates real value cheaply)

### F12 — WhatsApp Daily Digest (proactive nudge)

**The problem it solves:** every feature above still requires the owner to remember to open the QuoteRadar dashboard. That's the same "forgot to check" failure mode the product exists to fix, just moved one level up — a page nobody opens has the same effect as a chat nobody reads.

**What it is:** once a day (configurable time, e.g. 8am), the system sends a short WhatsApp message *from the business's own connected number back to the owner* (or to a second designated number) summarizing what needs attention — e.g. "3 quotes waiting >48h, 2 new unanswered messages, 1 overdue follow-up." No dashboard visit required to know something needs action.

**Why it's cheap to build:** it reuses F9's staleness engine exactly — same query, different output (a WA template message instead of a UI list). No new data model, no new detection logic, just a scheduled send.

**Why it's the right kind of new feature, not scope creep:** it's a single fixed automated message, not a rules/automation builder (still consistent with "v1 stays purely time-based, zero configuration" from [[product_system_summary]]). It's non-AI (no generated text, just a templated count). And it directly strengthens the exact wedge in [[market_country_retest_2026-08-06]] — "I don't want a new inbox" — by meeting the owner inside the WhatsApp they already live in, instead of asking them to adopt a new habit of checking a web page. None of Kommo/Zena/Adjoltz frame their notification model this way; they all assume the owner lives inside their inbox UI ([[competitor_product_analysis_2026-08-06]]).

**Where it sits in build order:** after F1-F9 are working, before F10-F11 polish — it's a thin layer on top of the staleness engine, not a new subsystem.

## Build sequencing (ties to the scope-lock doc)

1. F1 Coexistence connection
2. F2 Auto-ingest + F3 Inbox (proves the core loop end-to-end)
3. F5 Mark as Quote + F6 Quote Queue + F7 Quote Detail Panel
4. F9 Follow-ups/staleness engine
5. F8 Dashboard (pure aggregation, cheap once F2-F9 exist)
6. F10 Closed view
7. F12 Daily Digest (fast-follow, reuses F9)

## What stays out (recap, full reasoning in [[competitor_feature_diff_and_build_scope_2026-08-06]])

No AI chatbot/auto-reply, no CRM fields/custom fields, no broadcast/marketing, no configurable pipelines, no automation/rules builder, no bilingual support (v1 EN only), no in-app compose/send replacing the native WhatsApp Business App.
