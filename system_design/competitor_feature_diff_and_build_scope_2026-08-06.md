# Competitor feature diff + build scope lock

Date: 2026-08-06

Purpose: turn the market retest into a build-ready scope guardrail. Every row below is a deliberate include/exclude decision, so future build sessions don't silently drift into rebuilding Kommo/Zena.

## Feature matrix — Gulf rivals vs QuoteRadar v1

| Feature | Kommo | Zena | Adjoltz | QuoteRadar v1 | Reason |
|---|---|---|---|---|---|
| WhatsApp Coexistence (keep using WA Business App) | Yes | Yes | Yes (managed) | **Yes** | Table stakes — no product here without it |
| Shared team inbox (full WhatsApp replacement UI) | Yes | Yes | Yes | **No — read/status only** | This is the exact thing our target owner said they don't want to migrate into |
| Full CRM (deals, custom fields, contact timeline) | Yes | Yes | Partial | **No** | Out of scope — we track quotes, not relationships |
| AI chatbot / auto-reply | No (add-on) | Yes | Higher tier | **No** | Different product category; also our target owner replies personally, doesn't want to automate the reply |
| Broadcast / marketing campaigns | No | Yes | Yes (core) | **No** | Compliance overhead (opt-in rules) + not the pain we're solving |
| Sales pipelines (generic, configurable) | Yes | Yes | No | **No — fixed quote states only** | Configurable pipelines require onboarding effort; our states are fixed and match the workflow exactly, zero setup |
| Automation / triggers builder | Yes (Advanced) | Yes | Higher tier | **No (v1)** | Time-based staleness detection only, see [[product_system_summary]] — no rules engine |
| Time-based unanswered/stale detection | Missed-message detection (Advanced tier only) | Not a headline feature | Not a headline feature | **Yes — core, free tier equivalent** | This is the wedge. Nobody below gives this as the *primary* view for free/cheap |
| Quote-specific tracking (won/lost/delayed) | No (generic deal stages) | No | No (reporting only) | **Yes — core** | No rival tracks "quote sent → what happened" as its main object |
| Bilingual AR/EN | Partial | Yes | Yes | **No (v1, EN only)** | Real gap vs Zena/Adjoltz — flagged as a fast-follow if v1 validates |
| Setup complexity for the owner | Medium (CRM concepts) | Low-medium | Low (managed) | **Target: lowest** | Connect number → done. No fields to configure, no pipeline to design |
| Price (1-3 user) | AED 55-165/mo | AED 199-249/mo | AED 199-499/mo | **AED 99-199/mo target** | Below Zena/Adjoltz, above Kommo per-seat — priced for "narrower but zero setup," not "cheaper CRM" |

## The one sentence this matrix has to keep proving

"I don't want a CRM, chatbot, or shared inbox — I want one page that tells me which WhatsApp quotes I'm forgetting."

Every "No" row above exists because the feature would blur that sentence. If a build decision later adds one of the "No" rows back in, it should be a deliberate scope change with a reason written down here, not scope creep.

## What this means for build order

Build in the order the matrix implies risk, cheapest-to-validate first:

1. **Coexistence connection** (open-bsp-api reference — see [[whatsapp_foundation_options]]) — proves the legal/technical foundation works at all
2. **Auto-ingest to `Unanswered` + staleness surfacing** — this is the only feature no rival leads with; if this alone doesn't land in the pain-point conversations, nothing else in the matrix matters
3. **Quote Queue + fixed states** (Mark as Quote → Won/Lost/Delayed) — second-order, only needed once step 2 is proven wanted
4. Everything in the "No" column stays out of v1 by default — do not pull from wacrm's CRM/pipeline/broadcast modules even though they're already coded, unless a specific validated demand reopens that row

## Open-source foundation update

Adds to [[whatsapp_foundation_options]] (not a replacement — that file's wacrm recommendation stands for the inbox/CRM shell):

**open-bsp-api** (`github.com/matiasbattocchia/open-bsp-api`) — implements WhatsApp Coexistence via Embedded Signup directly, multi-tenant. More narrowly scoped to exactly the Coexistence connection step (item 1 above) than wacrm, which is a fuller CRM shell. Read this one specifically for the Embedded Signup + `smb_message_echoes`/`smb_app_state_sync` webhook handling.

**Repos to avoid copying the WhatsApp layer from:** Evolution API, OpenWA, whatomate — these support/emulate the unofficial WhatsApp Web protocol (Baileys-style) alongside or instead of official Cloud API. Confirms the zero-risk rule already locked: official Cloud API + Coexistence only, no Baileys, no unofficial WA Web emulation, anywhere in the stack.

## Legal status confirmation

WhatsApp Cloud API + Coexistence (Embedded Signup) is Meta's own sanctioned mechanism for exactly this use case — an SMB keeps their WhatsApp Business App and number while a third-party tool gets API-level read/sync access. No ToS violation, no ban risk, when built on this path only. Requires: Meta Business Manager account, WhatsApp Business Account (WABA), a Meta App with the WhatsApp product added, then the Embedded Signup flow per client.
