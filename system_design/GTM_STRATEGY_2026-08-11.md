# Go-to-market strategy — written 2026-08-11

Written after ~355 cold contacts across three products produced zero customers.
This document exists so that every decision below has a stated reason and can be
argued with, rather than being re-invented next week.

**The one-line change:** stop selling a problem people have to be convinced of,
and start selling a cheaper version of a purchase they have already made.

---

## 1. Why the last three attempts failed

| Attempt | Pain we sold | Was it funded? | Result |
|---|---|---|---|
| AI Chatbot → stores | "customers ask questions at night" | No — nobody had a budget line | 0 / ~200 |
| AI Chatbot → agencies | "resell our bot" | No — not their problem | 0 / ~100 |
| QuoteRadar | "quotes go quiet" | No — and they believe a person covers it | 0 / ~55 |

Reply rate to openers was ~20%, five times the cold-WhatsApp benchmark. **The
opener was never the problem.** Every conversation died at the moment of
explanation, because the explanation was an argument: *you are losing money in a
way you haven't noticed.* Nobody buys the resolution to an argument from a
stranger.

The common flaw is targeting by **category** (Pakistani Shopify stores, UAE
fit-out firms) — businesses that *look like* they should have the problem.

---

## 2. The wedge: COD order confirmation

### The pain, and why it is different

- Cash on delivery is **over 80% of Pakistani e-commerce transactions**.
- National average RTO (return to origin) is **18–20%**, and **30–40%** at the
  bad end — the highest of any region.
- Every RTO costs the store two-way courier charges, packaging, and locked-up
  capital. It is a cash loss, per parcel, every single day.
- Stores already fight it by **hiring people to phone every order**. Agent
  salaries run **PKR 25,000–60,000/month**, and Rozee and Indeed PK carry a
  constant stream of "Customer Support and Order Confirmation" ads —
  1,000+ WhatsApp-related listings on Indeed PK alone.

This is the opposite of every pain we have sold so far:

| Test | Quotes going quiet | COD confirmation |
|---|---|---|
| Does the owner already know? | No | Yes — it is their loudest complaint |
| Is money already allocated? | No | Yes — a salary, right now |
| Can it be measured? | Vaguely | Exactly: parcels not shipped × courier cost |
| Do they believe a human covers it? | Yes, fatally | Yes — and that human costs 30k/month |

"We already have a person" ends the QuoteRadar conversation. Here it *starts*
the conversation, because a person is precisely what we are undercutting.

### The offer

> We confirm every COD order on WhatsApp within 5 minutes of it being placed.
> Confirmed orders ship. Unreachable and cancelled ones never leave your
> warehouse. You stop paying two-way courier on parcels that were never real.
>
> First 100 orders free. After that PKR 7,500/month. If your confirmation rate
> doesn't beat what your team does by hand, you pay nothing and we switch it off.

Risk reversal is not a discount tactic — it is the direct answer to the trust
problem that killed 355 conversations. An unknown person from another city
cannot be trusted in advance. They can be trusted **afterwards**.

### Why they can say yes in one day

**The client integrates nothing.** v1 sends from our own WABA with the store's
name in the message body. No Meta account, no Embedded Signup, no Tech Provider,
no access to their WhatsApp, nothing to install. This removes the exact sentence
that killed QuoteRadar — *"connect your entire business WhatsApp to software from
someone you have never met."*

Trade-off, stated honestly: the message arrives from a number the customer does
not recognise, which will convert slightly worse than the store's own number,
and heavy reporting could hurt our WABA quality rating. Mitigations: store name
in the first line, only message people who ordered minutes ago, and migrate
paying clients onto their own number via Coexistence once they trust us.

### Unit economics

| Item | Amount |
|---|---|
| Meta utility template, Pakistan | ~PKR 2.79 per delivered message |
| Customer's reply and our follow-ups | Free (inside the 24h service window) |
| 300 orders/month | ~PKR 840 in Meta fees |
| Price to client | PKR 7,500/month |
| **Gross margin** | **~89%** |
| What we replace | a PKR 25,000–60,000 salary |

At 300 orders/month and 20% RTO, roughly 60 parcels are returned. Catching even
half before dispatch saves the store more than the fee, before counting the
salary.

---

## 3. Targeting: signals, not categories

Every prospect must carry **public evidence of a funded, admitted problem**. No
guessing. Ranked by strength:

