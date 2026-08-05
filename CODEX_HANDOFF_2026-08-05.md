# Codex Handoff — Quote Recovery Queue (Quote Querry)

Date: August 5, 2026
Purpose: bring Codex up to date on a strategy session that changed the go-to-market, and hand over the next task.
Product design itself is unchanged — see `system_design/product_system_summary.md`. This document is about **market, channel, and sequencing**.

---

## 1. Current state (facts, not plans)

- **Code written: none.** The project is design decisions only.
- **Outreach done:** ~120 Pakistani businesses cold-messaged on WhatsApp (interior, kitchens, uPVC, solar). Lists and prefilled `wa.me` links are in `outreach/`.
- **Result:** 8 "interested". Zero paying. All 8 are **weak hypothetical yeses** — they reacted to a description, not a product, and none has been asked for or given a commitment.
- **Outreach is paused** (~2 days) for an unrelated hardware reason. It should stay paused — see §5.

---

## 2. Options considered and rejected this session

### Rejected: LinkedIn outreach to Pakistani businesses
Suggested previously as a way around low WhatsApp reply rates. Rejected on ICP grounds.

Pakistan has ~18.0M LinkedIn *registered members* (~12.3% of the 18+ population), but LinkedIn publishes registrations, not monthly actives — unlike every other platform. The real active base is far smaller and skews to IT, banking, telecom, corporate HR, students, and jobseekers. Interior/kitchen/uPVC/solar SMB owners are not in it. Cold DM also requires InMail (Sales Navigator, ~$100/mo) or connection requests that dormant accounts never accept.

**Note the asymmetry:** LinkedIn *does* work when the buyer is a foreign founder/CTO. The channel isn't bad; the PK-SMB ICP is wrong for it.

### Rejected: phone calls and showroom visits
Highest-converting motion for PK SMBs, but ruled out — founder constraint (not comfortable cold-calling or walking in). Also moot: there is no product to show. Do not re-propose.

### Rejected: build a thin slice to demo early
Standard advice would be: ship the smallest vertical slice, record it, sell off that. **It does not apply here.** The core loop — inbound lands as `Unanswered` → ages past threshold → surfaces → follow-up → outcome — *is* roughly 90% of the total build. There is no meaningful slice that is both demoable and cheap. Building it early would look trivial to prospects and would not save time.

**Conclusion: the product must be built more or less in full before any demo exists.**

### Rejected: cold WhatsApp to US/UK/EU businesses
WhatsApp is a personal channel in those markets, not a business one. Consequences: WhatsApp Business account ban risk (would lose **923354106848**, the number the 8 leads already have), GDPR/TCPA exposure, and Cloud API template approval will not pass cold sales copy. This is already excluded by the project's zero-risk rule (official Cloud API + Coexistence only).

For US/UK/AU the correct channel is **cold email**, not WhatsApp.

---

## 3. Root-cause finding

The working theory was *"70-80% of businesses never see the message."* That is likely wrong. These businesses publish that number on their website specifically to receive messages from strangers — it is their sales line. Absence of blue ticks proves nothing (read receipts are commonly disabled). They see it and decline to reply.

Evidence from the same project: the preview-safe `"is someone available?"` opener produced 7+ replies where the previous opener produced ~0. Same channel, same list, different message. **Visibility was never the constraint.**

The deeper issue: **8/120 ≈ 6-7% is a normal cold-outreach interest rate.** Interest generation is not broken. What is broken is the step from *interested* → *paying*, and that step is currently impossible because there is no product. Every additional message sent right now generates unconvertible interest.

**This repeats the AI Chatbot failure mode:** that product was finished — 100% evals, per-store branding, analytics, admin panel, demo keys, video generator — and still produced ~0 sales across 100s of stores and ~100 agencies. Completeness was never the missing variable. Do not treat "build more features so it's impressive enough" as the fix.

---

## 4. THE PIVOT

Two changes. Both are decided.

### 4a. Market: Pakistan → UAE / Gulf

Same product, same vertical, same channel, different country.

| | Pakistan | UAE / Gulf |
|---|---|---|
| WhatsApp as business channel | Yes | Yes — default, every site has a WA button |
| Target vertical present | Yes | Yes — interior fit-out, kitchens, joinery, uPVC is a major industry |
| Est. price tolerance | PKR 5,000/mo (~$18) | AED 300-500/mo (~$80-135) — **unvalidated estimate, must be tested** |
| Cold WA acceptable | Yes | Yes — normal business behaviour |
| Language / timezone | — | English works; +1hr; many PK/Indian owners |

Rationale: PKR 5,000/mo is ~$18. A modest living requires 60-100 paying SMBs, each needing convincing, onboarding, and support, in a market that churns hard and pays late. One Gulf client is worth 5-7 PK clients for identical effort. Pakistan was chosen for proximity, not for ability to pay.

WhatsApp cold outreach also works in India, Brazil, Mexico, Indonesia, Egypt, Nigeria — Gulf is first because of vertical density and price tolerance.

The existing PK list is **not** the launch list. It is a fallback and a source of design-partner conversations.

