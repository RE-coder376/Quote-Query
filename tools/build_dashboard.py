"""Compose app/static/index.html: the demo's stylesheet + a live, API-driven app.

The design stays defined in one place (the demo file). This script lifts its
<style> block so the running product and the sales demo cannot drift apart.

    python -m tools.build_dashboard
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "demo" / "quoteradar_dashboard_aed.html"
TARGET = ROOT / "app" / "static" / "index.html"

BODY = """
<div class="shell">

  <header class="masthead">
    <h1 class="wordmark">
      <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
        <circle cx="12" cy="12" r="9.2" opacity=".35"/><circle cx="12" cy="12" r="5" opacity=".6"/>
        <circle cx="12" cy="12" r="1.6" fill="currentColor" stroke="none"/><path d="M12 12 L19 6.4"/>
      </svg>
      QuoteRadar
    </h1>
    <div class="masthead-meta">
      <span class="connected"><span class="pulse" aria-hidden="true"></span> <span id="biz">—</span></span>
      <span id="clock">—</span>
    </div>
  </header>

  <!-- Only visible while a freshly connected number is backfilling its history. -->
  <div class="importing" id="importing" hidden role="status">
    <span class="pulse" aria-hidden="true"></span>
    <span id="importing-text">Importing your WhatsApp history…</span>
  </div>

  <section class="cards" aria-label="Summary">
    <div class="card card-money">
      <p class="card-label">Money stuck in quiet quotes</p>
      <p class="card-value"><span class="cur" id="cur1">—</span><span id="at-risk">0</span></p>
      <p class="card-sub" id="denominator"></p>
    </div>
    <div class="card card-won">
      <p class="card-label">Won this month</p>
      <p class="card-value" id="won">—</p>
      <p class="card-sub" id="won-sub"></p>
    </div>
  </section>

  <div class="toolbar" role="group" aria-label="Filter the list">
    <button class="filter" type="button" data-filter="all" aria-pressed="true">All open <span class="count" data-count="open">0</span></button>
    <button class="filter filter-owed" type="button" data-filter="awaiting_reply" aria-pressed="false">You need to reply <span class="count" data-count="awaiting_reply">0</span></button>
    <button class="filter" type="button" data-filter="awaiting_customer" aria-pressed="false">Waiting on customer <span class="count" data-count="awaiting_customer">0</span></button>
    <button class="filter" type="button" data-filter="overdue" aria-pressed="false">Overdue <span class="count" data-count="overdue">0</span></button>
    <button class="filter" type="button" data-filter="closed" aria-pressed="false">Closed <span class="count" data-count="closed">0</span></button>
    <span class="toolbar-spacer"></span>
    <span class="threshold-note">Overdue after 24 hours</span>
  </div>

  <div class="workspace">
    <section class="queue" aria-label="Quote list">
      <div class="queue-head" aria-hidden="true">
        <span></span><span>Customer</span><span>Status</span><span class="ta-r">Quoted</span>
      </div>
      <div id="rows"><p class="empty">Loading…</p></div>
    </section>

    <aside class="rail" aria-live="polite">
      <div class="rail-head">
        <h2 id="d-name">—</h2>
        <span class="rail-phone" id="d-phone">—</span>
      </div>
      <div class="rail-body">
        <dl class="facts">
          <div class="fact"><dt>Status</dt><dd id="d-state">—</dd></div>
          <div class="fact"><dt id="d-last-label">Waiting</dt><dd class="mono" id="d-last">—</dd></div>
          <div class="fact"><dt>Quoted amount</dt><dd class="mono" id="d-amount">—</dd></div>
        </dl>

        <div class="thread" id="d-thread"></div>

        <div class="actions">
          <a class="btn btn-primary" id="d-nudge" href="#" target="_blank" rel="noopener">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" aria-hidden="true"><path d="M4 12h13M12 5l7 7-7 7"/></svg>
            Open this chat in WhatsApp
          </a>
          <button class="btn btn-ghost" type="button" id="d-mark">Add quote amount</button>
          <p class="optional-note">Optional. The queue works exactly the same without any amounts — they only feed the money total.</p>
        </div>

        <div class="draft">
          <p class="draft-label">Opens their chat with this ready to edit</p>
          <p class="draft-text" id="d-draft">—</p>
          <p class="draft-foot">Opens <code id="d-link">wa.me/…</code> — your WhatsApp, your thumb on send. Nothing leaves QuoteRadar.</p>
        </div>

        <div class="closeout">
          <p class="card-label">Close this quote</p>
          <div class="closeout-row">
            <button class="btn-sm btn-won" type="button" data-status="won" aria-pressed="false">Won</button>
            <button class="btn-sm btn-lost" type="button" data-status="lost" aria-pressed="false">Lost</button>
            <button class="btn-sm" type="button" data-status="no_deal" aria-pressed="false">No deal</button>
          </div>
          <p class="note">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" aria-hidden="true"><path d="M3 12a9 9 0 1 1 3 6.7"/><path d="M3 20v-6h6"/></svg>
            <span id="reopen-copy"></span>
          </p>
          <p class="note">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" aria-hidden="true"><path d="M4 7h16M9 7V5h6v2M7 7l1 13h8l1-13"/></svg>
            <span>Asked to be forgotten?
              <button type="button" class="linkish" id="d-delete">Delete this customer's records</button>
            </span>
          </p>
        </div>

        <div class="note">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" aria-hidden="true">
            <rect x="4" y="10.5" width="16" height="10" rx="2"/><path d="M8 10.5V7a4 4 0 0 1 8 0v3.5"/>
          </svg>
          <span><b>There is no reply box, on purpose.</b> Your team keeps answering in the WhatsApp Business app they already use. QuoteRadar only watches which chats went quiet.</span>
        </div>
      </div>
    </aside>
  </div>

  <footer class="legend">
    <div><h3>How a chat gets flagged</h3>
      <p>Two things only: <b>who spoke last</b>, and <b>how long ago</b>. No keywords, no AI reading your messages, nothing to set up or tag.</p>
      <p><span style="color:var(--owed);font-weight:600">Orange</span> means the customer spoke last and you owe a reply. <span style="color:var(--parked);font-weight:600">Slate</span> means you spoke last and it's their turn.</p></div>
    <div><h3>About “seen”</h3>
      <p>A <b>seen</b> mark shows only when WhatsApp confirms one. If it's missing, we show nothing — a missing tick is not proof the customer didn't read it.</p></div>
    <div><h3>About the totals</h3>
      <p>Amounts are optional, so every total says <b>how many quotes it came from</b>. A partial figure that admits it beats a confident one that's wrong.</p></div>
  </footer>
