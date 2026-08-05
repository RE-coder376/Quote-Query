# Revenue tracking — how it actually works, and what it must not become

Date: 2026-08-06

Purpose: [[value_depth_enhancements_2026-08-06]] proposed revenue-at-risk framing as the highest-leverage addition. Hamza flagged it could go wrong. This doc locks the safe version and draws a hard line against the failure mode.

## What goes wrong with the naive version

**Undercount-as-lie:** quote amounts must stay optional to keep the zero-friction philosophy ([[auto_classification_state_model_2026-08-06]]). Optional entry means partial adoption — most stale quotes won't have a value recorded. A dashboard showing "AED 12,000 at risk" when the true figure is AED 60,000 doesn't look incomplete, it looks *wrong* — and once an owner (who knows their own deal sizes) catches one bad number, trust in the entire dashboard collapses, including the parts that were accurate.

**"Paid" reopens excluded scope.** Tracking what a customer actually paid (vs. what was quoted) means tracking partial payments, installments, renegotiated prices, discounts — a real invoicing subsystem. [[product_system_summary]] already excludes this explicitly ("It is not: ... accounting software... payment software"). Adding a "how much it paid" field is the exact kind of small-looking request that pulls the whole product back into the category it's positioned against.

## The safe version

**One field only: `quoted_amount`.** Captured optionally when staff does `Mark as Quote` — not a separate section, not a second workflow, just one number field on the same action. No editing history, no partial/paid tracking, no currency conversion logic.

**`Won` reuses the same number, nothing new.** When a quote is marked Won, the reporting figure is the `quoted_amount` already on file — not a "final paid amount." If the real deal closed at a different price, that's accepted imprecision, not a bug to fix with a new field. The product answers "roughly how much was at stake," not "what did we collect" — that boundary has to be explicit and stated as a deliberate exclusion, not silently dropped later.

**Revenue-at-risk must show its own denominator, never a bare total.** Instead of "AED 45,000 at risk" (implies completeness), show "AED 32,000 recorded across 5 of 7 stale quotes (2 untracked)." This is the actual fix for the undercount problem — it's honest about partial data instead of presenting a number that looks authoritative but isn't. A transparent partial number builds trust; a confident-looking wrong number destroys it.

**Amount prompt only fires at an action staff already chose to take.** No prompt on every message, no prompt on entering `Unanswered`/`Read`/etc. states ([[auto_classification_state_model_2026-08-06]]) — only at the moment someone deliberately clicks `Mark as Quote`, which is already a manual decision point. Marginal friction is low because they're already stopping to act; this does not violate the "no manual entry required anywhere in the core loop" rule because the core loop (states 1-5) works identically with zero quotes ever marked.

## Hard line

If actual payment tracking is wanted later (partial payments, installments, "how much it paid"), that is a deliberate v2 scope decision requiring explicit reopening — not something to fold in by default because it looks like a small addition next to `quoted_amount`. Flagging this now so it doesn't drift in unnoticed during build.
