#!/usr/bin/env python3
"""Build the enterlabs static site from content.json into dist/ and write CONTENT.md."""
from __future__ import annotations

import json
import shutil
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
CONTENT = json.loads((ROOT / "content.json").read_text(encoding="utf-8"))
SITE = CONTENT["site"]
PAGES = CONTENT["pages"]
LEGAL = json.loads((ROOT / "legal.json").read_text(encoding="utf-8"))


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def device(src: str, alt: str, w: int = 1600, h: int = 1200, extra_class: str = "", caption: str | None = None) -> str:
    return f'''<figure class="device {extra_class}">
  <div class="device-bar" aria-hidden="true"><b></b><b></b><b></b><span class="url">{esc(SITE["device_url"])}</span></div>
  <img src="{esc(src)}" alt="{esc(alt)}" width="{w}" height="{h}">
</figure>'''


def device_shell(inner: str, extra_class: str = "") -> str:
    return f'''<figure class="device {extra_class}">
  <div class="device-bar" aria-hidden="true"><b></b><b></b><b></b><span class="url">{esc(SITE["device_url"])}</span></div>
  <div class="device-body">{inner}</div>
</figure>'''


def _svg_ico(name: str) -> str:
    icons = {
        "docs": '<rect x="6" y="4" width="12" height="16" rx="2"/><path d="M9 9h6M9 12h6M9 15h4"/>',
        "inbox": '<rect x="4" y="6" width="16" height="13" rx="2"/><path d="M4 11h4.5l1.5 2h4l1.5-2H20"/>',
        "review": '<circle cx="12" cy="12" r="8"/><path d="M8.5 12.5l2.5 2.5 4.5-5"/>',
        "log": '<path d="M7 5h10M7 10h10M7 15h7"/><path d="M5 4v16"/>',
        "user": '<circle cx="12" cy="9" r="3.2"/><path d="M6 19c.8-3 2.8-4.5 6-4.5s5.2 1.5 6 4.5"/>',
        "email": '<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M4 7l8 6 8-6"/>',
        "upload": '<path d="M12 16V7"/><path d="M8 11l4-4 4 4"/><path d="M5 19h14"/>',
        "scan": '<path d="M5 8V5h3M16 5h3v3M19 16v3h-3M8 19H5v-3"/><rect x="8" y="8" width="8" height="8" rx="1"/>',
        "export": '<rect x="4" y="4" width="10" height="16" rx="1.5"/><path d="M14 10h6m0 0l-2.5-2.5M20 10l-2.5 2.5"/>',
        "core": '<rect x="5" y="5" width="14" height="14" rx="3"/><path d="M9 9h6v6H9z"/>',
        "api": '<path d="M8 12h8"/><circle cx="8" cy="12" r="2.5"/><circle cx="16" cy="12" r="2.5"/><path d="M16 9.5V7M16 14.5V17"/>',
        "systems": '<rect x="3" y="8" width="7" height="10" rx="1.2"/><rect x="14" y="4" width="7" height="14" rx="1.2"/>',
        "redact": '<rect x="4" y="6" width="16" height="12" rx="2"/><path d="M8 12h8"/>',
        "flag": '<path d="M6 20V5"/><path d="M6 5h11.5l-2.8 3.6 2.8 3.6H6z" fill="currentColor" stroke="none"/>',
    }
    return (
        f'<svg class="ico" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
        f'<g fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{icons[name]}</g></svg>'
    )


def product_app(view: str, label: str, animate: bool = False) -> str:
    """Industry-neutral HTML product workspace: invoice matched to a PO and delivery note."""
    m = SITE["product_screen"]
    stats = []
    for s in m["stats"]:
        stats.append(
            f'<div class="ps-stat ps-stat-{esc(s["kind"])}">'
            f'{_svg_ico("flag") if s["kind"]=="flag" else ""}'
            f'<div><b>{esc(s["value"])}</b><small>{esc(s["label"])}</small></div></div>'
        )
    fields = []
    for n, f in enumerate(m["fields"]):
        chip = '<span class="chip chip-match">Match</span>' if f["ok"] else '<span class="chip chip-review">Review</span>'
        slug = "supplier" if n == 0 else "date" if n == 1 else "lines"
        fields.append(
            f'<li data-field="{slug}"><div><b>{esc(f["label"])}</b><span>{esc(f["value"])}</span></div>'
            f'<small>{esc(f["confidence"])}</small>{chip}</li>'
        )
    ths = "".join(f'<th scope="col">{esc(col)}</th>' for col in m["cols"])
    rows = []
    for r in m["rows"]:
        flag = r.get("flag")
        cells = []
        for i, v in enumerate(r["v"]):
            cls = ' class="cell-flag"' if flag is not None and i == flag else ""
            cells.append(f"<td{cls}>{esc(v)}</td>")
        if flag is not None:
            res = '<span class="chip chip-review chip-mismatch">Mismatch</span>'
        else:
            res = '<span class="chip chip-match">Match</span>'
        rows.append(
            f'<tr{" class=\"row-flag\"" if flag is not None else ""}>'
            f'<th scope="row">{esc(r["item"])}</th>{"".join(cells)}<td>{res}</td></tr>'
        )
    finding = m["finding"]
    prev = m["preview"]
    header = prev.get("header") or prev.get("lines") or []
    head_bits = []
    for i, line in enumerate(header):
        hot = ""
        if i == 0:
            hot = ' class="ps-hot" data-hot="supplier"'
        elif line.startswith("Date"):
            rest = line[4:].lstrip()
            head_bits.append(
                f'<p>Date <span class="ps-hot" data-hot="date">{esc(rest)}</span></p>'
            )
            continue
            hot = ' class="ps-hot" data-hot="date"'
        head_bits.append(f"<p{hot}>{esc(line)}</p>")
    doc_head = "".join(head_bits)
    doc_items = ""
    if prev.get("items"):
        lis = []
        for j, it in enumerate(prev["items"]):
            lis.append(
                f'<li><span>{esc(it["item"])}</span><span>{esc(it["qty"])}</span><span>{esc(it["amount"])}</span></li>'
            )
        if prev.get("total"):
            total = (
                f'<p class="ps-doc-total"><span class="ps-hot" data-hot="amount">'
                f'Total {esc(prev["total"])}</span></p>'
            )
        else:
            total = ""
        first_item_mark = ""
        doc_items = f'<ul class="ps-doc-lines" data-hot="lines">{"".join(lis)}</ul>{total}'
    extras = ""
    if animate:
        extras = (
            '<span class="ps-stamp ps-hot" data-hot="stamp" aria-hidden="true">Received</span>'
            '<span class="ps-tip" data-tip="supplier">Supplier</span>'
            '<span class="ps-tip" data-tip="date">Invoice date</span>'
            '<span class="ps-tip" data-tip="lines">Lines</span>'
            '<span class="ps-box" hidden aria-hidden="true"></span>'
        )
    doc_lines = doc_head + doc_items + extras
    audit = "".join(
        f'<li><time>{esc(a["time"])}</time><span>{esc(a["text"])}</span></li>'
        for a in m["audit"]
    )
    nav = "".join(
        f'<span class="ps-nav{" is-on" if name=="docs" else ""}">{_svg_ico(name)}</span>'
        for name in ("docs", "inbox", "review", "log", "user")
    )
    docs = " · ".join(m["documents"])
    ctrl = ""
    if animate:
        ctrl = (
            '<div class="ps-control">'
            '<div class="ps-ctrl-row"><span>Document check</span>'
            '<span class="ps-status is-wait">Awaiting review</span></div>'
            '<p class="ps-metric"><b data-count-from="2" data-count-to="3">2</b> of 3 lines matched</p>'
            '<button type="button" class="ps-fwd" tabindex="-1">Forward to approver</button>'
            '</div>'
        )
    inner = f'''<div class="pscreen{" is-live" if animate else ""}" data-view="{esc(view)}" aria-label="{esc(label)}">
  <div class="pscreen-inner">
    <div class="ps-app">
      <aside class="ps-rail" aria-hidden="true">
        <img class="ps-mark" src="/assets/brand/enterlabs-mark.png" alt="" width="28" height="28">
        <div class="ps-navs">{nav}</div>
      </aside>
      <div class="ps-main">
        <div class="ps-head">
          <div>
            <div class="ps-idrow"><h3 class="ps-id">{esc(m["id"])}</h3><span class="chip chip-status">{esc(m["status"])}</span></div>
            <p class="ps-meta">{esc(m["workspace"])} · {esc(m["supplier"])} · {esc(docs)}</p>
          </div>
        </div>
        <div class="ps-stats">{"".join(stats)}</div>
        <div class="ps-grid">
          <div class="ps-stack">
            <section class="ps-card" data-panel="extract">
              <div class="ps-card-h"><h4>Extracted fields</h4></div>
              <ul class="ps-fields">{"".join(fields)}</ul>
            </section>
            <section class="ps-card" data-panel="exception">
              <div class="ps-card-h"><h4>Line item check</h4><span class="chip chip-review">Needs review</span></div>
              <div class="mock-table-wrap"><table class="mock-table">
                <thead><tr><th scope="col">Item</th>{ths}<th scope="col">Result</th></tr></thead>
                <tbody>{"".join(rows)}</tbody>
              </table></div>
              <div class="mock-reason"><p class="mock-reason-h">{esc(finding["item"])} · {esc(finding["kind"])}</p><p>{esc(finding["text"])}</p></div>
            </section>
          </div>
          <div class="ps-stack">
            <section class="ps-card ps-preview" data-panel="preview">
              <div class="ps-card-h"><h4>{esc(m["preview"]["title"])}</h4></div>
              <div class="ps-doc">{doc_lines}</div>
            </section>
            <section class="ps-card ps-audit" data-panel="audit">
              <div class="ps-card-h"><h4>Audit log</h4></div>
              <ol class="ps-log">{audit}</ol>
              {ctrl}
            </section>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>'''
    return device_shell(inner)


def systems_flow(p: dict) -> str:
    sources = "".join(
        f'<div class="flow-source"><span class="flow-ico">{_svg_ico({"email":"email","uploads":"upload","scans":"scan","exports":"export"}[s["id"]])}</span>'
        f'<span>{esc(s["label"])}</span></div>'
        for s in p["systems_sources"]
    )
    modes = p["systems_modes"]
    tabs = []
    copies = []
    for i, mode in enumerate(modes):
        selected = "true" if i == 0 else "false"
        tabs.append(
            f'<button type="button" class="flow-tab" role="tab" id="flow-tab-{esc(mode["id"])}" '
            f'aria-selected="{selected}" aria-controls="flow-board" data-mode="{esc(mode["id"])}">{esc(mode["label"])}</button>'
        )
        hidden = "" if i == 0 else " hidden"
        copies.append(
            f'<p class="flow-mode-p" data-mode-copy="{esc(mode["id"])}"{hidden}>{esc(mode["p"])}</p>'
        )
    first = modes[0]
    return f'''<div class="flow reveal" data-flow>
  <p class="flow-toggle-label" id="flow-toggle-label">{esc(p["systems_toggle_label"])}</p>
  <div class="flow-toggle" role="tablist" aria-labelledby="flow-toggle-label">
    {"".join(tabs)}
  </div>
  {"".join(copies)}
  <div class="flow-board" id="flow-board" role="tabpanel" aria-labelledby="flow-tab-{esc(first["id"])}" data-mode="{esc(first["id"])}">
    <div class="flow-track">
      <div class="flow-group" aria-label="Documents in">{sources}</div>
      <span class="flow-arrow" aria-hidden="true"></span>
      <div class="flow-node flow-redact" data-hybrid-only>
        <span class="flow-ico">{_svg_ico("redact")}</span>
        <strong>{esc(p["systems_node_redact"])}</strong>
      </div>
      <span class="flow-arrow" data-hybrid-only aria-hidden="true"></span>
      <div class="flow-node flow-core">
        <span class="flow-ico"><img class="flow-mark" src="/assets/brand/enterlabs-mark.png" alt="" width="18" height="18"></span>
        <strong>{esc(p["systems_node_enterlabs"])}</strong>
      </div>
      <span class="flow-arrow" aria-hidden="true"></span>
      <div class="flow-node">
        <span class="flow-ico">{_svg_ico("api")}</span>
        <strong>{esc(p["systems_node_out"])}</strong>
      </div>
      <span class="flow-arrow" aria-hidden="true"></span>
      <div class="flow-node">
        <span class="flow-ico">{_svg_ico("systems")}</span>
        <strong>{esc(p["systems_node_systems"])}</strong>
      </div>
    </div>
  </div>
</div>'''


