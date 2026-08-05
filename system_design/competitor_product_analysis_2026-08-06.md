# Competitor product analysis (product teardown, not market/pricing)

Date: 2026-08-06

Purpose: [[market_country_retest_2026-08-06]] and [[competitor_feature_diff_and_build_scope_2026-08-06]] compare pricing and market fit. This doc is different — it inspects what Kommo, Zena, and Adjoltz actually contain as products: their UI modules, data model, and workflow mechanics, gathered directly from their product/docs pages, so the build scope is grounded in what they really do, not just what they charge.

## Kommo — product teardown

**UI modules:** Unified chat inbox, Kanban-style pipeline board, dashboard/analytics, contact records, Salesbot (visual no-code bot builder), AI Booking Agent, Kommo AI/Copilot, WhatsApp broadcasting, social comment management.

**WhatsApp connection:** three paths — new number, reuse an existing WhatsApp Business App number via Coexistence, or migrate from another provider.

**Coexistence mechanics:** native app and Kommo both stay active on one number simultaneously; a 24-hour customer-service-window countdown timer shows in the UI; incompatible with Marketing Messages Lite API; numbers already in Meta Inbox must be removed from Meta's Business Portfolio first.

**Message tooling:** Meta-approved templates (text, carousel, flows), list messages (only inside Salesbot), bulk template sends, assignment rules triggered by reply or pipeline stage.

**Core object:** a *deal/lead* moving through a configurable pipeline. The pipeline stages are generic — the business designs them.

## Zena — product teardown

**UI modules:** Team Inbox (AI-suggested replies + collision detection so two agents don't answer the same chat), Chatflow Builder (node-based, connects inbound messages → KB lookup → branch → reply, no code), Broadcasting Console, CRM & Contacts (fielded: name, intent, budget, slot, source), Analytics Dashboard.

**AI chatbot mechanics:** grounded only in uploaded documents (menu, pricelist, booking rules, FAQ file) — not open internet. Explicitly designed to say "I don't know" rather than fabricate an answer. Auto-detects and replies in the customer's language across Arabic (Gulf dialect, MSA, Arabizi), English, Hindi, Urdu, Tagalog, Bengali, without manual language config.

**Coexistence mechanics:** Meta Embedded Signup, OAuth-based, ~5 minutes, no trade license required. Syncs up to 6 months of existing 1:1 chat history; group chats stay phone-only (Meta restriction, not Zena's choice).

**Extras:** role-based access (Superadmin/Admin/Agent/Viewer), audit logs (Business/Enterprise tier), webhooks + full REST API (Business tier), Google Sheets automation trigger, Meta Conversions API integration, round-robin assignment, "Owner AI Companion" — a personal AI assistant that runs on the owner's own WhatsApp number.

**Core object:** a *contact/lead* with CRM fields (intent, budget, slot). Still CRM-shaped, just with an AI layer on top.

## Adjoltz — product teardown

**UI modules:** Shared Inbox, Broadcast Builder, Chatbot & Flows, built-in CRM (segmented by customer spend), Catalog & Commerce (in-chat product browsing, cart, checkout), Analytics Dashboard, Mobile App (Surge tier and up).

**Setup model:** fully managed/done-for-you — Adjoltz's team handles Meta verification, template approval, and flow configuration. The business owner doesn't touch Meta Business Manager directly.

**Feature gating by tier:** Spark (AED 199) = API setup + 1 inbox + basic reporting only. Chatbot/flows/automation only unlock at Surge (AED 499). CRM integration, catalog/commerce, and A/B testing only unlock at Supercharge (AED 899).

**Dashboard framing:** shows 30-day revenue totals, month-over-month % change, daily delivery-rate charting — a *commerce/campaign-performance* dashboard, not a "what am I forgetting" dashboard.

**Core object:** a broadcast/campaign, or a raw chat thread. Commerce-and-marketing shaped, not quote-lifecycle shaped.

## The real gap (product-level, not pricing-level)

- **None of the three has "a quote" as their core data object.** Kommo's object is a generic configurable deal. Zena's is a CRM contact. Adjoltz's is a campaign/thread. QuoteRadar's object — a quote moving through Unanswered → Quoted → Waiting/Replied/Team-Action → Won/Lost/Delayed — doesn't exist natively in any of them.
- **None auto-enters every inbound conversation into a tracked state on arrival with zero configuration.** Kommo needs a pipeline designed first. Zena needs KB documents uploaded before the AI is useful. Adjoltz needs a managed onboarding setup call. All three require a setup decision before the product shows anything useful — QuoteRadar's "connect number → see what's unanswered" with no configuration step is a genuine product gap, not just a messaging angle.
- **AI-generated replies are core to Kommo's and Zena's value prop**, not an add-on. This confirms QuoteRadar isn't "Kommo/Zena minus AI" — it's a different category (visibility/tracking tool vs. conversation-automation tool). Worth stating this plainly in any future pitch: not a cheaper AI chatbot, a non-AI tracking layer.

## Build implications

- Both open-source foundations already picked ([[whatsapp_foundation_options]]: wacrm, open-bsp-api) are shaped like **Kommo's model** (generic pipeline/deal object). Confirms the scope-lock decision in [[competitor_feature_diff_and_build_scope_2026-08-06]]: fork the Coexistence/inbox plumbing only — do not carry over wacrm's pipeline/deal data model. The quote object needs to be built from scratch to match the fixed-state workflow in [[product_system_summary]], since none of the three rivals' underlying data model fits it.
- Zena's "say I don't know, never fabricate" design is worth copying in spirit for any future AI feature — not relevant to v1 since v1 has no AI, but noted for whenever that door reopens.
- Adjoltz's tier-gating shape (bare connection cheap, automation/integration paywalled higher) is a reusable pricing pattern regardless of feature set — plain connection + tracking at the AED 99-199 v1 price, any future automation becomes the upsell tier.

## Sources

- https://www.kommo.com/
- https://support.kommo.com/docs/tr/whatsapp-business-overview
- https://zena.fictoralabs.ae/
- https://adjoltz.com/