| Tier | Signal | Why it is strong |
|---|---|---|
| 1 | Hiring a confirmation / WhatsApp support agent right now (Rozee, Indeed PK, LinkedIn, FB job posts) | Problem admitted publicly, budget already approved, decision-maker already looking |
| 1 | Job ad posted and still open 3+ weeks | They cannot fill it — we are the easier answer |
| 2 | Running Meta ads to a COD store | They pay per lead, so a wasted parcel has a price they already know |
| 2 | Reviews or comments complaining about fake orders / no confirmation call | Pain in their own words, quotable back to them |
| 3 | High-volume Shopify/Woo COD store, no confirmation flow visible | Category only — use to fill the list, never to lead |

We already hold hundreds of vetted Pakistani stores with contact numbers from
the chatbot work, plus `_CONTACTED_MASTER.md`. Those become the base layer; the
signals above are the ranking on top.

### The list we build

`intent_hunter.py` — scrapes job boards for the roles our automation replaces,
cross-references store presence, ad activity and WhatsApp behaviour, and emits a
ranked list where **every row carries its evidence**. Same discipline as
`store_vet.py`: no row without proof.

---

## 4. The approach

The opener already works — 20% reply rate. Keep it short and preview-safe. What
changes is everything after the reply.

**Rule: never explain the product.** Lead with their own evidence.

1. **Opener** — reference the signal, not the product.
   *"Aoa — saw you're hiring for order confirmation. Quick question about that,
   are you free?"*
2. **On reply** — one sentence of outcome plus one number, no mechanics.
   *"We confirm COD orders on WhatsApp in under 5 minutes so fake orders never
   ship. Costs less than a tenth of an agent."*
3. **Proof** — a 30-second recording of the flow running on **their own** store's
   order format, with their name in it. Built per prospect, automatically.
4. **Close** — first 100 orders free, no integration, live tomorrow.

### Objection answers, written in advance

- **"We already have a person."** — Good, keep them. They should be selling, not
  dialling. This handles the calls; they handle what actually needs a human.
- **"Who are you?"** — A one-line answer, then straight back to the free trial.
  Credibility is not established by talking; it is established by them watching
  it work on their own orders for free.
- **"I'll ask my team."** — Historically means no. Pre-empt: *"Nothing to
  decide — send me one test order and see it happen."*
- **"Is this allowed / will WhatsApp ban us?"** — Official Meta Cloud API,
  utility templates, no unofficial libraries. Reference: we already run a
  Meta-approved app.

---

## 5. Funnel maths and kill criteria

Working assumptions from our own history, to be replaced by real numbers:

| Stage | Rate | Per 100 signal-qualified |
|---|---|---|
| Reply to opener | 20% | 20 |
| Watch the proof | 40% of repliers | 8 |
| Accept a free trial (nothing to lose) | 40% of watchers | 3 |
| Convert to paid after trial | 50% | **1–2 paying** |

At PKR 7,500 each, ten clients is PKR 75,000/month at ~89% margin. That is the
first real target — not a hundred clients.

**Kill criteria, agreed in advance so we do not repeat the last three months:**

- 40 tier-1 prospects contacted with zero free trials accepted → the *offer* is
  wrong, not the wording. Change the offer.
- 5 free trials run with zero conversions to paid → the *value* is not real.
  Stop and re-examine.
- Any client churning inside month two → fix delivery before selling more.

---

## 6. What gets built, and in what order

Reuses the QuoteRadar engine heavily — webhook ingest, dedupe, state, dashboard
are all already written and tested.

1. **`intent_hunter.py`** — the signal-based target list. *Nothing else matters
   until this exists.*
2. **Order-confirmation flow** — store order feed → utility template within 5
   minutes → capture reply → confirmed / cancelled / unreachable → dashboard.
3. **Per-prospect proof recording** — auto-generated, their store, their format.
4. **Client dashboard** — reuse QuoteRadar's, retitled: confirmed, cancelled,
   unreachable, and rupees saved.
5. Only when 3+ clients exist: their own number via Coexistence, which is when
   Tech Provider verification finally becomes worth the paperwork.

## 7. What this does not change

QuoteRadar is not thrown away. Its engine is the foundation, and its
positioning stays available for the UAE list once there is a Pakistani reference
to open with. The 25 unspent UAE contacts remain unspent, deliberately.