</div>
"""

SCRIPT = """
<script>
(function () {
  "use strict";

  var rowsEl = document.getElementById("rows");
  var filterBtns = [].slice.call(document.querySelectorAll(".filter"));
  var statusBtns = [].slice.call(document.querySelectorAll("[data-status]"));

  var activeFilter = "all", selectedId = null, cache = [], summary = {}, sync = {};

  function money(n) { return (n || 0).toLocaleString("en-US"); }
  function cur() { return summary.currency || ""; }

  function api(path, opts) {
    return fetch(path, opts).then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    });
  }

  function load() {
    return api("/api/conversations?filter=" + activeFilter).then(function (d) {
      summary = d.summary;
      cache = d.conversations;
      sync = d.sync || {};
      if (!selectedId && cache.length) selectedId = cache[0].wa_id;
      renderSummary();
      renderSync();
      renderRows();
      if (selectedId) renderDetail();
    }).catch(function () {
      rowsEl.innerHTML = '<p class="empty">Could not reach the server.</p>';
    });
  }

  function renderSync() {
    // The first minutes after connecting are the only time this shows. An empty
    // screen with no explanation is the worst possible first impression.
    var bar = document.getElementById("importing");
    if (!sync.active) { bar.hidden = true; return; }
    bar.hidden = false;
    document.getElementById("importing-text").textContent =
      "Importing your WhatsApp history — " + (sync.imported || 0) +
      " messages so far. Your quotes will appear as they load.";
  }

  function renderSummary() {
    document.getElementById("biz").textContent = summary.business_name;
    document.getElementById("clock").textContent =
      new Date().toLocaleString(undefined, { weekday: "long", day: "numeric", month: "long" });
    document.getElementById("cur1").textContent = cur();
    document.getElementById("at-risk").textContent = money(summary.at_risk_total);

    // The total never appears without the fraction it came from.
    document.getElementById("denominator").innerHTML = summary.at_risk_overdue === 0
      ? "Nothing is overdue. Every open quote has had a reply within 24 hours."
      : "From <b>" + summary.at_risk_counted + " of the " + summary.at_risk_overdue +
        "</b> quotes with no reply for over 24 hours." +
        (summary.at_risk_untracked > 0
          ? " <b>" + summary.at_risk_untracked + " with no amount recorded</b>, so the real figure is higher."
          : "");

    var wonEl = document.getElementById("won");
    if (summary.won_counted === 0) {
      wonEl.textContent = "—";
      document.getElementById("won-sub").textContent =
        "Nothing marked won yet. Close a quote as Won to start the record.";
    } else {
      wonEl.textContent = cur() + " " + money(summary.won_total);
      document.getElementById("won-sub").innerHTML =
        "from <b>" + summary.won_counted + " of the " + summary.won_count +
        "</b> quotes you closed here.";
    }

    Object.keys(summary.counts || {}).forEach(function (k) {
      var el = document.querySelector('[data-count="' + k + '"]');
      if (el) el.textContent = summary.counts[k];
    });
  }

  function icon(c) {
    if (!c.is_open) return '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M20 6 9 17l-5-5"/></svg>';
    return c.state === "awaiting_reply"
      ? '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M19 7 6 20M6 20h9M6 20v-9"/></svg>'
      : '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M5 17 18 4M18 4H9M18 4v9"/></svg>';
  }

  function renderRows() {
    if (!cache.length) {
      rowsEl.innerHTML = '<p class="empty">' + (sync.active
        ? "Loading your past conversations…"
        : "Nothing here right now.") + "</p>";
      return;
    }

    rowsEl.innerHTML = cache.map(function (c) {
      var dir = !c.is_open ? "done" : (c.state === "awaiting_reply" ? "owed" : "parked");
      var pills = "";
      if (c.overdue) pills += '<span class="pill pill-warn">Overdue ' + c.overdue_label + '</span>';
      if (c.outcome === "won") pills += '<span class="pill pill-won">Won</span>';
      if (c.outcome === "lost") pills += '<span class="pill pill-lost">Lost</span>';
      if (c.outcome === "no_deal") pills += '<span class="pill pill-closed">No deal</span>';

      return '<button class="row ' + dir + (c.is_open ? "" : " row-closed") + '" type="button" data-id="' + c.wa_id + '" aria-current="' + (c.wa_id === selectedId) + '">' +
        '<span class="stripe"></span>' +
        '<span class="row-main"><span class="row-name"><strong>' + c.name + '</strong>' + pills + '</span>' +
        '<span class="row-preview">' + (c.last_message || "") + '</span></span>' +
        '<span class="row-status"><span class="status-text">' + icon(c) + c.status + '</span>' +
        '<span class="status-time">' + c.wait_text + '</span></span>' +
        '<span class="row-amount">' + (c.quoted_amount
          ? cur() + " " + money(c.quoted_amount)
          : '<span class="untracked">No amount recorded</span>') + '</span></button>';
    }).join("");
  }

  function selected() {
    return cache.filter(function (c) { return c.wa_id === selectedId; })[0];
  }

  function renderDetail() {
    var c = selected();
    if (!c) return;

    document.getElementById("d-name").textContent = c.name;
    document.getElementById("d-phone").textContent = "+" + c.wa_id;
    document.getElementById("d-state").textContent = c.status + (c.overdue ? " · overdue" : "");
    document.getElementById("d-last-label").textContent = c.is_open
      ? (c.state === "awaiting_reply" ? "No reply from you for" : "No customer reply for")
      : "Waiting";
    document.getElementById("d-last").textContent =
      c.is_open ? c.wait_text.replace(/^.*for /, "") : "stopped";
    document.getElementById("d-amount").innerHTML = c.quoted_amount
      ? cur() + " " + money(c.quoted_amount)
      : '<span style="color:var(--fg-faint);font-weight:400">Not recorded</span>';
    document.getElementById("d-mark").textContent =
      c.quoted_amount ? "Edit quote amount" : "Add quote amount";

    document.getElementById("d-thread").innerHTML = c.messages.length
      ? c.messages.map(function (m) {
          return '<span class="bubble bubble-' + (m.direction === "in" ? "in" : "out") + '">' +
                 (m.text || "(attachment)") +
                 '<time>' + new Date(m.at).toLocaleString() + (m.seen ? " · seen" : "") + '</time></span>';
        }).join("")
      : '<p class="thread-more">No messages yet.</p>';

    var draft = c.state === "awaiting_reply"
      ? "Hi — apologies for the slow reply. Coming back to you on this today."
      : (c.quoted_amount
          ? "Hi — following up on the quote we sent (" + cur() + " " + money(c.quoted_amount) + "). Any questions on it?"
          : "Hi — following up on what we sent over. Any questions on it?");

    document.getElementById("d-draft").textContent = "\\u201C" + draft + "\\u201D";
    document.getElementById("d-nudge").href = "https://wa.me/" + c.wa_id + "?text=" + encodeURIComponent(draft);
    document.getElementById("d-link").textContent = "wa.me/" + c.wa_id;

    statusBtns.forEach(function (b) {
      b.setAttribute("aria-pressed", String(c.outcome === b.getAttribute("data-status")));
    });
    document.getElementById("reopen-copy").innerHTML = c.is_open
      ? "<b>Closing stops the countdown.</b> If this customer messages again, it comes back automatically under <b>You need to reply</b> — nothing to un-archive."
      : "<b>Tracking stopped.</b> The next message from this number brings it back automatically. Press the same button again to reopen it now.";
  }

  rowsEl.addEventListener("click", function (e) {
    var row = e.target.closest(".row");
    if (!row) return;
    selectedId = row.getAttribute("data-id");
    renderRows();
    renderDetail();
  });

  filterBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
      activeFilter = btn.getAttribute("data-filter");
      filterBtns.forEach(function (b) { b.setAttribute("aria-pressed", String(b === btn)); });
      selectedId = null;
      load();
    });
  });

  statusBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
      var c = selected();
      if (!c) return;
      var want = btn.getAttribute("data-status");
      api("/api/conversations/" + c.wa_id + "/outcome", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ outcome: c.outcome === want ? null : want }),
      }).then(load);
    });
  });

  document.getElementById("d-mark").addEventListener("click", function () {
    var c = selected();
    if (!c) return;
    var input = window.prompt("Amount quoted to " + c.name + " (" + cur() + "). Optional — leave blank to skip.",
                              c.quoted_amount || "");
    if (input === null) return;
    var clean = parseInt(String(input).replace(/[^0-9]/g, ""), 10);
    api("/api/conversations/" + c.wa_id + "/amount", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount: isNaN(clean) ? null : clean }),
    }).then(load);
  });

  document.getElementById("d-delete").addEventListener("click", function () {
    var c = selected();
    if (!c) return;
    // Deliberately blunt wording. This is not an archive and there is no undo.
    // Escape line breaks twice in this file: it is a Python string first, and a
    // real newline inside a JS literal takes the whole dashboard down.
    if (!window.confirm(
          "Permanently delete every message and record for " + c.name + "?\\n\\n" +
          "This cannot be undone. If they message you again a new conversation " +
          "starts from scratch. Backup copies are removed within 30 days."
        )) return;
    api("/api/conversations/" + c.wa_id, { method: "DELETE" }).then(function () {
      selectedId = null;
      return load();
    });
  });

  load();
  window.setInterval(load, 20000);   // new messages arrive by webhook; poll to reflect them
})();
</script>
"""


# The demo stylesheet has no import banner - the demo never backfills. Appended
# rather than added to the demo so the two files stay renderable side by side.
EXTRA_STYLE = """
<style>
  .importing {
    display: flex; align-items: center; gap: .55rem;
    margin: 0 0 .75rem;
    padding: .6rem .85rem; border-radius: 8px;
    background: var(--surface-2); border: 1px solid var(--rule);
    color: var(--fg-muted); font-size: var(--step--1);
  }
  .importing[hidden] { display: none; }
  .linkish {
    font: inherit; color: var(--accent); background: none; border: 0;
    padding: 0; cursor: pointer; text-decoration: underline;
  }
