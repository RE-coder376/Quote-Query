# What WhatsApp can and cannot tell us — plain-language reference

Date: 2026-08-06

Purpose: plain-English companion to [[webhook_signal_verification_2026-08-06]]. That doc has the technical verification and sources. This one exists so the constraint stays obvious to anyone (including future sessions) without re-reading webhook documentation. The most common confusion is mixing up the two message directions — they have completely different visibility.

## Direction 1 — customer messages the business

| Signal | Available? |
|---|---|
| Their message arrived, and when | ✅ Yes |
| Did staff **open** it | ❌ **No. Never.** No webhook reports this. |
| Did staff **reply** | ✅ Yes (including replies typed in the WhatsApp Business App, via `smb_message_echoes`) |

## Direction 2 — business replies to the customer

| Signal | Available? |
|---|---|
| Message sent + delivered to their phone | ✅ Yes |
| Did they **open** it | ⚠️ Only if that person has read receipts enabled. Silently absent otherwise. |
| Did they **reply** | ✅ Yes |

**Summary:** "seen" exists only for the customer reading *our* message, and only for some contacts. There is no "seen" signal for staff reading a customer's message, in any form.

## What this means for the product

**The follow-up mechanic works fully and never depended on "seen":**

Owner sets a threshold (e.g. 3 days).
- Customer messaged 3 days ago, no reply sent → **Follow-up needed** (business owes them)
- Business replied 3 days ago, no response back → **Follow-up needed** (customer owes them)

Both computed from message direction + timestamp. Reliable for every contact, unaffected by any privacy setting.

**What is lost:** the ability to separate "they read the quote and went quiet" (interested, hesitating) from "they never opened it" (wrong number? uninterested?). Both land in the same follow-up bucket. The required action is identical either way — chase them.

**What can still be shown:** a small "seen" marker on a row when WhatsApp happens to provide it. Acceptable as a cosmetic detail.

**What must never be built:** a bucket/filter named "Seen but no reply." Everyone with read receipts disabled would be silently missing from that list, and the owner would believe it was complete. Same rule applies to any UI that renders absence-of-read-receipt as "unseen" — that is an unprovable claim, not a fact.

## The rule to carry forward

Only build states on signals that arrive 100% of the time (message direction, timestamps). Anything conditional — read receipts especially — is display-only enrichment, never a state, filter, or count the owner is expected to trust as complete.