def industry_picker(picker_id: str, options: list[dict], label: str) -> str:
    first = options[0]
    opts = []
    panels = []
    for i, o in enumerate(options):
        selected = "true" if i == 0 else "false"
        opts.append(
            f'<li role="option" id="{esc(picker_id)}-opt-{esc(o["id"])}" data-ind="{esc(o["id"])}" '
            f'aria-selected="{selected}">{esc(o["label"])}</li>'
        )
        hidden = "" if i == 0 else " hidden"
        kicker = f'<p class="kicker">{esc(o["kicker"])}</p>' if o.get("kicker") else ""
        docs = f'<p class="ind-docs">{esc(o["docs"])}</p>' if o.get("docs") else ""
        problem = f'<p class="ind-problem">{esc(o["problem"])}</p>' if o.get("problem") else ""
        checks = ""
        if o.get("checks"):
            items = "".join(f"<li>{esc(ch)}</li>" for ch in o["checks"])
            checks = f'<p class="ind-checks-label">Example checks</p><ul class="ind-checks">{items}</ul>'
        note = f'<p class="ind-note">{esc(o["note"])}</p>' if o.get("note") else ""
        link = (
            f'<a class="more" href="{esc(o["href"])}">{esc(o["link"])}</a>'
            if o.get("href") and o.get("link") else ""
        )
        page_link = (
            f'<a class="more" href="{esc(o["page_href"])}">{esc(o["page_link"])}</a>'
            if o.get("page_href") and o.get("page_link") else ""
        )
        links = f'<div class="ind-links">{page_link}{link}</div>' if (page_link or link) else ""
        panels.append(
            f'<div class="ind-panel" data-ind="{esc(o["id"])}"{hidden}>'
            f'{kicker}<h3>{esc(o["label"])}</h3>{docs}{problem}{checks}{note}{links}</div>'
        )
    return f'''<div class="ind-picker reveal" id="{esc(picker_id)}">
  <p class="ind-picker-label" id="{esc(picker_id)}-label">{esc(label)}</p>
  <div class="ind-combo">
    <button type="button" class="ind-trigger" aria-haspopup="listbox" aria-expanded="false" aria-controls="{esc(picker_id)}-list" aria-labelledby="{esc(picker_id)}-label {esc(picker_id)}-value" id="{esc(picker_id)}-button">
      <span class="ind-value" id="{esc(picker_id)}-value">{esc(first["label"])}</span>
      <span class="ind-chevron" aria-hidden="true"></span>
    </button>
    <ul class="ind-list" id="{esc(picker_id)}-list" role="listbox" aria-labelledby="{esc(picker_id)}-label" hidden>
      {"".join(opts)}
    </ul>
  </div>
  {"".join(panels)}
</div>'''


def clients_wall(label: str | None = None) -> str:
    label = label or SITE["logo_strip_label"]
    cells = []
    for c in SITE["clients"]:
        if c.get("wordmark"):
            slug = re.sub(r"[^a-z0-9]+", "-", c["wordmark"].lower()).strip("-")
            cells.append(f'<li><span class="wm wm-{slug}" role="img" aria-label="{esc(c["alt"])}">{esc(c["wordmark"])}</span></li>')
        else:
            # Visual size is normalised by ink area, so wide and tall marks read at the same weight.
            ar = c["w"] / c["h"]
            h = max(22, min(34, round((3300 / ar) ** 0.5)))
            w = round(h * ar)
            cells.append(f'<li><img src="{esc(c["src"])}" alt="{esc(c["alt"])}" width="{w}" height="{h}" loading="lazy"></li>')
    return f'''<section class="clients" aria-label="{esc(label)}">
  <div class="wrap">
    <p class="mono-label reveal">{esc(label)}</p>
    <ul class="client-wall" data-motion="logos">{"".join(cells)}</ul>
  </div>
</section>'''


def stats_strip(items: list) -> str:
    cells = []
    for it in items:
        raw = it["num"]
        if it.get("small"):
            num = f'<span class="iso">{esc(raw)}</span>'
        else:
            i = 0
            while i < len(raw) and raw[i].isdigit():
                i += 1
            head, tail = raw[:i], raw[i:]
            num = f'<span data-count="{esc(head)}">{esc(head)}</span>{esc(tail)}'
            if it.get("sup"):
                num += f'<sup>{esc(it["sup"])}</sup>'
            if it.get("unit"):
                num += f' <span class="unit">{esc(it["unit"])}</span>'
        cells.append(f'<div class="stat"><p class="stat-num">{num}</p><p class="stat-cap">{esc(it["cap"])}</p></div>')
    return f'''<section class="stats" data-motion="stats" aria-label="enterlabs in numbers">
  <div class="wrap"><div class="stats-row">{"".join(cells)}</div></div>
</section>'''


def logo_row(label: str | None = None) -> str:
    return clients_wall(label)


def quotes_head(h2: str, kicker: str | None = None, link: dict | None = None) -> str:
    kicker_html = f'<p class="kicker">{esc(kicker)}</p>\n      ' if kicker else ""
    pill = ""
    if link:
        pill = (
            f'<a class="voices-pill" href="{esc(link["href"])}">{esc(link["label"])}</a>'
        )
    return f'''<div class="voices-head reveal">
    <div>
      {kicker_html}<h2>{esc(h2)}</h2>
    </div>
    {pill}
  </div>'''


def proof_metrics(metrics: list, extra_class: str = "") -> str:
    items = "".join(
        f'<li><strong>{esc(m["value"])}</strong><span>{esc(m["label"])}</span></li>'
        for m in metrics
    )
    n = len(metrics)
    cls = f"proof-metrics cols-{n}" + (f" {extra_class}" if extra_class else "")
    return f'<ul class="{cls}">{items}</ul>'


def cases_html() -> str:
    cards = []
    for q in SITE["quotes"]:
        logos = "".join(
            f'<img class="proof-client-logo" src="{esc(src)}" alt="" width="160" height="48">'
            for src in q.get("client_logos") or []
        )
        portrait = (
            f'<img class="proof-portrait" src="{esc(q["img"])}" alt="{esc(q["name"])}" width="80" height="100">'
            if q.get("img")
            else ""
        )
        cards.append(f'''<article class="proof-card reveal" id="{esc(q["id"])}">
  <header class="proof-top">
    <p class="proof-tag">{esc(q["tag"])}</p>
    <div class="proof-client">{logos}<p class="proof-client-name">{esc(q["client"])}</p></div>
  </header>
  <h3 class="proof-headline">{esc(q["headline"])}</h3>
  <div class="proof-cols">
    <div>
      <h4>Challenge</h4>
      <p>{esc(q["challenge"])}</p>
    </div>
    <div>
      <h4>What we did</h4>
      <p>{esc(q["did"])}</p>
    </div>
    <div class="proof-scale">
      <h4>Scale</h4>
      <p class="proof-scale-value">{esc(q["scale_value"])}</p>
      <p>{esc(q["scale_caption"])}</p>
    </div>
  </div>
  {proof_metrics(q["metrics"])}
  <figure class="proof-quote">
    {portrait}
    <div>
      <blockquote>“{esc(q["text"])}”</blockquote>
      <p class="who"><strong>{esc(q["name"])}</strong>{esc(q["role"])}</p>
    </div>
  </figure>
  <p class="proof-more"><a href="{esc(q["story_path"])}">Read the full story</a></p>
</article>''')
    foot = SITE.get("cases_footnote") or ""
    foot_html = f'<p class="proof-foot">{esc(foot)}</p>' if foot else ""
    return f'<div class="proof-list">{"".join(cards)}</div>{foot_html}'


def quotes_html(note: str | None = None, compact: bool = False) -> str:
    blocks = []
    arrow = (
        '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false">'
        '<path d="M7 17L17 7M8 7h9v9" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round"/></svg>'
    )
    for q in SITE["quotes"]:
        vid = esc(q.get("id") or q["name"].lower().replace(" ", "-"))
        href = esc(q.get("story_path") or f"/customers/{vid}/")
        label = q.get("customer") or q.get("client") or q["name"]
        stat = ""
        if q.get("hover_value"):
            stat = (
                f'<span class="voice-stat">'
                f'<strong>{esc(q["hover_value"])}</strong>'
                f'<span>{esc(q["hover_caption"])}</span>'
                f"</span>"
            )
        blocks.append(
            f'<a class="voice reveal" href="{href}">'
            f'<div class="voice-stage">'
            f'<img class="voice-cover" src="{esc(q["cover"])}" alt="" width="1200" height="1200">'
            f'<span class="voice-shade"></span>'
            f'<img class="voice-logo" src="{esc(q["logo"])}" alt="" width="400" height="160">'
            f'<span class="voice-go" aria-hidden="true">{arrow}</span>'
            f"{stat}"
            f"</div>"
            f'<span class="voices-sr">Read the {esc(label)} story</span>'
            f"</a>"
        )
    note_html = f'<p class="note reveal">{esc(note)}</p>' if note else ""
    foot = ""
    if compact and SITE.get("cases_footnote"):
        foot = f'<p class="proof-foot">{esc(SITE["cases_footnote"])}</p>'
    return note_html + f'<div class="voices-grid">{"".join(blocks)}</div>' + foot


