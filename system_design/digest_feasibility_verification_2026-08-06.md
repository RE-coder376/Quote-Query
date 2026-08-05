# F12 Daily Digest — feasibility and cost verification

Date: 2026-08-06

Purpose: [[feature_plan_and_ui_spec_2026-08-06]] proposed F12 (daily WhatsApp digest to the owner) as "cheap to build, just a scheduled send." [[webhook_signal_verification_2026-08-06]] flagged that as unverified. Verified here. **Verdict: viable, and cheaper than flagged — but with one real onboarding catch that touches the core positioning.**

## Corrected cost picture — the earlier flag overstated this

The "~30 conversations/month recurring COGS" framing used the **old** pricing model. Meta moved to **per-message pricing on July 1, 2025**; conversation-based billing is gone, and Service messages became free in Nov 2024.

Actual numbers for UAE:
- Utility template: **$0.0285/message** base (Meta direct, no BSP markup since we use Cloud API directly)
- Marketing template: $0.0816/message
- Billed **only on delivered** messages — failed sends are free

**Daily digest = 30 messages/month/client:**
- If classified Utility: **~$0.86/month/client** (≈ AED 3.14)
- If misclassified Marketing: ~$2.45/month/client (≈ AED 9)

Against AED 99-199/month pricing that is **1.5-3% of revenue at worst.** Negligible. The cost concern was worth raising but resolves clean — this does not threaten unit economics.

## The real catch: per-client template approval vs. the zero-setup promise

Business-initiated messages outside an open 24-hour customer service window require a **pre-approved Meta template**. Confirmed. And templates are approved **per-WABA** — meaning every single client needs their own digest template submitted and approved, not one template for the whole product.

This collides directly with the wedge in [[market_country_retest_2026-08-06]]: "connect your number → done, no setup." An owner-facing "wait for Meta to approve your template" step would break the one thing differentiating us from Kommo/Zena/Adjoltz, all of which require configuration ([[competitor_product_analysis_2026-08-06]]).

**Mitigation (keeps the promise intact):** templates can be created programmatically via the API. Submit the digest template automatically during onboarding, in the background. The digest simply doesn't fire until approval lands (typically minutes to 24h). The owner never sees a setup step — the rest of the product works immediately, and the digest turns itself on when ready. Degrades gracefully, no owner-facing friction.

**Residual risk:** template categorization is decided by Meta, not us. A digest with dynamic counts ("4 quotes going stale") may be auto-categorized Marketing rather than Utility — 3x the cost, still trivial. Outright rejection is possible but unlikely for a notification-shaped template; needs one real submission to confirm, which cannot be tested before a live WABA exists.

## Secondary findings

- **Sending to the owner's own number is permitted.** Templates can be sent to any WhatsApp-registered number without prior contact — the "recipient must message first" rule applies only to non-template (free-form) messages. No blocker.
- **Opt-in:** the owner is opting themselves in during onboarding; trivially satisfied with a checkbox, and they are the account holder, not a third party.
- **A free alternative exists if any of the above sours:** email digest, or a web-push notification from the dashboard — both zero-cost and zero-Meta-dependency. Worse for the wedge (the point is meeting the owner inside WhatsApp), but a working fallback rather than a dead feature.

## Verdict

F12 stays on the roadmap as originally sequenced (fast-follow after F1-F9). Cost is a non-issue. The template-approval step must be handled programmatically and invisibly — if it ever becomes an owner-facing setup task, it breaks the positioning and should be dropped in favour of the email/web-push fallback instead.

## Sources

- Meta pricing (per-message model, category definitions, CSW rules): https://developers.facebook.com/docs/whatsapp/pricing
- UAE rate card: https://sleekflow.io/blog/whatsapp-business-price-uae , https://www.greenadsglobal.com/post/whatsapp-api-pricing-uae
- Per-message pricing change + volume tiers: https://setsmart.io/blog/whatsapp-business-api-pricing
- Template-vs-free-form recipient rules: https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages/