### 4b. Funding: products financed by services income, not by hope

Stated founder goal: make a living building products like this one. That requires products to be *funded* rather than to be the thing that must work first.

How Pakistani software houses actually fill pipelines, for reference — none of it resembles what has been tried here:
1. **Upwork / Fiverr at volume** — the dominant channel; teams bidding 30-80 proposals/day with a connects budget
2. **White-label subcontracting** — being the invisible backend for a US/UK agency; one relationship = years of work
3. **Directories** — Clutch, GoodFirms, DesignRush (paid placement + reviews)
4. **Cold email at volume** — multiple warmed domains, Instantly/Smartlead, 1-3% reply
5. **LinkedIn** — works here, because the buyer is a foreign founder/CTO
6. **Referrals**

They sell **services** (client pays for the build, sell → then build, demand already exists) not **products** (self-funded, build → then hope, demand must be created). Quote Querry is the harder game being run without the funding that normally supports it.

**Decision: run the Upwork/foreign-services track in parallel** — it matches the already-saved career direction (240-day roadmap, FastAPI/LangChain/RAG stack). Services income buys runway for repeated product attempts. Quote Querry is a bet, not the plan.

---

## 5. Sequencing rule (do not violate)

```
BUILD  →  RECORD DEMO ON REAL DATA  →  THEN OUTREACH (Gulf)
```

**No cold outreach until a working demo exists.** The prospect pool per market is finite — a few hundred good fit-out companies per city. Every business messaged with nothing to show is one that cannot be approached fresh later; a second pitch to someone who already ignored you converts far worse than a first. The PK list was largely spent this way. **Do not spend the Gulf list the same way — it is the one that pays.**

On the demo: the AI Chatbot's `make_video.py` motion is the proven pattern — a recorded video of the product working **on the prospect's own business data**. It produced real replies (RTW, Paperman both requested demos off it). Specificity is what makes a demo land, not feature count. It is also a text-only sales motion, which fits the founder constraint of not calling or visiting.

---

## 6. Open items

- The 8 interested PK businesses have not been split solar vs interior. Still open from Aug 2.
- Gulf pricing (AED 300-500/mo) is an estimate, not researched. Validate before it goes into any pitch.
- No Gulf target list exists yet.
- Cloud API + Coexistence setup is designed but not implemented or tested.

---

## 7. Next task for Codex

**Scope the build.** Produce a realistic implementation plan for the core loop as defined in `system_design/product_system_summary.md`:

inbound conversation lands as `Unanswered` → ages past threshold → surfaces on "Needs First Reply" → staff acts → `Mark as Quote` → tracked to won/lost/delayed/closed.

Required in the output:
1. Component breakdown (WhatsApp Cloud API + Coexistence integration, ingestion, state machine, queue/dashboard UI, notification/threshold engine, storage)
2. Honest calendar estimate — is this 3 weeks or 3 months for one part-time developer
3. The riskiest dependency (assumption: Coexistence behaviour and Cloud API template/approval limits) and how to de-risk it early
4. What must exist specifically to make a **recordable demo** possible, since that gates all outreach

Constraints: zero/near-zero budget; official WhatsApp Cloud API + Coexistence only (Baileys is deleted and permanently excluded); no keyword/intent detection (explicitly rejected — see product summary).

---

## 8. Update — Aug 6, 2026: Coexistence verified + role split with Claude Code

Coexistence technical claims independently verified against Meta's own docs (not just Codex's read — confirmed): `smb_message_echoes` webhook mirrors staff replies sent from the WhatsApp Business App; `smb_app_state_sync` mirrors contacts; up to 6 months chat history syncs on connect; throughput capped at 5 msg/sec (irrelevant at this business's volume). This is a real, documented Meta feature, not an assumption to de-risk from scratch — Codex's research task in §7 should confirm **Gulf/UAE-specific availability** specifically, since rollout can lag region to region, but the core mechanism is not in question.

**Read-only dashboard decision confirmed as correct approach:** not sending replies via the Cloud API (staff keeps replying in the WhatsApp Business App as today) removes template-approval and bot-says-something-wrong risk entirely. `Mark as Quote` is a dashboard-side status action, not a WhatsApp send — no API send permission needed for it.

**Working split going forward:**
- **Codex:** specs, research docs, webhook payload contracts, anything under `system_design/` — no app code.
- **Claude Code:** the actual build — backend, DB schema, webhook endpoint, dashboard UI, state machine, auth, local/demo setup, tests.
- This is a **sequential fallback, not parallel work.** Claude Code builds by default. When Claude's usage limit runs out mid-task, Hamza hands the same task to Codex to continue coding from where Claude stopped — one agent active at a time, never both editing simultaneously.
- Handoff mechanism: **`BUILD_STATE.md`** in the project root. Whichever agent is working updates it before stopping (done / in-progress / next step / any decision made that isn't in the spec docs yet). Whichever agent picks up next reads it first, before touching any code.
- Style continuity: an agent picking up mid-build should match the existing code's patterns (naming, structure, error handling) rather than write in its own style, since the codebase is shared across handoffs.