def build_story(q: dict) -> str:
    logos = "".join(
        f'<img class="cs-hero-logo" src="{esc(src)}" alt="" width="200" height="64">'
        for src in q.get("client_logos") or []
    )
    stats = "".join(
        f'<li><strong>{esc(s["value"])}</strong><span>{esc(s["label"])}</span></li>'
        for s in q["hero_stats"]
    )
    fields = [
        ("Company name", q["company_name"]),
        ("Industry", q["industry_label"]),
        ("Use case", q["use_case"]),
        ("Customer", q["customer"]),
    ]
    fields_html = "".join(
        f'<div class="cs-field"><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in fields
    )
    steps = "".join(
        f'<li><h3><span class="cs-step-n">{i}</span>{esc(s["h"])}</h3><p>{esc(s["p"])}</p></li>'
        for i, s in enumerate(q["steps"], 1)
    )
    rows = "".join(
        f'<tr><th scope="row">{esc(m["label"])}</th><td>{esc(m["value"])}</td></tr>'
        for m in q["metrics"]
    )
    portrait = (
        f'<img class="cs-quote-photo" src="{esc(q["img"])}" alt="{esc(q["name"])}" width="80" height="100">'
        if q.get("img")
        else ""
    )
    footnote = esc(SITE.get("cases_footnote") or "")
    email = esc(SITE["email"])
    ldquo = "\u201c"
    rdquo = "\u201d"
    body = (
        f'<article class="cs">'
        f'<header class="cs-hero"><div class="wrap">'
        f'<p class="cs-crumb"><a href="/customers/">Customers</a></p>'
        f'<div class="cs-hero-card">'
        f'<div class="cs-hero-photo">'
        f'<img src="{esc(q["cover"])}" alt="" width="1200" height="480">'
        f'<span class="cs-hero-shade"></span>'
        f"</div>"
        f'<div class="cs-hero-body">'
        f'<div class="cs-hero-meta">'
        f'<span class="cs-tag">{esc(q["tag"])}</span>'
        f'<span class="cs-date">{esc(q["period"])}</span>'
        f"</div>"
        f'<div class="cs-hero-title">'
        f"<h1>{esc(q['headline'])}</h1>"
        f'<div class="cs-hero-logos">{logos}</div>'
        f"</div>"
        f'<ul class="cs-hero-stats">{stats}</ul>'
        f"</div></div></div></header>"
        f'<div class="wrap cs-layout">'
        f'<aside class="cs-side">'
        f'<nav class="cs-index" aria-label="In this story">'
        f'<p class="cs-index-label">Index</p>'
        f'<a href="#overview">Company overview</a>'
        f'<a href="#challenge">The challenge</a>'
        f'<a href="#solution">What we built</a>'
        f'<a href="#roi">Measurable ROI</a>'
        f'<a href="#next">Looking ahead</a>'
        f"</nav>"
        f'<div class="cs-side-cta">'
        f'<p class="cs-index-label">Get started</p>'
        f"<p>Turn documents into confident decisions.</p>"
        f'<a class="btn btn-primary" href="/book-a-demo/">Book a demo</a>'
        f'<a class="cs-side-mail" href="mailto:{email}">{email}</a>'
        f"</div></aside>"
        f'<div class="cs-main">'
        f'<section class="cs-section" id="overview">'
        f"<h2>Company overview</h2>"
        f'<dl class="cs-fields">{fields_html}</dl>'
        f'<p class="cs-about"><strong>About the company.</strong> {esc(q["about"])}</p>'
        f"</section>"
        f'<figure class="cs-quote">{portrait}<div>'
        f"<blockquote>{ldquo}{esc(q['text'])}{rdquo}</blockquote>"
        f'<p class="who"><strong>{esc(q["name"])}</strong>{esc(q["role"])}</p>'
        f"</div></figure>"
        f'<section class="cs-section" id="challenge">'
        f"<h2>{esc(q['challenge_h'])}</h2>"
        f"<p>{esc(q['challenge_body'])}</p>"
        f"</section>"
        f'<section class="cs-section" id="solution">'
        f"<h2>{esc(q['solution_h'])}</h2>"
        f"<p>{esc(q['solution_lead'])}</p>"
        f'<ol class="cs-steps">{steps}</ol>'
        f"</section>"
        f'<section class="cs-section" id="roi">'
        f"<h2>Measurable ROI</h2>"
        f"<p>{footnote}</p>"
        f'<div class="cs-table-wrap"><table class="cs-table">'
        f"<thead><tr><th scope=\"col\">Metric</th><th scope=\"col\">Result</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></div>"
        f"</section>"
        f'<section class="cs-section" id="next">'
        f"<h2>{esc(q['next_h'])}</h2>"
        f"<p>{esc(q['next_body'])}</p>"
        f"</section>"
        f"</div></div></article>"
        + closing(
            PAGES["home"]["close_h2"],
            PAGES["home"]["close_lead"],
            {"label": "Book a demo", "href": "/book-a-demo/"},
            {"label": SITE["email"], "href": "mailto:" + SITE["email"]},
        )
    )
    return layout(q["story_title"], q["story_description"], q["story_path"], body)

def investors_block(kicker: str, heading: str, lead: str | None = None) -> str:
    figs = []
    for i, inv in enumerate(SITE["investors"]):
        if i:
            figs.append('<span class="backed-rule" aria-hidden="true"></span>')
        src = inv.get("src_on_dark") or inv["src"]
        figs.append(
            f'<figure><img src="{esc(src)}" alt="{esc(inv["alt"])}" width="{inv["w"]}" height="{inv["h"]}"></figure>'
        )
    lead_html = f'<p class="backed-lead">{esc(lead)}</p>' if lead else ""
    return f'''<section class="backed-band" id="investors">
  <div class="wrap backed reveal">
    <div class="backed-copy">
      <p class="kicker">{esc(kicker)}</p>
      <h2>{esc(heading)}</h2>
      {lead_html}
    </div>
    <div class="inv">{"".join(figs)}</div>
  </div>
</section>'''


def orbs(n: int = 3) -> str:
    return ""


def actions(*btns: dict, extra_class: str = "") -> str:
    parts = []
    for i, b in enumerate(btns):
        cls = "btn btn-primary" if i == 0 else "btn btn-ghost"
        parts.append(f'<a class="{cls}" href="{esc(b["href"])}">{esc(b["label"])}</a>')
    return f'<div class="actions {extra_class}">{"".join(parts)}</div>'


DOC_CARDS = """<div class="docs" aria-hidden="true">
  <div class="doc doc-id"><i class="ph"></i><b></b><b></b><b></b><b></b></div>
  <div class="doc doc-table"><b></b><b></b><b></b><b></b><b></b><b></b></div>
  <div class="doc doc-receipt"><b></b><b></b><b></b><b></b><b></b></div>
  <div class="doc doc-form"><b></b><b></b><b></b><b></b></div>
</div>"""


def closing(h2: str, lead: str, primary: dict, secondary: dict | None = None) -> str:
    btns = [primary] + ([secondary] if secondary else [])
    return f'''<section class="closing" data-motion="float">
  {DOC_CARDS}
  <div class="wrap reveal closing-inner">
    <img class="closing-logo" src="/assets/brand/enterlabs-logo.svg" alt="enterlabs" width="168" height="39">
    <h2>{esc(h2)}</h2>
    <span class="rule" aria-hidden="true"></span>
    <p class="lead">{esc(lead)}</p>
    {actions(*btns)}
  </div>
</section>'''


def page_hero(p: dict, extra: str = "") -> str:
    return f'''<section class="page-hero">
  {orbs()}
  <div class="wrap">
    <p class="kicker">{esc(p["kicker"])}</p>
    <h1>{esc(p["h1"])}</h1>
    <p class="lead">{esc(p["lead"])}</p>
    {extra}
  </div>
</section>'''


def nav_html(current: str) -> str:
    out = []
    for gi, item in enumerate(SITE["nav"]):
        href = item["href"]
        kids = item.get("children")
        match = item.get("match") or [href]
        is_cur = any(current.startswith(m) for m in match if m != "/") or current == href
        if not kids:
            cur = ' aria-current="page"' if is_cur else ""
            out.append(f'<a href="{esc(href)}"{cur}>{esc(item["label"])}</a>')
            continue
        mid = "menu-" + item["label"].lower().replace(" ", "-")
        cur = ' data-current="true"' if is_cur else ""
        lis = []
        for k in kids:
            kc = ' aria-current="page"' if current.rstrip("/") == k["href"].rstrip("/") else ""
            desc = f'<span>{esc(k["desc"])}</span>' if k.get("desc") else ""
            lis.append(f'<li><a href="{esc(k["href"])}"{kc}><strong>{esc(k["label"])}</strong>{desc}</a></li>')
        if item.get("all"):
            a = item["all"]
            ac = ' aria-current="page"' if current.rstrip("/") == a["href"].rstrip("/") else ""
            lis.append(f'<li class="nav-all"><a href="{esc(a["href"])}"{ac}>{esc(a["label"])}<span aria-hidden="true"> &rarr;</span></a></li>')
        align = " align-right" if gi >= len(SITE["nav"]) - 2 else ""
        out.append(
            f'<div class="nav-group{align}"{cur}>'
            f'<button type="button" class="nav-trigger" aria-expanded="false" aria-controls="{mid}">{esc(item["label"])}<span class="nav-chevron" aria-hidden="true"></span></button>'
            f'<div class="nav-menu" id="{mid}" hidden><ul>{"".join(lis)}</ul></div></div>'
        )
    cta = SITE["cta"]
    cta_current = ' aria-current="page"' if current.startswith("/book-a-demo") else ""
    out.append(f'<a class="btn btn-primary" href="{esc(cta["href"])}"{cta_current}>{esc(cta["label"])}</a>')
    return "\n      ".join(out)


def layout(title: str, description: str, path: str, body: str) -> str:
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="{esc(SITE["meta_robots"])}">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="icon" href="/assets/brand/favicon-32.png" type="image/png">
<link rel="apple-touch-icon" href="/assets/brand/apple-touch-icon.png">
<link rel="stylesheet" href="/css/styles.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header>
  <div class="wrap nav">
    <a class="brand" href="/"><img src="/assets/brand/enterlabs-logo.svg" alt="enterlabs" width="150" height="35"></a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="nav-panel">Menu</button>
    <nav class="nav-panel" id="nav-panel" aria-label="Primary">
      {nav_html(path)}
    </nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer>
  <div class="wrap foot">
    <div class="foot-grid">
      <div class="foot-col foot-brand">
        <a class="brand" href="/"><img src="/assets/brand/enterlabs-logo.svg" alt="enterlabs" width="140" height="32"></a>
        <p>{esc(SITE["footer_tagline"])}</p>
      </div>
      <nav class="foot-col" aria-label="Footer">
        <h4>Explore</h4>
        {"".join(f'<a href="{esc(i["href"])}">{esc(i["label"])}</a>' for i in SITE["footer_explore"])}
      </nav>
      <div class="foot-col">
        <h4>Contact</h4>
        <a href="mailto:{esc(SITE["email"])}">{esc(SITE["email"])}</a>
        <a href="{esc(SITE["cta"]["href"])}">{esc(SITE["cta"]["label"])}</a>
      </div>
      {"".join('<div class="foot-col foot-office"><h4>' + esc(o["city"]) + '</h4>' + "".join('<span>' + esc(l) + '</span>' for l in o["lines"]) + '</div>' for o in SITE["footer_offices"])}
    </div>
    <div class="foot-base"><span>&copy; 2026 enterlabs. All rights reserved.</span>
      <nav class="foot-legal" aria-label="Legal">{"".join(f'<a href="{esc(i["href"])}">{esc(i["label"])}</a>' for i in SITE["footer_legal"])}</nav>
    </div>
  </div>
