# Quote Recovery Queue — Codebase Fit Assessment

Last updated: July 29, 2026

## Question

Can we take an open-source WhatsApp inbox/CRM codebase and basically copy-paste the whole system for our product?

## Short answer

`Not copy-paste.`

`But yes, a lot of the hard plumbing already exists and can be reused.`

## Best current candidate

### wacrm

Sources:

- [wacrm docs overview](https://wacrm.tech/docs)
- [wacrm architecture](https://wacrm.tech/docs/architecture)
- [wacrm inbox docs](https://wacrm.tech/docs/inbox)
- [wacrm public API](https://wacrm.tech/docs/public-api)

## Why wacrm is the best fit

It already appears to contain most of the communication-layer system we would otherwise have to build from zero:

- official Meta Cloud API integration
- incoming webhook handling
- message storage
- contact creation/matching
- conversation creation/matching
- real-time inbox updates
- conversation list UI
- thread UI
- team/shared inbox structure
- conversation statuses
- public API for messages/contacts/conversations

### Architecture signs that the backend is real, not just a UI

The architecture docs explicitly show:

- `src/app/api/whatsapp/webhook/` for inbound from Meta
- `src/app/api/whatsapp/send/` for outbound messages
- `src/app/api/whatsapp/templates/` for templates
- `src/lib/whatsapp/` for Meta API client + encryption + phone utils
- Supabase-backed data/auth/realtime

The inbound request lifecycle is clearly documented:

- Meta webhook hits the app
- contact is found/created
- conversation is found/created
- message row is inserted
- realtime updates the inbox

That is real backend plumbing, not just mock frontend.

### Inbox fit to our product

The inbox docs show:

- conversation list
- message thread
- contact sidebar
- message statuses
- open/pending/closed conversation states

This is close to the communication foundation we need.

## Important limitation

wacrm is still a broad WhatsApp CRM, not our product.

So we should think:

- `reuse the communication engine`
- `custom-build the quote workflow engine`

## What we can probably reuse directly

- WhatsApp webhook/backend plumbing
- message ingestion/storage
- conversation list UI
- message thread UI
- contacts
- team/shared inbox structure
- message status handling
- realtime updates

## What we can probably reuse partially

- conversation status system
- contact sidebar
- pipeline/deal concepts
- automations
- public API

These may help, but they likely need adaptation.

## What we still need to build ourselves

- `Mark Quote Sent`
- quote object / quote table
- quote queue page
- quote-specific states:
  - waiting for customer
  - customer replied
  - team action needed
  - needs revision
  - won
  - lost
  - delayed
- quote-linked timeline
- reopened quote logic
- quote-detail panel behavior
- “why this quote is here” logic
- owner-focused quote recovery views

## Is the entire system already present?

### Communication system

Mostly yes.

The WhatsApp inbox/conversation/backend layer looks substantially present.

### Quote recovery system

No.

That part is still our custom product layer.

So the honest answer is:

`the communication engine is largely there`

but

`the quote-recovery engine is not there yet`

## Can we just copy-paste it and start?

Not safely.

Reasons:

- we still need to inspect the actual repo code before implementation
- we need to understand its database model
- we need to carve away generic CRM features
- we need to add our custom quote workflow
- we need to make sure the license and maintenance posture are acceptable

Also, there is at least one publicly documented 2026 security issue against wacrm's automation engine:

- [CVE-2026-49141](https://nvd.nist.gov/vuln/detail/CVE-2026-49141)

This does **not** automatically kill the option.
But it means we should not treat it like a magical drop-in base without code review.

## Chatwoot comparison

Sources:

- [Chatwoot GitHub](https://github.com/chatwoot/chatwoot)
- [Chatwoot inbox/channel docs](https://www.chatwoot.com/hc/user-guide/articles/1677492191-adding-inboxes)

Chatwoot is:

- much more mature
- more battle-tested
- broader
- more support/helpdesk-oriented
- heavier technically

Meaning:

- very strong as a general conversation desk
- less naturally aligned with quote recovery
- likely more work to bend into our product

## Final assessment

### If the question is:

`Can we reuse a lot of the WhatsApp UI/backend system?`

Answer:

`Yes.`

### If the question is:

`Is it already so complete that we just paste it and our product is done?`

Answer:

`No.`

### Best current technical direction

1. use `wacrm` as the first serious foundation candidate
2. treat it as the communication-layer base
3. build Quote Recovery Queue as a custom layer on top
4. do not assume zero engineering work

## Practical conclusion

This idea is more feasible than it looked at first because the hardest generic WhatsApp inbox plumbing appears reusable.

But it is not a zero-work “copy and launch” situation.