</style>
"""


def _check_script() -> None:
    """Syntax-check the JS before writing it.

    This file is a Python string, so a `\\n` typed as `\n` becomes a real
    newline, breaks the JS literal, and takes the *whole* script down - the page
    still renders, it simply never loads any data. That failure looks like a
    server problem and is invisible to the Python tests. Skipped silently if
    node is unavailable; a missing linter must not block a build.
    """
    import shutil
    import subprocess
    import tempfile

    node = shutil.which("node")
    if not node:
        return

    body = SCRIPT.split("<script>", 1)[-1].rsplit("</script>", 1)[0]
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                     encoding="utf-8") as fh:
        fh.write(body)
        path = fh.name

    result = subprocess.run([node, "--check", path], capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit("dashboard JS is broken:\n" + (result.stderr or "").strip())


def main() -> None:
    html = SOURCE.read_text(encoding="utf-8")
    style = re.search(r"<style>.*?</style>", html, re.S)
    if not style:
        raise SystemExit("no <style> block found in " + str(SOURCE))

    _check_script()
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(
        "<!doctype html>\n<html lang=\"en\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        "<title>QuoteRadar</title>\n"
        + style.group(0) + EXTRA_STYLE
        + "\n</head>\n<body>\n" + BODY + SCRIPT + "\n</body>\n</html>\n",
        encoding="utf-8",
    )
    print("wrote", TARGET, TARGET.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