</footer>
<script src="/js/site.js"></script>
</body>
</html>
'''



def doc_wall(p: dict) -> str:
    w = p["doc_wall"]
    return (
        f'<section class="doc-wall" id="documents" aria-label="{esc(w["line1"])} {esc(w["line2"])}">'
        '<div class="wrap"><div class="wall-copy">'
        '<span class="rule wall-rule" aria-hidden="true"></span>'
        '<h2 class="wall-h">'
        f'<span class="wall-line wall-line-lead">{esc(w["line1"])}</span>'
        f'<span class="wall-line wall-line-follow">{esc(w["line2"])}</span>'
        "</h2></div></div></section>"
    )


def build_home() -> str:
    p = PAGES["home"]
    steps = []
    shots = []
    for i, s in enumerate(p["story_steps"]):
        active = "active" if i == 0 else ""
        steps.append(
            f'<article class="story-step {active}" data-step="{i}"><div class="story-step-inner">'
            f'<div class="num">{esc(s["num"])}</div>'
            f'<h3>{esc(s["h"])}</h3><p>{esc(s["p"])}</p></div></article>'
        )
        shots.append(
            f'<div class="story-shot {active}" data-shot="{i}">{product_app(s["view"], s["alt"], animate=True)}</div>'
        )
    cards = "".join(
        f'<article><h3>{esc(c["h"])}</h3><p>{esc(c["p"])}</p></article>' for c in p["problem_cards"]
    )
    trust_items = []
    for t in p["trust_items"]:
        img = (
            f'<img src="{esc(t["img"])}" alt="{esc(t["alt"])}" width="80" height="80">'
            if t.get("img") else ""
        )
        trust_items.append(f'<article>{img}<h3>{esc(t["h"])}</h3><p>{esc(t["p"])}</p></article>')
    hero = f'''<section class="hero">
  {orbs()}
  <div class="wrap">
    <p class="kicker">{esc(p["kicker"])}</p>
    <h1>{esc(p["h1"])} <em>{esc(p["h1_em"])}</em></h1>
    <span class="rule" aria-hidden="true"></span>
    <p class="lead">{esc(p["lead"])}</p>
    {actions(p["primary_cta"], p["secondary_cta"])}
    <div class="hero-visual">
      <div class="hero-parallax">
        {product_app(p["hero_screen"]["view"], p["hero_screen"]["alt"])}
      </div>
    </div>
  </div>
</section>'''
    doors = "".join(
        f'<a class="door reveal" href="{esc(d["href"])}">'
        f'<p class="kicker">{esc(d["kicker"])}</p>'
        f'<h3>{esc(d["h"])}</h3>'
        f'<p>{esc(d["p"])}</p>'
        f'<span class="door-go">{esc(d["label"])}<span aria-hidden="true"> &rarr;</span></span>'
        f"</a>"
        for d in p["doors"]
    )
    products = "".join(
        f'<article class="reveal"><div class="num">{esc(item["num"])}</div>'
        f'<h3>{esc(item["h"])}</h3><p>{esc(item["p"])}</p></article>'
        for item in p["products"]
    )
    body = f'''{hero}
<section class="wrap doors-sec" id="audiences" aria-label="{esc(p["doors_h2"])}">
  <div class="reveal" style="max-width:720px">
    <p class="kicker">{esc(p["doors_kicker"])}</p>
    <h2>{esc(p["doors_h2"])}</h2>
  </div>
  <div class="doors">{doors}</div>
</section>
<section class="wrap" id="products">
  <div class="reveal" style="max-width:740px">
    <p class="kicker">{esc(p["products_kicker"])}</p>
    <h2>{esc(p["products_h2"])}</h2>
    <p class="muted">{esc(p["products_lead"])}</p>
  </div>
  <div class="card-grid">{products}</div>
</section>
{doc_wall(p)}
{stats_strip(p["stats"])}
{clients_wall()}
<section class="problem wrap" id="problem">
  <div class="reveal" style="max-width:720px">
    <p class="kicker">{esc(p["problem_kicker"])}</p>
    <h2>{esc(p["problem_h2"])}</h2>
    <p class="muted">{esc(p["problem_lead"])}</p>
  </div>
  <div class="grid reveal">{cards}</div>
</section>
<div class="story-band" id="story">
  <svg class="circuit circuit-story" viewBox="0 0 200 200" preserveAspectRatio="none" aria-hidden="true">
    <path class="circuit-path" pathLength="1" d="M 16 0 V 64 H 78"/>
  </svg>
  <div class="wrap">
    <div class="reveal" style="max-width:800px">
      <p class="kicker">{esc(p["story_kicker"])}</p>
      <h2>{esc(p["story_h2"])}</h2>
    </div>
    <div class="story-layout">
      <div class="story-steps">{"".join(steps)}</div>
      <div class="story-stage-wrap"><div class="story-stage">{"".join(shots)}</div></div>
    </div>
  </div>
</div>
<section class="wrap" id="industries">
  <div class="reveal" style="max-width:740px">
    <p class="kicker">{esc(p["industries_kicker"])}</p>
    <h2>{esc(p["industries_h2"])}</h2>
    <p class="muted">{esc(p["industries_lead"])}</p>
  </div>
  {industry_picker("industry-picker-home", PAGES["industries"]["options"], p.get("industries_picker_label") or PAGES["industries"]["picker_label"])}
</section>
<section class="wrap voices" id="customers">
  {quotes_head(p["quotes_h2"], p["quotes_kicker"], p.get("quotes_link"))}
  {quotes_html(compact=True)}
</section>
{investors_block(p["investors_kicker"], p["investors_h2"])}
<section class="wrap" id="trust">
  <div class="reveal" style="max-width:720px">
    <p class="kicker">{esc(p["trust_kicker"])}</p>
    <h2>{esc(p["trust_h2"])}</h2>
    <p class="muted">{esc(p["trust_lead"])}</p>
  </div>
  <div class="trust-grid reveal">{"".join(trust_items)}</div>
</section>
<section class="wrap" id="systems">
  <div class="section-head reveal">
    <p class="kicker">{esc(p["systems_kicker"])}</p>
    <h2>{esc(p["systems_h2"])}</h2>
    <p class="muted">{esc(p["systems_lead"])}</p>
  </div>
  {systems_flow(p)}
</section>
{closing(p["close_h2"], p["close_lead"], p["primary_cta"], p["secondary_cta"])}
'''
    return layout(p["title"], p["description"], p["path"], body)


def build_platform() -> str:
    p = PAGES["platform"]
    pillars = []
    for item in p["pillars"]:
        note = f'<p class="note">{esc(item["note"])}</p>' if item.get("note") else ""
        pillars.append(f'''<section class="wrap">
  <div class="split">
    <div class="reveal">
      <p class="kicker">{esc(item["kicker"])}</p>
      <h2>{esc(item["h"])}</h2>
      <p class="muted">{esc(item["p"])}</p>
      {note}
    </div>
    <div class="reveal">{product_app(item["view"], item["alt"])}</div>
  </div>
</section>''')
    deploy = "".join(
        f'<article class="ind-card"><h3>{esc(d["h"])}</h3><p>{esc(d["p"])}</p></article>'
        for d in p["deploy"]
    )
    note = f'<p class="note">{esc(p["integrate_note"])}</p>' if p.get("integrate_note") else ""
    body = f'''{page_hero(p)}
<section class="wrap">
  <p class="muted reveal" style="max-width:740px">{esc(p["intro"])}</p>
</section>
{"".join(pillars)}
<section class="wrap">
  <div class="section-head reveal">
    <p class="kicker">{esc(p["integrate_kicker"])}</p>
    <h2>{esc(p["integrate_h2"])}</h2>
    <p class="muted">{esc(p["integrate_lead"])}</p>
  </div>
  <div class="card-grid two reveal" style="margin-top:36px">{deploy}</div>
  {note}
</section>
{closing(p["close_h2"], p["close_lead"], {"label": "Book a demo", "href": "/book-a-demo/"}, {"label": "See how it works", "href": "/#story"})}
'''
    return layout(p["title"], p["description"], p["path"], body)


def build_industries() -> str:
    p = PAGES["industries"]
    body = f'''{page_hero(p)}
<section class="wrap" id="industries">
  <div class="section-head reveal">
    <h2>{esc(p["reach_h2"])}</h2>
    <p class="muted">{esc(p["reach_lead"])}</p>
  </div>
  {industry_picker("industry-picker-industries", p["options"], p["picker_label"])}
</section>
{closing(p["close_h2"], p["close_lead"], {"label": "Book a demo", "href": "/book-a-demo/"})}
'''
    return layout(p["title"], p["description"], p["path"], body)


def build_health() -> str:
    p = PAGES["health"]
    how = "".join(
        f'<article><h3>{esc(s["h"])}</h3><p>{esc(s["p"])}</p></article>' for s in p["how"]
    )
    body = f'''{page_hero(p)}
<section class="wrap">
  <div class="section-head reveal">
    <h2>{esc(p["who_h2"])}</h2>
    <p class="muted">{esc(p["who_lead"])} <a href="/customers/">See customers</a>.</p>
  </div>
</section>
<section class="wrap">
  <div class="section-head reveal">
    <h2>{esc(p["how_h2"])}</h2>
    <p class="note">{esc(p["qualify"])}</p>
  </div>
  <div class="card-grid reveal">{how}</div>
  <div class="bento">
    <div class="card wide reveal">{device_shell("""<video class="device-video" autoplay muted loop playsinline preload="metadata" poster="/assets/video/claims-demo-poster.jpg" width="1248" height="718" aria-label="Walkthrough of an enterlabs health insurance claims review"><source src="/assets/video/claims-demo.mp4" type="video/mp4"></video>""")}</div>
  </div>
</section>
<section class="wrap">
  <div class="section-head reveal">
    <h2>{esc(p["docs_h2"])}</h2>
    <p class="muted">{esc(p["docs_lead"])}</p>
  </div>
</section>
{closing("Walk through a claim your team already knows.", p["close_lead"], {"label": "Book a demo", "href": "/book-a-demo/"}, {"label": "See the platform", "href": "/platform/"})}
'''
    return layout(p["title"], p["description"], p["path"], body)


def mock_screen(m: dict) -> str:
    """Clean HTML mockup in the style of the product screens."""
    ths = "".join(f'<th scope="col">{esc(c)}</th>' for c in m["cols"])
    rows = []
    for r in m["rows"]:
        flag = r.get("flag")
        cells = []
        for i, v in enumerate(r["v"]):
            cls = ' class="cell-flag"' if flag is not None and i == flag else ""
            cells.append(f"<td{cls}>{esc(v)}</td>")
        if flag is not None:
            res = '<span class="chip chip-review chip-mismatch">Mismatch</span>'
        else:
            res = '<span class="chip chip-match">Match</span>'
        rows.append(f'<tr{" class=row-flag" if flag is not None else ""}><th scope="row">{esc(r["item"])}</th>{"".join(cells)}<td>{res}</td></tr>')
    meta = "".join(f"<span>{esc(x)}</span>" for x in m["meta"])
    f = m["finding"]
    checks = "".join(
        f'<li><span class="chk-ico {"ok" if c["ok"] else "rv"}" aria-hidden="true"></span>'
        f'<div><b>{esc(c["label"])}</b><small>{esc(c["value"])}</small></div>'
        f'<span class="chip {"chip-match" if c["ok"] else "chip-review"}">{"Match" if c["ok"] else "Review"}</span></li>'
        for c in m["checks"]
    )
    label = m.get("ref") or "Document workspace"
    return f'''<figure class="mock" aria-label="{esc(label)}">
  <div class="mock-stage">
    <div class="mock-panel mock-main">
      <p class="mock-crumb">{esc(m["crumb"])} <i>/</i> <b>{esc(m["crumb_active"])}</b></p>
      <div class="mock-title"><h3>{esc(m["ref"])}</h3><span class="chip chip-status">{esc(m["status"])}</span></div>
      <p class="mock-meta">{meta}</p>
      <div class="mock-table-wrap"><table class="mock-table">
        <thead><tr><th scope="col">Item</th>{ths}<th scope="col">Result</th></tr></thead>
        <tbody>{"".join(rows)}</tbody>
      </table></div>
    </div>
    <div class="mock-side">
      <div class="mock-panel mock-finding">
        <div class="mock-title"><h3>Finding</h3><span class="chip chip-review">Needs review</span></div>
        <p class="mock-item"><b>{esc(f["item"])}</b><small>{esc(f["kind"])}</small></p>
        <div class="mock-reason"><p class="mock-reason-h">Why it was flagged</p><p>{esc(f["text"])}</p></div>
        <div class="mock-btns"><span class="mock-btn">Cancel</span><span class="mock-btn mock-btn-dark">Send to reviewer</span></div>
      </div>
      <div class="mock-panel mock-checks">
        <div class="mock-title"><h3>Checks</h3></div>
        <ul>{checks}</ul>
      </div>
    </div>
  </div>
