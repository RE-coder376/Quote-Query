# Quote Recovery Queue — WhatsApp Foundation Options

Last updated: July 29, 2026

## Purpose

This note compares open-source WhatsApp inbox / CRM foundations that could save time when building Quote Recovery Queue.

Goal:

- avoid building the WhatsApp conversation layer from scratch
- reuse existing inbox/message plumbing where possible
- build our quote workflow layer on top

## What we need from a base

The foundation should ideally give us:

- official WhatsApp Business API support
- conversation list UI
- conversation thread UI
- message storage
- webhook/incoming-message plumbing
- contact mapping
- ownership / assignment support

What we will build ourselves:

- `Mark Quote Sent`
- quote object
- quote queue
- quote states
- quote-linked conversation logic
- silent-after-quote / team-action-needed workflow
- won/lost/delayed/reopen logic

## Best current option

### 1. wacrm

Site:

- [wacrm homepage](https://wacrm.tech/)
- [wacrm docs](https://wacrm.tech/docs)

Why it stands out:

- explicitly built on the official WhatsApp Business API
- open-source
- already has:
  - shared inbox
  - contacts
  - pipelines
  - templates
  - automations
  - agent ownership
- documentation openly describes architecture and WhatsApp setup
- much closer to our use case than a generic helpdesk

Strong signs from docs/site:

- official Cloud API support is explicitly stated on the homepage
- inbox and automation features are already documented
- automations support inbound-message triggers, contact triggers, tagging, assignment, wait steps, and sending templates

Useful sources:

- [wacrm homepage](https://wacrm.tech/)
- [wacrm docs](https://wacrm.tech/docs)
- [wacrm automations docs](https://wacrm.tech/docs/automations)
- [wacrm cron/automation docs](https://wacrm.tech/docs/automations-and-cron)

Why this fits our design:

Our product needs:

- conversations loaded into UI
- conversation context around a quote
- ability to attach business workflow to a conversation

wacrm already appears to solve the hardest generic layer:

- WhatsApp conversation handling
- inbox UI
- agent/team structure
- official messaging plumbing

Our custom product would then sit on top of that layer.

Main concern:

- it is broader than our product
- we would need to strip away or ignore generic CRM pieces
- we still need to inspect the code later before committing

Current verdict:

`Best first foundation candidate`

## Good fallback option

### 2. Chatwoot

Sources:

- [Chatwoot inbox/channel guide](https://www.chatwoot.com/hc/user-guide/articles/1677492191-adding-inboxes)
- [Chatwoot GitHub](https://github.com/chatwoot/chatwoot)

Why it matters:

- mature open-source inbox/helpdesk
- supports WhatsApp among many other channels
- proven omnichannel conversation system

Why it is less ideal than wacrm:

- more support/helpdesk-oriented than sales-quote-oriented
- broader and heavier
- likely more work to shape into a quote-recovery product

Current verdict:

`Strong technical fallback, but less aligned product-wise`

## Official platform reference

Regardless of which open-source base we use, the underlying model still depends on the official WhatsApp Business Platform.

Useful references:

- [Meta WhatsApp Business Platform Postman overview](https://www.postman.com/meta/whatsapp-business-platform/overview)
- [Webhook payload reference](https://www.postman.com/meta/whatsapp-business-platform/folder/vzaxn16/webhook-payload-reference)

Meaning:

- incoming messages and statuses come through official APIs/webhooks
- the product should be built around official business integration, not WhatsApp Web scraping

## Update 2026-08-06 — Coexistence-specific candidate found

`open-bsp-api` (`github.com/matiasbattocchia/open-bsp-api`) implements Coexistence via Embedded Signup directly and is multi-tenant. Narrower than wacrm — it covers only the Coexistence connection step, not a full inbox/CRM shell. Read it specifically for the Embedded Signup + webhook handling; still use wacrm for the inbox/CRM shell layer. Full feature-scope comparison against Kommo/Zena/Adjoltz now lives in [[competitor_feature_diff_and_build_scope_2026-08-06]].

## Current technical recommendation

If we continue with this product, the current best path is:

1. inspect `wacrm` first
2. confirm whether its codebase is practical enough to fork/adapt
3. use it as the conversation/inbox foundation if it looks solid
4. build the custom Quote Recovery Queue workflow on top

## What is already decided from this comparison

We should **not** plan to build the WhatsApp inbox layer from zero.

We should think in terms of:

- `foundation product` = WhatsApp inbox/CRM base
- `our product layer` = Quote Recovery Queue

That is the current saved direction.
