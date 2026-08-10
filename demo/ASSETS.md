# QuoteRadar demo assets

Built 2026-08-06. Everything lives in `Documents\Projects\Quote Querry\demo\`.

Two editions of the same product, differing only in currency, customer names,
cities and phone numbers. **Match the edition to the prospect's country** —
sending a Dubai fit-out prospect a screen showing PKR reads as a template.

## Which file to send

| Prospect | Screenshot (send first) | Film (send only if they ask for a demo) |
|---|---|---|
| **UAE / Gulf** | `ui_uae_mobile_light.png` | `quoteradar_film_uae.mp4` |
| **Pakistan** | `ui_pakistan_mobile_light.png` | `quoteradar_film_pakistan.mp4` |

**Send the mobile screenshot, not the desktop one.** Prospects open WhatsApp on a
phone; the desktop shot renders as an unreadable wide strip in a chat thread.

Desktop versions (`ui_*_desktop_light.png`, `ui_*_desktop_dark.png`) are for
email, a landing page, or a pitch deck — not for WhatsApp.

## Sequencing

The film is **not** an opener. Current outreach plan is text-first; the video
goes out only when a prospect asks what it looks like. Leading with an 8 MB
video to a cold contact reads as a broadcast.

## Delivery notes

- Send the MP4 **as a video** (Gallery), not as a document — decided 2026-08-06.
  WhatsApp re-encodes video regardless, so the extra fidelity of a lossless
  master would never reach the viewer. Rendered accordingly at CRF 18.
- If a film is ever needed for **YouTube** or byte-exact transfer, re-render with
  `python capture_film.py --lossless` (PNG frames, CRF 12). Much slower, much larger.
- UAE film is ~8.8 MB, comfortably inside WhatsApp's send limit.

## Numbers shown in the demos

Both totals are computed from the visible rows — the header total always equals
the sum of the quotes on screen. Do not quote a different figure in a message
than the one in the image; a fit-out owner will add up the column.

| | UAE | Pakistan |
|---|---|---|
| Money in quiet quotes | **AED 210,000** | **PKR 250,000** |
| Drawn from | 4 of 6 overdue quotes | 4 of 6 overdue quotes |
| Untracked | 2 quotes have no amount | 2 quotes have no amount |
| Largest single quote | AED 132,000 (showroom fit-out) | PKR 110,000 (showroom furnishing) |
| Oldest wait | 12 days | 12 days |

## Claims the assets make (safe to repeat in a message)

- Watches every WhatsApp chat automatically — no tagging, no pipeline setup.
- Flags on two signals only: who spoke last, and how long ago.
- No AI reads the customer's messages.
- Never sends anything on its own — it opens the chat in the owner's own WhatsApp.
- Closing a quote stops the countdown; a new message from that customer reopens
  it automatically.
- Quote amounts are optional; the queue works identically without them.

## Claims the assets do NOT support (do not write these)

- Anything about who on the team read a message — WhatsApp provides no such
  signal, and the product deliberately does not claim it.
- "The customer hasn't seen your reply" — absence of a read receipt is not proof.
  The UI only ever shows a *Seen* mark when WhatsApp confirms one.
- Any payment, invoicing or accounting capability.

## Regenerating

Source HTML is the master; the PNGs and MP4s are derived.

```
python capture_ui.py          # all 6 screenshots
python capture_film.py        # both MP4s
python capture_film.py uae    # one edition
```

The PKR files are generated from the AED files by a replacement map in
`scratchpad/make_pkr.py` — edit the AED source, then regenerate, so the two
editions never drift apart.