</figure>'''


def build_industry(slug: str) -> str:
    p = PAGES["industry_pages"][slug]
    checks = "".join(f"<article><h3>Check {i}</h3><p>{esc(c)}</p></article>" for i, c in enumerate(p["checks"], 1))
    how = "".join(
        f'<article><div class="num">{i:02d}</div><h3>{esc(s["h"])}</h3><p>{esc(s["p"])}</p></article>'
        for i, s in enumerate(p["how"], 1)
    )
    if p.get("mock"):
        screen = mock_screen(p["mock"])
    else:
        im = p["image"]
        screen = device(im["src"], im["alt"])
    extra = ""
    if p.get("extra_link"):
        extra = f'<p class="note"><a href="{esc(p["extra_link"]["href"])}">{esc(p["extra_link"]["label"])}</a> or see <a href="/customers/">our customers</a>.</p>'
    hero = page_hero(p, actions({"label": "Book a demo", "href": "/book-a-demo/"}, {"label": "All industries", "href": "/industries/"}))
    body = f'''{hero}
<section class="wrap">
  <div class="section-head reveal">
    <h2>{esc(p["problem_h2"])}</h2>
    <p class="muted">{esc(p["problem"])}</p>
    <p class="note">Documents: {esc(p["docs"])}</p>
  </div>
</section>
<section class="wrap" style="padding-top:0">
  <div class="section-head reveal"><h2>{esc(p["checks_h2"])}</h2></div>
  <div class="card-grid reveal">{checks}</div>
</section>
<section class="wrap" style="padding-top:0">
  <div class="section-head reveal"><h2>{esc(p["how_h2"])}</h2></div>
  <div class="card-grid reveal">{how}</div>
</section>
<section class="wrap" id="example" style="padding-top:0">
  <div class="section-head reveal">
    <h2>{esc(p["screen_h2"])}</h2>
    <p class="muted">{esc(p["screen_lead"])}</p>
    {extra}
  </div>
  <div class="reveal">{screen}</div>
</section>
{closing(p["close_h2"], p["close_lead"], {"label": "Book a demo", "href": "/book-a-demo/"})}
'''
    return layout(p["title"], p["description"], p["path"], body)


def build_customers() -> str:
    p = PAGES["customers"]
    body = f'''{page_hero(p)}
{clients_wall()}
<section class="wrap voices">
  {quotes_head(p["quotes_h2"])}
  {cases_html()}
  {f'<p class="note">{esc(p["after"])}</p>' if p.get("after") else ""}
</section>
{closing(PAGES["home"]["close_h2"], PAGES["home"]["close_lead"], {"label": "Book a demo", "href": "/book-a-demo/"})}
'''
    return layout(p["title"], p["description"], p["path"], body)


def _icon(name: str) -> str:
    # Simple line icons for the controls grid. Sized in CSS.
    paths = {
        "lock": '<rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/><path d="M12 14v3"/>',
        "doc": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6M8 13h8M8 17h8"/>',
        "log": '<path d="M3 11a9 9 0 1 1 2.5 7"/><path d="M3 4v7h7"/><path d="M12 7v5l3 2"/>',
        "people": '<circle cx="9" cy="7" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3"/><path d="M16 4a3 3 0 0 1 0 6"/><path d="M18 14a5 5 0 0 1 3 4v3"/>',
        "cloud": '<path d="M7 18h10a4 4 0 0 0 1-7.9 6 6 0 0 0-11.4-1.6A4 4 0 0 0 7 18Z"/>',
        "db": '<ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v8c0 1.7 3.1 3 7 3s7-1.3 7-3V6"/><path d="M5 10c0 1.7 3.1 3 7 3s7-1.3 7-3"/>',
        "user": '<circle cx="12" cy="8" r="3.2"/><path d="M5 19a7 7 0 0 1 14 0"/>',
        "shield": '<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6Z"/>',
    }
    d = paths.get(name, "")
    return (
        f'<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{d}</svg>'
    )


def trust_deploy_mock() -> str:
    rows = [
        ("cloud", "Environment", "Managed cloud", "Managed cloud", "tag-cloud"),
        ("db", "Data processing", "Client environment", "Client environment", "tag-env"),
        ("user", "Access", "Role-based", "Role-based", "tag-role"),
        ("shield", "Review", "Client review required", "Client review required", "tag-review"),
    ]
    lis = []
    for icon, title, sub, tag, cls in rows:
        lis.append(
            f'<li><span class="cfg-ico">{_icon(icon)}</span>'
            f'<div><b>{title}</b><small>{sub}</small></div>'
            f'<span class="cfg-tag {cls}">{tag}</span></li>'
        )
    items = "".join(lis)
    return (
        '<figure class="trust-shot" aria-label="Deployment configuration">'
        '<div class="trust-shot-stage"><div class="cfg-card">'
        '<div class="cfg-head"><strong>Deployment configuration</strong><span aria-hidden="true">...</span></div>'
        f'<ul class="cfg-list">{items}</ul>'
        '<div class="cfg-actions"><span class="cfg-cancel">Cancel</span><span class="cfg-save">Save configuration</span></div>'
        '</div></div></figure>'
    )


def trust_diligence_mock() -> str:
    rows = [
        ("Control evidence", "Security team", "Discuss scope"),
        ("Data handling", "IT and privacy", "Map responsibilities"),
        ("Acceptance", "Operations", "Define criteria"),
    ]
    trs = "".join(f'<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>' for a, b, c in rows)
    return (
        '<figure class="trust-shot" aria-label="Security review">'
        '<div class="trust-shot-stage is-table"><div class="cfg-card dil-card">'
        '<div class="cfg-head"><strong>Security review</strong><span class="cfg-pill">Draft</span></div>'
        '<p class="dil-kicker">Diligence agenda</p>'
        '<h3>Prepare the security discussion</h3>'
        '<p class="dil-sub">Evidence and responsibilities</p>'
        '<table class="dil-table"><thead><tr><th>Review topic</th><th>Owner</th><th>Next step</th></tr></thead>'
        f'<tbody>{trs}</tbody></table>'
        '</div></div></figure>'
    )


def frameworks_html(frameworks: list | None = None) -> str:
    badges = []
    for f in frameworks or PAGES["trust"]["frameworks"]:
        art = " framework-art" if f.get("art") else ""
        inner = (
            f'<img src="{esc(f["img"])}" alt="{esc(f["alt"])}" width="160" height="160" loading="lazy">'
            f'<strong>{esc(f["h"])}</strong>'
            f'<span class="framework-status {esc(f["kind"])}">{esc(f["status"])}</span>'
        )
        if f.get("href"):
            badges.append(f'<a class="framework{art}" href="{esc(f["href"])}">{inner}</a>')
        else:
            badges.append(f'<div class="framework{art}">{inner}</div>')
    return "".join(badges)


def build_trust() -> str:
    p = PAGES["trust"]
    h1 = esc(p["h1"])
    if p.get("h1_line2"):
        h1 += "<br>" + esc(p["h1_line2"])
    badges = frameworks_html()

    deploy = "".join(
        f'<article><h3>{esc(x["h"])}</h3><p>{esc(x["p"])}</p></article>'
        for x in p["deploy_items"]
    )
    qs = []
    for i, q in enumerate(p["diligence_questions"]):
        open_attr = " open" if i == 0 else ""
        qs.append(
            f'<details class="dil-item"{open_attr}>'
            f'<summary><span class="dil-num">{esc(q["num"])}</span> {esc(q["h"])}</summary>'
            f'<p>{esc(q["p"])}</p>'
            f'<div class="dil-agree"><strong>{esc(q["agree_h"])}</strong><p>{esc(q["agree"])}</p></div>'
            f'</details>'
        )
    ctrls = []
    for x in p["controls"]:
        ctrls.append(
            f'<article class="control-card">{_icon(x["icon"])}'
            f'<h3>{esc(x["h"])}</h3><p>{esc(x["p"])}</p></article>'
        )
    hero = (
        '<section class="page-hero"><div class="wrap">'
        f'<p class="kicker">{esc(p["kicker"])}</p>'
        f'<h1>{h1}</h1>'
        f'<p class="lead">{esc(p["lead"])}</p>'
        f'{actions(p["primary_cta"])}'
        '</div></section>'
    )
    close = closing(
        PAGES["home"]["close_h2"],
        PAGES["home"]["close_lead"],
        {"label": "Book a demo", "href": "/book-a-demo/"},
        {"label": "See how it works", "href": "/#story"},
    )
    body = f'''{hero}
<section class="wrap trust-compliance" id="compliance">
  <div class="section-head reveal">
    <p class="kicker">{esc(p["compliance_kicker"])}</p>
    <h2>{esc(p["compliance_h2"])}</h2>
  </div>
  <div class="compliance-badges reveal" aria-label="Current certification and privacy practices">
    {badges}
  </div>
  <p class="muted reveal compliance-note">{esc(p["compliance_lead"])}</p>
</section>
<section class="wrap trust-deployment" id="deployment-planning">
  <div class="section-head reveal">
    <p class="kicker">{esc(p["deploy_kicker"])}</p>
    <h2>{esc(p["deploy_h2"])}</h2>
    <p class="muted">{esc(p["deploy_lead"])}</p>
  </div>
  <div class="trust-visual-grid reveal">
    <div class="trust-explanations">{deploy}</div>
    {trust_deploy_mock()}
  </div>
</section>
<section class="wrap trust-diligence" id="security-diligence">
  <div class="section-head reveal">
    <p class="kicker">{esc(p["diligence_kicker"])}</p>
    <h2>{esc(p["diligence_h2"])}</h2>
    <p class="muted">{esc(p["diligence_lead"])}</p>
  </div>
  <div class="trust-visual-grid is-diligence reveal">
    {trust_diligence_mock()}
    <div class="diligence-questions">{"".join(qs)}</div>
  </div>
</section>
<section class="wrap trust-controls" id="controls">
  <div class="section-head reveal">
    <p class="kicker">{esc(p["controls_kicker"])}</p>
    <h2>{esc(p["controls_h2"])}<br>{esc(p["controls_h2_line2"])}</h2>
  </div>
  <div class="controls-grid reveal">{"".join(ctrls)}</div>
  <div class="actions reveal" style="justify-content:flex-start;margin:36px 0 0">
    <a class="btn btn-primary" href="{esc(p["controls_cta"]["href"])}">{esc(p["controls_cta"]["label"])}</a>
    <a class="btn btn-ghost" href="{esc(p["controls_contact"]["href"])}">{esc(p["controls_contact"]["label"])}</a>
    <a class="btn btn-ghost" href="/legal/security/">Security Overview</a>
  </div>
