# Webhook signal verification — what Coexistence actually gives us

Date: 2026-08-06

Purpose: [[auto_classification_state_model_2026-08-06]] built its 4 core states on WhatsApp read/delivered ticks. That assumption was never verified. This doc records the verification and corrects the model. **One of the four states is unbuildable as specified.**

## Verified findings

### 1. There is NO webhook for "the business read an incoming message" — state 2 is unbuildable

`smb_message_echoes` fires when the business **sends**, edits, or revokes a message from the WhatsApp Business App. Its documented scope is outbound-only: it "does not include delivery statuses, read receipts, or seen status for incoming messages."

`smb_app_state_sync` syncs the business's **contacts**, not message read state.

Nothing in Coexistence reports that staff opened a customer's message. **"Read, Reply Needed" (state 2) cannot be distinguished from "Unread" (state 1).** They collapse into one state.

### 2. Outbound read status exists but is unreliable — state 4 degrades silently

The standard `statuses` webhook does deliver `sent` / `delivered` / `read`. But:
- If the recipient disables read receipts in privacy settings, the `read` status **never fires** — the message sits at `delivered` permanently even after being read.
- Additional Meta privacy rule: if the recipient hasn't previously communicated with the business or added it as a contact, read status is withheld until they reply or add the contact. (Lower risk for us — our customers message first — but it applies to any business-initiated thread.)

**This is the dangerous part: "delivered, never read" and "read, but receipts disabled" are indistinguishable.** A UI state that says "customer hasn't seen your reply" would be silently wrong for every privacy-conscious contact, with no way to detect which.

### 3. What IS 100% reliable

- Inbound message arrival + timestamp (standard `messages` webhook)
- Outbound message sent, including from the WhatsApp Business App (`smb_message_echoes`)
- Therefore: **message direction and elapsed time between them** — fully reliable, no privacy dependency, no degradation.

## Corrected state model

The core loop rests **only** on direction + time. Read receipts become optional enrichment that never drives a state the UI depends on.

**Reliable states (the product):**
1. **Awaiting Reply** — customer's last message has no outbound message after it. (Merges old states 1 and 2. The required action is identical either way — reply — so the lost distinction costs nothing operationally.)
2. **Awaiting Customer** — business's last message has no inbound message after it.
3. **Needs Follow-up** — overlay flag: either state above, past `StaleThreshold`. Unchanged, and unaffected by any of this.

**Soft enrichment (display only, never a state):** if a `read` status arrives on an outbound message, show a subtle "seen" marker on the row. If it never arrives, show nothing — **not** "unseen," which would be a false claim. Absence of a read receipt must never be rendered as evidence the customer didn't read it.

## What this costs, honestly

Lost: the ability to tell an owner "your staff are opening messages and ignoring them" vs "your staff aren't opening messages at all." That's a management diagnostic, not core-loop function.

Not lost: everything the product actually sells on. "No reply has been sent to this customer in 3 days" is fully computable and is the claim the whole pitch rests on. The "false coverage assumption" pain point (one staffer assumes another replied) is still solved — the system reports whether a reply exists, regardless of who believed what.

**Net: the model gets simpler and more honest. Three states instead of five, zero dependency on a signal that silently fails.**

## Correction to earlier docs

- [[auto_classification_state_model_2026-08-06]] — states 1-4 replaced by the 2+1 model above. States 1/2 unbuildable-as-separate; states 3/4 unreliable as a boundary.
- [[value_depth_enhancements_2026-08-06]] item 4 (staff attribution, "who last touched this") — **also unbuildable.** Staff share one number; `smb_message_echoes` reports the number, not which human sent it. Remove from the roadmap unless a per-staff-device signal is found.
- [[feature_plan_and_ui_spec_2026-08-06]] F12 Daily Digest — separate unverified risk, not covered here: outside the 24-hour window, business-initiated messages require a pre-approved Meta template, and per-conversation fees apply (~30/month/client recurring COGS against an AED 99-199 price). Needs its own verification before F12 is treated as cheap.

## Sources

- smb_message_echoes scope/limitations: https://dualhook.com/docs/webhook-smb-message-echoes
- Coexistence webhook overview: https://whautomate.com/whatsapp-coexistence
- Read-receipt suppression behavior: https://support.whapi.cloud/help-desk/troubleshooting/not-getting-a-read-status-on-webhook , https://wasenderapi.com/help/whatsapp-sessions/troubleshooting-not-getting-read-status
- Meta webhook components reference: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/components
