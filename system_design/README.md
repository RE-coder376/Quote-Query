# Quote Recovery Queue System Design

This folder is the working home for product/system design decisions for Quote Recovery Queue.

Purpose:

- keep product logic in one place
- separate system design from market research
- update the design only when something becomes concrete enough to matter

Current files:

- `product_system_summary.md` — current locked product understanding
- `market_country_retest_2026-08-06.md` - US vs UK vs UAE/Gulf market retest after finding direct WhatsApp CRM competition
- `competitor_feature_diff_and_build_scope_2026-08-06.md` — feature-by-feature include/exclude scope lock vs Kommo/Zena/Adjoltz
- `competitor_product_analysis_2026-08-06.md` — product teardown of Kommo/Zena/Adjoltz (UI modules, data model, workflow mechanics)
- `mainstream_existence_check_2026-08-06.md` — check for whether the zero-config tracking mechanism already exists mainstream elsewhere
- `feature_plan_and_ui_spec_2026-08-06.md` — full feature-by-feature functional + UI spec for build, incl. suggested Daily Digest feature
- `auto_classification_state_model_2026-08-06.md` — supersedes manual Mark-as-Quote gate with fully automatic state classification from WhatsApp message ticks + time
- `value_depth_enhancements_2026-08-06.md` — ranked ideas to make the product more than message structuring (revenue-at-risk framing, one-tap nudge links, trend reporting) without breaking the CRM/AI-free scope lock
- `revenue_tracking_safeguards_2026-08-06.md` — locks the safe version of revenue-at-risk (quoted_amount only, transparent denominator) and draws a hard line against tracking actual payment (re-enters excluded accounting scope)
- `webhook_signal_verification_2026-08-06.md` — **read before building.** Verifies what Coexistence webhooks actually deliver. Kills the 5-state model (no business-read webhook; read receipts silently fail) and replaces it with a 2+1 state model resting only on message direction + time
- `digest_feasibility_verification_2026-08-06.md` — F12 Daily Digest verified: cost is negligible (~$0.86/mo/client), but per-client template approval must be handled programmatically or it breaks the zero-setup wedge
- `what_whatsapp_can_and_cannot_tell_us.md` — plain-language reference for which signals exist in each message direction; read this before designing any state, filter, or count

Rules for this folder:

- keep notes product-focused
- avoid marketing/research clutter here
- update incrementally as the product becomes clearer
- prefer simple language over technical jargon unless needed