</section>
{close}
'''
    return layout(p["title"], p["description"], p["path"], body)


LINK_RE = re.compile(r"\[\[([^\]|]+)\|([^\]]+)\]\]")


def rich(text: str) -> str:
    parts: list[str] = []
    last = 0
    for m in LINK_RE.finditer(text):
        parts.append(esc(text[last : m.start()]))
        parts.append(f'<a href="{esc(m.group(2))}">{esc(m.group(1))}</a>')
        last = m.end()
    parts.append(esc(text[last:]))
    return "".join(parts)


def legal_blocks(blocks: list) -> str:
    out = []
    for b in blocks:
        if "p" in b:
            out.append(f"<p>{rich(b['p'])}</p>")
        elif "ul" in b:
            items = "".join(f"<li>{rich(item)}</li>" for item in b["ul"])
            out.append(f"<ul>{items}</ul>")
        elif "table" in b:
            t = b["table"]
            th = "".join(f"<th>{esc(h)}</th>" for h in t["headers"])
            rows = []
            for row in t["rows"]:
                rows.append("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in row) + "</tr>")
            out.append(f'<div class="legal-table-wrap"><table class="legal-table"><thead><tr>{th}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')
    return "\n".join(out)


def legal_end() -> str:
    email = LEGAL.get("contact_email", SITE["email"])
    return (
        '<p class="legal-end">'
        '<a href="/legal/">All legal documents</a>'
        f'<a href="mailto:{esc(email)}">Contact {esc(email)}</a>'
        "</p>"
    )


def build_legal_hub() -> str:
    p = LEGAL["hub"]
    groups = []
    for g in p["groups"]:
        cards = "".join(
            f'<a class="legal-card-link" href="{esc(i["href"])}">'
            f'<h3>{esc(i["h"])}</h3><p>{esc(i["p"])}</p></a>'
            for i in g["items"]
        )
        groups.append(f'<div class="legal-group reveal"><h2>{esc(g["h"])}</h2><div class="legal-cards">{cards}</div></div>')
    body = f'''<section class="page-hero">
  <div class="wrap">
    <p class="kicker">{esc(p["kicker"])}</p>
    <h1>{esc(p["h1"])}</h1>
    <p class="lead">{esc(p["lead"])}</p>
    <p class="muted">{esc(p["note"])}</p>
  </div>
</section>
<section class="wrap legal-directory">
  {"".join(groups)}
</section>
<section class="wrap legal-help reveal">
  <h2>{esc(p["help_h"])}</h2>
  <p>{rich(p["help"])}</p>
</section>
'''
    return layout(p["title"], p["description"], p["path"], body)


def build_legal_doc(doc: dict) -> str:
    toc = []
    secs = []
    for s in doc["sections"]:
        if s.get("h"):
            toc.append(f'<a href="#{esc(s["id"])}">{esc(s["h"])}</a>')
        heading = f'<h2 id="{esc(s["id"])}">{esc(s["h"])}</h2>' if s.get("h") else ""
        if not s.get("h") and s.get("id"):
            heading = f'<div id="{esc(s["id"])}"></div>'
        secs.append(f'{heading}{legal_blocks(s["blocks"])}')
    body = f'''<section class="legal-doc">
  <div class="wrap legal-doc-grid">
    <aside class="legal-sidebar">
      <a class="legal-back" href="/legal/">Back to Legal</a>
      <p class="legal-toc-label">On this page</p>
      <nav class="legal-toc" aria-label="On this page">{"".join(toc)}</nav>
    </aside>
    <article class="legal-prose">
      <p class="kicker">Legal</p>
      <h1>{esc(doc["h1"])}</h1>
      <p class="legal-date">{esc(doc["date"])}</p>
      {"".join(secs)}
      {legal_end()}
    </article>
  </div>
</section>
'''
    return layout(doc["title"], doc["description"], doc["path"], body)




def build_enterprises() -> str:
    p = PAGES["enterprises"]
    offer = "".join(
        f'<article class="reveal"><div class="num">{esc(item["num"])}</div>'
        f'<h3>{esc(item["h"])}</h3><p>{esc(item["p"])}</p></article>'
        for item in p["offer"]
    )
    hero = page_hero(p, actions(p["primary_cta"], p["secondary_cta"]))
    body = f'''{hero}
<section class="wrap" id="offer">
  <div class="section-head reveal">
    <p class="kicker">{esc(p["offer_kicker"])}</p>
    <h2>{esc(p["offer_h2"])}</h2>
    <p class="muted">{esc(p["offer_lead"])}</p>
  </div>
  <div class="card-grid">{offer}</div>
</section>
<section class="wrap trust-compliance" id="security">
  <div class="section-head reveal">
    <p class="kicker">{esc(p["trust_kicker"])}</p>
    <h2>{esc(p["trust_h2"])}</h2>
    <p class="muted">{esc(p["trust_lead"])}</p>
  </div>
  <div class="compliance-badges reveal" aria-label="Current certification and privacy practices">
    {frameworks_html()}
  </div>
  <p class="note reveal"><a href="{esc(p["trust_link"]["href"])}">{esc(p["trust_link"]["label"])}</a></p>
</section>
<section class="wrap" id="proof">
  <div class="section-head reveal">
    <p class="kicker">{esc(p["proof_kicker"])}</p>
    <h2>{esc(p["proof_h2"])}</h2>
    <p class="muted">{esc(p["proof_lead"])}</p>
  </div>
  {cases_html()}
</section>
{closing(p["close_h2"], p["close_lead"], p["primary_cta"], {"label": SITE["email"], "href": "mailto:" + SITE["email"]})}
'''
    return layout(p["title"], p["description"], p["path"], body)


def build_growing() -> str:
    p = PAGES["growing"]
    offer = "".join(
        f'<article class="reveal"><div class="num">{esc(item["num"])}</div>'
        f'<h3>{esc(item["h"])}</h3><p>{esc(item["p"])}</p></article>'
        for item in p["offer"]
    )
    how = "".join(
        f'<article class="reveal"><div class="num">{esc(item["num"])}</div>'
        f'<h3>{esc(item["h"])}</h3><p>{esc(item["p"])}</p></article>'
        for item in p["how"]
    )
    plan = p["plan"]
    includes = "".join(f"<li>{esc(item)}</li>" for item in plan["includes"])
    plan_card = f'''<aside class="plan-card reveal">
  <p class="kicker">{esc(plan["name"])}</p>
  <p class="plan-price">{esc(plan["price"])} <span>{esc(plan["period"])}</span></p>
  <p class="plan-term">{esc(plan["term"])}</p>
  <p class="plan-includes-label">{esc(plan["includes_label"])}</p>
  <ul class="plan-includes">{includes}</ul>
  <a class="btn btn-primary" href="{esc(plan["cta"]["href"])}">{esc(plan["cta"]["label"])}</a>
  <p class="plan-note">{esc(plan["note"])}</p>
</aside>'''
    hero = page_hero(p, actions(p["primary_cta"], p["secondary_cta"]))
    body = f'''{hero}
<section class="wrap" id="offer">
  <div class="section-head reveal">
    <p class="kicker">{esc(p["offer_kicker"])}</p>
    <h2>{esc(p["offer_h2"])}</h2>
    <p class="muted">{esc(p["offer_lead"])}</p>
  </div>
  <div class="card-grid">{offer}</div>
</section>
<section class="wrap" id="how">
  <div class="section-head reveal">
    <p class="kicker">{esc(p["how_kicker"])}</p>
    <h2>{esc(p["how_h2"])}</h2>
    <p class="muted">{esc(p["how_lead"])}</p>
  </div>
  <div class="card-grid">{how}</div>
</section>
<section class="wrap plan-sec" id="plan">
  <div class="plan-layout">
    <div class="section-head reveal">
      <p class="kicker">{esc(p["plan_kicker"])}</p>
      <h2>{esc(p["plan_h2"])}</h2>
      <p class="muted">{esc(p["plan_lead"])}</p>
    </div>
    {plan_card}
  </div>
</section>
{closing(p["close_h2"], p["close_lead"], p["primary_cta"], p["secondary_cta"])}
'''
    return layout(p["title"], p["description"], p["path"], body)


def build_company() -> str:
    p = PAGES["company"]
    ents = []
    for e in p["entities"]:
        facts = "".join(f'<li>{esc(f)}</li>' for f in e["facts"])
        ents.append(
            f'<article class="legal-card"><h3>{esc(e["h"])}</h3><p>{esc(e["p"])}</p><ul>{facts}</ul></article>'
        )
    body = f'''{page_hero(p)}
<section class="wrap">
  <div class="section-head reveal">
    <h2>{esc(p["about_h2"])}</h2>
    <p class="muted">{esc(p["about"])}</p>
    {f'<p class="note">{esc(p["team_note"])}</p>' if p.get("team_note") else ""}
  </div>
</section>
{investors_block(p["investors_kicker"], p["investors_h2"], p["investors_lead"])}
<section class="wrap legal-entities" id="legal-entities">
  <div class="section-head reveal">
    <h2>{esc(p["entities_h2"])}</h2>
    {f'<p class="muted">{esc(p["entities_lead"])}</p>' if p.get("entities_lead") else ""}
  </div>
  <div class="legal-grid reveal">{"".join(ents)}</div>
  {f'<p class="note reveal"><a href="{esc(p["entities_link"])}">{esc(p["entities_link_label"])}</a></p>' if p.get("entities_link") else ""}
</section>
{closing(PAGES["home"]["close_h2"], PAGES["home"]["close_lead"], {"label": "Book a demo", "href": "/book-a-demo/"})}
'''
    return layout(p["title"], p["description"], p["path"], body)


def build_demo() -> str:
    p = PAGES["demo"]
    fields = [
        '<p class="hidden"><label>Don’t fill this in <input name="bot-field"></label></p>',
        '<input type="hidden" name="form-name" value="book-a-demo">',
    ]
    for f in p["fields"]:
        req = " required" if f["required"] else ""
        req_label = ' <span class="req">(required)</span>' if f["required"] else ""
        name = esc(f["name"])
        label = esc(f["label"])
        if f["type"] == "textarea":
            fields.append(
                f'<label for="{name}">{label}{req_label}</label>'
                f'<textarea id="{name}" name="{name}"{req}></textarea>'
            )
        else:
            fields.append(
                f'<label for="{name}">{label}{req_label}</label>'
                f'<input id="{name}" name="{name}" type="{esc(f["type"])}"{req}>'
            )
    form = f'''<form class="form-card reveal" name="book-a-demo" method="POST" action="{esc(p["thanks_path"])}" data-netlify="true" netlify-honeypot="bot-field">
  {"".join(fields)}
  <p class="hint">{esc(p["hint"])}</p>
  <button class="btn btn-primary" type="submit">{esc(p["submit"])}</button>
</form>'''
    extra = f'<div style="margin-top:36px;max-width:560px">{form}</div>'
    body = f'''<section class="page-hero" style="padding-bottom:96px">
  {orbs()}
  <div class="wrap">
    <p class="kicker">{esc(p["kicker"])}</p>
    <h1>{esc(p["h1"])}</h1>
    <p class="lead">{esc(p["lead"])}</p>
    {extra}
  </div>
</section>'''
    return layout(p["title"], p["description"], p["path"], body)


def build_thanks() -> str:
    p = PAGES["demo"]
    body = f'''<section class="page-hero">
  {orbs()}
  <div class="wrap">
    <p class="kicker">Book a demo</p>
    <h1>{esc(p["thanks_h1"])}</h1>
    <p class="lead">{esc(p["thanks_lead"])}</p>
    <div class="actions" style="justify-content:flex-start;margin-top:28px;margin-bottom:0">
      <a class="btn btn-primary" href="/">Back to home</a>
    </div>
  </div>
</section>'''
    return layout(p["thanks_title"], p["thanks_lead"], p["thanks_path"], body)


def build_404() -> str:
    body = f'''<section class="page-hero">
  {orbs()}
  <div class="wrap">
    <p class="kicker">Not found</p>
    <h1>This page is not available.</h1>
    <p class="lead">The address may be wrong, or the page may have moved.</p>
    <div class="actions" style="justify-content:flex-start;margin-top:28px;margin-bottom:0">
      <a class="btn btn-primary" href="/">Back to home</a>
    </div>
  </div>
</section>'''
    return layout("Page not found | enterlabs", "This page is not available.", "/404.html", body)



def write_content_docx() -> None:
    """Regenerate the review Word file from CONTENT.md."""
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor
    from docx.enum.text import WD_LINE_SPACING

    md = (ROOT / "CONTENT.md").read_text(encoding="utf-8").splitlines()
    doc = Document()
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    i = 0
    while i < len(md):
        line = md[i]
        nxt = md[i + 1] if i + 1 < len(md) else ""
        if i == 0:
            p = doc.add_heading(line, level=1)
            i += 1
            continue
        if nxt and set(nxt) <= {"-"} and len(nxt) >= 3:
            doc.add_heading(line, level=2)
            i += 2
            continue
        if line == "====================":
            i += 1
            continue
        if not line:
            i += 1
            continue
        para = doc.add_paragraph(line)
        for run in para.runs:
            run.font.name = "Calibri"
            run.font.size = Pt(11)
            run.font.color.rgb = RGBColor(0x11, 0x11, 0x11)
        i += 1
    dest = ROOT / "enterlabs-website-content.docx"
    doc.save(dest)


def write_content_md() -> None:
    """Plain-text copy of every page for review."""
    lines: list[str] = []
    lines.append("enterlabs site copy")
    lines.append("====================")
    lines.append("")
    lines.append("This is the full copy of every page, for review. The live site is generated from content.json.")
    lines.append("The written name is 'enterlabs' in lowercase, with no 'AI' suffix.")
    lines.append("There are no published performance metrics. Product screens on the homepage and Platform use an industry-neutral HTML mockup of a supplier invoice matched against a purchase order and a delivery note. Real product screens stay on the insurance and health insurance claims pages.")
    lines.append("")

    def h(title: str) -> None:
        lines.append("")
        lines.append(title)
        lines.append("-" * len(title))
        lines.append("")

    def p(label: str, text: str) -> None:
        lines.append(f"{label}")
        lines.append(text)
        lines.append("")

    # Shared chrome
    h("Shared chrome")
    lines.append("Wordmark: official enterlabs logo (Enter-key icon + serif 'enterlabs'). Alt text: enterlabs.")
    lines.append("Navigation: " + " | ".join(i["label"] + (" (dropdown)" if i.get("children") else "") for i in SITE["nav"]) + " | " + SITE["cta"]["label"])
    for i in SITE["nav"]:
        if i.get("children"):
            lines.append(i["label"] + " dropdown: " + "; ".join(k["label"] + (" (" + k["desc"] + ")" if k.get("desc") else "") for k in i["children"]) + ("; " + i["all"]["label"] if i.get("all") else ""))
    lines.append("Footer Explore: " + " | ".join(i["label"] for i in SITE["footer_explore"]))
    lines.append("Footer legal: " + " | ".join(i["label"] for i in SITE["footer_legal"]))
    lines.append("Contact: " + SITE["email"])
    lines.append("Footer offices:")
    for line in [o["city"]+": "+", ".join(o["lines"]) for o in SITE["footer_offices"]]:
        lines.append("  " + line)
    lines.append("Footer tagline: " + SITE["footer_tagline"])
    lines.append("Clients label: " + SITE["logo_strip_label"])
    lines.append("Clients (greyscale wall, two rows): " + "; ".join(c["alt"] for c in SITE["clients"]))
    lines.append("Investors: " + "; ".join(i["alt"] for i in SITE["investors"]))
    lines.append("")

    home = PAGES["home"]
    h("Home")
    lines.append("Title: " + home["title"])
    lines.append("Meta description: " + home["description"])
    lines.append("")
    p("Kicker", home["kicker"])
    p("Headline", home["h1"] + " " + home["h1_em"])
    p("Lead", home["lead"])
    p("Document wall line 1", home["doc_wall"]["line1"])
    p("Document wall line 2", home["doc_wall"]["line2"])
    p("Stats strip", "; ".join(
        (x["num"] + (" " + x["unit"] if x.get("unit") else "") + x.get("sup", "")) + " = " + x["cap"]
        for x in home["stats"]))
    p("Clients label", SITE["logo_strip_label"])
    p("Clients (greyscale wall, two rows)", "; ".join(c["alt"] for c in SITE["clients"]))
    lines.append("Buttons: " + home["primary_cta"]["label"] + " | " + home["secondary_cta"]["label"])
    lines.append("")
    p("Problem kicker", home["problem_kicker"])
    p("Problem headline", home["problem_h2"])
    p("Problem lead", home["problem_lead"])
    for c in home["problem_cards"]:
        p(c["h"], c["p"])
    p("Story kicker", home["story_kicker"])
    p("Story headline", home["story_h2"])
    for s in home["story_steps"]:
        p(s["num"] + " " + s["h"], s["p"])
    ps = SITE["product_screen"]
    p(
        "Homepage and Platform product screen",
        ps["id"] + ", " + ps["supplier"] + ". " + ", ".join(ps["documents"])
        + ". Flagged: " + ps["finding"]["item"] + " (" + ps["finding"]["kind"] + "). "
        + ps["finding"]["text"],
    )
    p("Industries kicker", home["industries_kicker"])
    p("Industries headline", home["industries_h2"])
    p("Industries lead", home["industries_lead"])
    p("Quotes kicker", home["quotes_kicker"])
    p("Quotes headline", home["quotes_h2"])
    p("Investors kicker / headline", home["investors_kicker"] + " / " + home["investors_h2"])
    p("Trust kicker", home["trust_kicker"])
    p("Trust headline", home["trust_h2"])
    p("Trust lead", home["trust_lead"])
    for item in home["trust_items"]:
        p(item["h"], item["p"])
    p("Systems kicker", home["systems_kicker"])
    p("Systems headline", home["systems_h2"])
    p("Systems lead", home["systems_lead"])
    p("Deployment toggle", home["systems_toggle_label"])
    for d in home["systems_modes"]:
        p(d["label"], d["p"])
    p(
        "Flow",
        "In: " + ", ".join(s["label"] for s in home["systems_sources"])
        + ". Then " + home["systems_node_redact"] + " (hybrid only), "
        + home["systems_node_enterlabs"] + ", "
        + home["systems_node_out"] + ", "
        + home["systems_node_systems"] + ".",
    )
    p("Closing headline", home["close_h2"])
    p("Closing lead", home["close_lead"])
    p("Audience doors kicker / headline", home["doors_kicker"] + " / " + home["doors_h2"])
    for d in home["doors"]:
        p(d["kicker"] + ": " + d["h"], d["p"] + " Link: " + d["href"] + " (" + d["label"] + ")")
    p("Products kicker / headline", home["products_kicker"] + " / " + home["products_h2"])
    p("Products lead", home["products_lead"])
    for item in home["products"]:
        p(item["num"] + " " + item["h"], item["p"])

    for key, heading in (("enterprises", "For enterprises"), ("growing", "For growing businesses")):
        pg = PAGES[key]
        h(heading + "  (" + pg["path"] + ")")
        lines.append("Title: " + pg["title"])
        lines.append("Meta description: " + pg["description"])
        lines.append("")
        p("Kicker", pg["kicker"])
        p("Headline", pg["h1"])
        p("Lead", pg["lead"])
        lines.append("Buttons: " + pg["primary_cta"]["label"] + " | " + pg["secondary_cta"]["label"])
        lines.append("")
        p(pg["offer_h2"], pg["offer_lead"])
        for item in pg["offer"]:
            p(item["num"] + " " + item["h"], item["p"])
        if pg.get("trust_h2"):
            p(pg["trust_h2"], pg["trust_lead"] + " Link: " + pg["trust_link"]["label"])
            p("Security badges", "Reused from the Trust page, including ISO/IEC 27001:2022.")
        if pg.get("proof_h2"):
            p(pg["proof_h2"], pg["proof_lead"] + " Reuses the Mega Insurance and Takaful Keluarga with Medilink stories.")
        if pg.get("how"):
            p(pg["how_h2"], pg["how_lead"])
            for item in pg["how"]:
                p(item["num"] + " " + item["h"], item["p"])
        if pg.get("plan"):
            plan = pg["plan"]
            p(pg["plan_h2"], pg["plan_lead"])
            p("Plan card", plan["name"] + ". " + plan["price"] + " " + plan["period"] + ". " + plan["term"] + ".")
            for item in plan["includes"]:
                lines.append("  - " + item)
            lines.append("")
            p("Plan note", plan["note"])
            lines.append("Plan CTA: " + plan["cta"]["label"])
            lines.append("")
        p("Closing headline", pg["close_h2"])
        p("Closing lead", pg["close_lead"])

    plat = PAGES["platform"]
    h("Platform")
    lines.append("Title: " + plat["title"])
    lines.append("Meta description: " + plat["description"])
    lines.append("")
    p("Kicker", plat["kicker"])
    p("Headline", plat["h1"])
    p("Lead", plat["lead"])
    p("Intro", plat["intro"])
    for item in plat["pillars"]:
        p(item["kicker"] + " " + item["h"], item["p"] + ((" " + item["note"]) if item.get("note") else ""))
    p("Integration headline", plat["integrate_h2"])
    p("Integration lead", plat["integrate_lead"])
    for d in plat["deploy"]:
        p(d["h"], d["p"])
    if plat.get("integrate_note"):
        p("Integration note", plat["integrate_note"])
    p("Closing headline", plat["close_h2"])
    p("Closing lead", plat["close_lead"])

    ind = PAGES["industries"]
    h("Industries")
    lines.append("Title: " + ind["title"])
    lines.append("Meta description: " + ind["description"])
    lines.append("")
    p("Kicker", ind["kicker"])
    p("Headline", ind["h1"])
    p("Lead", ind["lead"])
    p("In production: " + ind["proven"]["h"], ind["proven"]["p"] + " Link: " + ind["proven"]["label"])
    p(ind["reach_h2"], ind["reach_lead"])
    p("Industry dropdown label", ind["picker_label"])
    for o in ind["options"]:
        extra = (" " + o["kicker"] + ".") if o.get("kicker") else ""
        body = " ".join(x for x in [o.get("docs"), o.get("problem"), o.get("note")] if x)
        if o.get("checks"):
            body += " Example checks: " + " ".join(o["checks"])
        if o.get("page_link"):
            body += " Link: " + o["page_link"] + "."
        if o.get("link"):
            body += " Link: " + o["link"]
        p(o["label"] + extra, body)
    p("Closing headline", ind["close_h2"])
    p("Closing lead", ind["close_lead"])

    for slug, ipg in PAGES["industry_pages"].items():
        h("Industries / " + ipg["label"] + "  (" + ipg["path"] + ")")
        lines.append("Title: " + ipg["title"])
        lines.append("Meta description: " + ipg["description"])
        lines.append("")
        p("Headline", ipg["h1"])
        p("Lead", ipg["lead"])
        p(ipg["problem_h2"], ipg["problem"] + " Documents: " + ipg["docs"])
        p(ipg["checks_h2"], " ".join(ipg["checks"]))
        p(ipg["how_h2"], " ".join(s["h"] + ": " + s["p"] for s in ipg["how"]))
        p(ipg["screen_h2"], ipg["screen_lead"])
        m = ipg.get("mock")
        if m:
            p("Example screen: " + m["ref"], "; ".join(m["meta"]) + ". Columns: " + ", ".join(m["cols"]) + ". Rows: " + " | ".join(r["item"] + ": " + ", ".join(r["v"]) + (" [" + r.get("result", "Review") + "]" if r.get("flag") is not None else "") for r in m["rows"]))
            p("Example screen finding", m["finding"]["item"] + " (" + m["finding"]["kind"] + "). " + m["finding"]["text"])
            p("Example screen checks", " | ".join(c["label"] + ": " + c["value"] + " [" + ("Match" if c["ok"] else "Review") + "]" for c in m["checks"]))
        else:
            p("Example screen", "Real product screen from the health insurance claims case.")
        if ipg.get("extra_link"):
            p("Link", ipg["extra_link"]["label"])
        p("Closing headline", ipg["close_h2"])
        p("Closing lead", ipg["close_lead"])

    health = PAGES["health"]
    h("Industries / Health insurance claims")
    lines.append("Title: " + health["title"])
    lines.append("Meta description: " + health["description"])
    lines.append("")
    p("Kicker", health["kicker"])
    p("Headline", health["h1"])
    p("Lead", health["lead"])
    p(health["who_h2"], health["who_lead"])
    p(health["how_h2"], health["qualify"])
    for s in health["how"]:
        p(s["h"], s["p"])
    p(health["docs_h2"], health["docs_lead"])
    p("Closing", health["close_lead"])

    cu = PAGES["customers"]
    h("Customers")
    lines.append("Title: " + cu["title"])
    lines.append("Meta description: " + cu["description"])
    lines.append("")
    p("Kicker", cu["kicker"])
    p("Headline", cu["h1"])
    p("Lead", cu["lead"])
    lines.append("Clients label: " + SITE["logo_strip_label"])
    lines.append("  " + "; ".join(c["alt"] for c in SITE["clients"]))
    lines.append("")
    p("Quotes headline", cu["quotes_h2"])
    if cu.get("quotes_note"): p("Note", cu["quotes_note"])
    if SITE.get("cases_footnote"):
        p("Figures note", SITE["cases_footnote"])
    for q in SITE["quotes"]:
        p(q["name"] + ", " + q["role"], "“" + q["text"] + "”")
        if q.get("headline"):
            p("Client", q.get("client", "") + ". " + q.get("tag", ""))
            p("Headline", q["headline"])
            p("Challenge", q["challenge"])
            p("What we did", q["did"])
            p("Scale", q["scale_value"] + " " + q["scale_caption"])
            for m in q["metrics"]:
                p("Metric", m["value"] + " " + m["label"])
            if q.get("story_path"):
                p("Story page", q["story_path"])
                p("Story title", q.get("story_title", ""))
                p("Company overview", q.get("company_name", "") + ". " + q.get("industry_label", "") + ". " + q.get("use_case", "") + ". " + q.get("customer", ""))
                p("About the company", q.get("about", ""))
                p("Challenge heading", q.get("challenge_h", ""))
                p("Challenge", q.get("challenge_body", ""))
                p("What we built", q.get("solution_lead", ""))
                for i, s in enumerate(q.get("steps") or [], 1):
                    p(f"Step {i}", s["h"] + ". " + s["p"])
                p("Looking ahead", q.get("next_h", "") + ". " + q.get("next_body", ""))
    if cu.get("after"):
        p("After the quotes", cu["after"])

    tr = PAGES["trust"]
    h("Trust")
    lines.append("Title: " + tr["title"])
    lines.append("Meta description: " + tr["description"])
    lines.append("")
    p("Kicker", tr["kicker"])
    p("Headline", tr["h1"] + " " + tr.get("h1_line2", ""))
    p("Lead", tr["lead"])
    p("Hero button", tr["primary_cta"]["label"])
    p(tr["compliance_kicker"], tr["compliance_h2"])
    for f in tr["frameworks"]:
        p(f["h"], f["status"])
    p("Compliance note", tr["compliance_lead"])
    p(tr["deploy_kicker"], tr["deploy_h2"])
    p("Deployment lead", tr["deploy_lead"])
    for x in tr["deploy_items"]:
        p(x["h"], x["p"])
    p(tr["diligence_kicker"], tr["diligence_h2"])
    p("Diligence lead", tr["diligence_lead"])
    for q in tr["diligence_questions"]:
        p(q["num"] + " " + q["h"], q["p"] + " " + q["agree_h"] + ": " + q["agree"])
    p(tr["controls_kicker"], tr["controls_h2"] + " " + tr["controls_h2_line2"])
    for x in tr["controls"]:
        p(x["h"], x["p"])
    lines.append("Buttons: " + tr["controls_cta"]["label"] + " | " + tr["controls_contact"]["label"])

    co = PAGES["company"]
    h("Company")
    lines.append("Title: " + co["title"])
    lines.append("Meta description: " + co["description"])
    lines.append("")
    p("Kicker", co["kicker"])
    p("Headline", co["h1"])
    p("Lead", co["lead"])
    p(co["about_h2"], co["about"])
    if co.get("team_note"):
        p("Team note", co["team_note"])
    p(co["entities_h2"], co.get("entities_lead") or "")
    for e in co["entities"]:
        lines.append(e["h"])
        lines.append(e["p"])
        for f in e.get("facts") or []:
            lines.append("  - " + f)
        lines.append("")
    if co.get("entities_link"):
        p("Legal entities link", co["entities_link_label"] + " -> " + co["entities_link"])
    p(co["investors_h2"], co["investors_lead"])

    h("Legal")
    hub = LEGAL["hub"]
    lines.append("Title: " + hub["title"])
    lines.append("Meta description: " + hub["description"])
    lines.append("")
    p("Kicker", hub["kicker"])
    p("Headline", hub["h1"])
    p("Lead", hub["lead"])
    p("Note", hub["note"])
    for g in hub["groups"]:
        lines.append(g["h"] + ":")
        for i in g["items"]:
            lines.append("  " + i["h"] + " (" + i["href"] + "): " + i["p"])
        lines.append("")
    p(hub["help_h"], hub["help"].replace("[[", "").replace("]]", "").replace("|", " -> "))
    lines.append("Footer legal: " + " | ".join(i["label"] for i in SITE["footer_legal"]))
    lines.append("")
    for doc in LEGAL["docs"]:
        h(doc["h1"])
        lines.append("Path: " + doc["path"])
        lines.append("Title: " + doc["title"])
        lines.append("Meta description: " + doc["description"])
        lines.append(doc["date"])
        lines.append("")
        for sec in doc["sections"]:
            if sec.get("h"):
                lines.append(sec["h"])
            for b in sec["blocks"]:
                if "p" in b:
                    lines.append(b["p"].replace("[[", "").replace("]]", "").replace("|", " -> "))
                    lines.append("")
                elif "ul" in b:
                    for item in b["ul"]:
                        lines.append("- " + item)
                    lines.append("")
                elif "table" in b:
                    t = b["table"]
                    lines.append("  " + " | ".join(t["headers"]))
                    for row in t["rows"]:
                        lines.append("  " + " | ".join(row))
                    lines.append("")
        lines.append("")

    demo = PAGES["demo"]
    h("Book a demo")
    lines.append("Title: " + demo["title"])
    lines.append("Meta description: " + demo["description"])
    lines.append("")
    p("Kicker", demo["kicker"])
    p("Headline", demo["h1"])
    p("Lead", demo["lead"])
    lines.append("Form fields:")
    for f in demo["fields"]:
        req = " (required)" if f["required"] else ""
        lines.append("  - " + f["label"] + req)
    lines.append("")
    p("Submit", demo["submit"])
    p("Privacy hint", demo["hint"])
    p("Thank-you headline", demo["thanks_h1"])
    p("Thank-you lead", demo["thanks_lead"])

    h("Items that need confirmation")
    for i, item in enumerate(CONTENT["confirmations"], 1):
        lines.append(f"{i}. {item}")
        lines.append("")

    (ROOT / "CONTENT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def copy_static() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    shutil.copytree(ROOT / "public" / "assets", DIST / "assets")
    shutil.copytree(ROOT / "public" / "fonts", DIST / "fonts")
    css_dir = DIST / "css"
    js_dir = DIST / "js"
    css_dir.mkdir()
    js_dir.mkdir()
    shutil.copy(ROOT / "src" / "styles.css", css_dir / "styles.css")
    shutil.copy(ROOT / "src" / "site.js", js_dir / "site.js")
    headers = "/*\n  X-Robots-Tag: noindex, nofollow\n  Referrer-Policy: strict-origin-when-cross-origin\n"
    (DIST / "_headers").write_text(headers + "\n", encoding="utf-8")
    (DIST / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    (ROOT / "netlify.toml").write_text(
        '[[headers]]\n  for = "/*"\n  [headers.values]\n    X-Robots-Tag = "noindex, nofollow"\n\n'
        '[[redirects]]\n  from = "/*"\n  to = "/404.html"\n  status = 404\n',
        encoding="utf-8",
    )
    shutil.copy(ROOT / "netlify.toml", DIST / "netlify.toml")


def write(path: str, html_text: str) -> None:
    if path.endswith(".html") and not path.endswith("/index.html"):
        dest = DIST / path.lstrip("/")
    else:
        dest = DIST / path.lstrip("/") / "index.html" if path != "/" else DIST / "index.html"
        if path != "/" and not path.endswith(".html"):
            dest = DIST / path.strip("/") / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html_text, encoding="utf-8")
    print("wrote", dest.relative_to(DIST))


def main() -> None:
    copy_static()
    write("/", build_home())
    write("/enterprises/", build_enterprises())
    write("/growing-businesses/", build_growing())
    write("/platform/", build_platform())
    write("/industries/", build_industries())
    write("/industries/health-insurance-claims/", build_health())
    for slug in PAGES["industry_pages"]:
        write(f"/industries/{slug}/", build_industry(slug))
    write("/customers/", build_customers())
    for q in SITE["quotes"]:
        if q.get("story_path"):
            write(q["story_path"], build_story(q))
    write("/trust/", build_trust())
    write("/company/", build_company())
    write("/legal/", build_legal_hub())
    for doc in LEGAL["docs"]:
        write(doc["path"], build_legal_doc(doc))
    write("/book-a-demo/", build_demo())
    write("/book-a-demo/thanks/", build_thanks())
    write("/404.html", build_404())
    write_content_md()
    try:
        write_content_docx()
    except ImportError:
        print('python-docx not installed, skipping docx')
    print("CONTENT.md and enterlabs-website-content.docx written")


if __name__ == "__main__":
    main()
