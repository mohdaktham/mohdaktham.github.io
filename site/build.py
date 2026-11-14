"""
Builds the portfolio site.

    python site/build.py

Reads the text in site/content.py and writes index.html, 404.html and one
case-study page per project (projects/<slug>/index.html). It uses only the
Python standard library, and the generated pages are committed, so GitHub
Pages serves them as they are with no build step of its own.
"""

from __future__ import annotations

import csv
import html
import json
import math
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import content as c  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BY_SLUG = {p["slug"]: p for p in c.PROJECTS}


# -- small helpers -----------------------------------------------------------

def esc(text: str) -> str:
    return html.escape(text, quote=True)


def inline(text: str) -> str:
    """Escapes text, then applies **bold** and `code`."""
    out = esc(text)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", out)


def png_size(path: Path) -> tuple[int, int]:
    """Reads width and height from a PNG header, so images never shift the layout."""
    with path.open("rb") as handle:
        header = handle.read(24)
    return struct.unpack(">II", header[16:24])


def anchor(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def project_url(slug: str, root: str) -> str:
    return f"{root}projects/{slug}/"


def words(text: str) -> str:
    """Wraps each word so the headline can arrive one word at a time."""
    return " ".join(
        f'<span class="word" style="--i:{index}">{esc(word)}</span>'
        for index, word in enumerate(text.split())
    )


SKILLS_BY_SLUG = {
    p["slug"]: [skill for skill, slugs in c.SKILLS if p["slug"] in slugs] for p in c.PROJECTS
}


# -- evidence: bars, stats and images ---------------------------------------

def bars(spec: dict) -> str:
    top = spec.get("max") or max(bar["value"] for bar in spec["bars"])
    summary = "; ".join(f'{bar["label"]} {bar["display"]}' for bar in spec["bars"])
    rows = "".join(
        f'<div class="bar"><span class="bar-label">{esc(bar["label"])}</span>'
        f'<span class="bar-track"><span class="bar-fill tone-{bar["tone"]}" '
        f'style="width:{bar["value"] / top * 100:.1f}%;--i:{index}"></span></span>'
        f'<span class="bar-value">{esc(bar["display"])}</span></div>'
        for index, bar in enumerate(spec["bars"])
    )
    return f'<div class="bars" role="img" aria-label="{esc(summary)}">{rows}</div>'


def stats(items: list[tuple[str, str]], cls: str = "stats") -> str:
    cells = "".join(
        f'<div class="stat"><dt>{esc(label)}</dt><dd>{esc(number)}</dd></div>'
        for number, label in items
    )
    return f'<dl class="{cls}">{cells}</dl>'


def evidence(spec: dict, root: str, link: str | None = None) -> str:
    caption = f'<figcaption>{inline(spec["caption"])}</figcaption>' if spec.get("caption") else ""
    if spec["kind"] == "bars":
        body = bars(spec)
    elif spec["kind"] == "stats":
        body = stats(spec["stats"])
    else:
        width, height = spec["size"]
        image = (
            f'<img src="{root}{spec["src"]}" alt="{esc(spec["alt"])}" '
            f'width="{width}" height="{height}" loading="lazy">'
        )
        body = f'<a class="shot" href="{link}">{image}</a>' if link else f'<span class="shot">{image}</span>'
    return f'<figure class="evidence evidence-{spec["kind"]}">{body}{caption}</figure>'


# -- page shell ---------------------------------------------------------------

def layout(*, title: str, description: str, body: str, root: str, path: str, page: str = "page") -> str:
    home = root or "./"
    url = f'{c.SITE["url"]}/{path}'
    progress = '<div class="progress" aria-hidden="true"><span></span></div>' if page == "case" else ""
    return f"""<!doctype html>
<html lang="en" data-page="{page}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="color-scheme" content="light dark">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(url)}">
<meta property="og:image" content="{c.SITE["url"]}/assets/img/og.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{esc(url)}">
<link rel="icon" href="{root}assets/favicon.svg" type="image/svg+xml">
<link rel="preload" href="{root}assets/fonts/bricolage-grotesque-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{root}assets/site.css">
<script>(function(){{var d=document.documentElement;d.classList.add("js");try{{var t=localStorage.getItem("theme");if(t)d.dataset.theme=t}}catch(e){{}}setTimeout(function(){{if(!window.siteReady)d.classList.remove("js")}},4000)}})()</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="wrap top-inner">
    <a class="brand" href="{home}">{esc(c.SITE["name"])}</a>
    <nav aria-label="Main">
      <a href="{home}#work">Work</a>
      <a href="{home}#skills">Skills</a>
      <a href="{home}#about">About</a>
      <button type="button" class="theme" id="theme-toggle" aria-label="Switch between light and dark">
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M12 3a9 9 0 1 0 0 18Z" fill="currentColor"/><circle cx="12" cy="12" r="8.25" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>
      </button>
    </nav>
  </div>
  {progress}
</header>
<main id="main">
{body}
</main>
<footer class="foot">
  <div class="wrap foot-inner">
    <p>{esc(c.SITE["name"])}, Toronto</p>
    <p>
      <a href="mailto:{c.SITE["email"]}">{c.SITE["email"]}</a>
      <a href="{c.SITE["linkedin"]}">LinkedIn</a>
      <a href="{c.SITE["github"]}">GitHub</a>
      <a href="{c.SITE["repo"]}">Source for this site</a>
    </p>
  </div>
</footer>
<script src="{root}assets/site.js" defer></script>
</body>
</html>
"""


# -- home page ---------------------------------------------------------------

def work_row(project: dict) -> str:
    url = project_url(project["slug"], "")
    slug = project["slug"]
    skills = "|".join(SKILLS_BY_SLUG[slug])
    return f"""
    <article class="work-row" data-reveal data-skills="{esc(skills)}" style="view-transition-name:row-{slug}">
      <div class="claim">
        <p class="kicker">{esc(project["kicker"])}</p>
        <h3 style="view-transition-name:title-{slug}"><a href="{url}">{esc(project["title"])}</a></h3>
        <p class="finding">{inline(project["finding"])}</p>
        <p class="tools">{esc(", ".join(project["tools"]))}</p>
      </div>
      {evidence(project["evidence"], "", url)}
    </article>"""


def skills_matrix() -> str:
    head = "".join(
        f'<th scope="col"><a href="{project_url(p["slug"], "")}">{esc(p["short"])}</a></th>'
        for p in c.PROJECTS
    )
    rows = []
    for row, (skill, slugs) in enumerate(c.SKILLS):
        cells = "".join(
            f'<td><span class="mark" aria-label="yes" style="--d:{row + column}"></span></td>'
            if p["slug"] in slugs
            else '<td><span class="sr">no</span></td>'
            for column, p in enumerate(c.PROJECTS)
        )
        rows.append(
            f'<tr><th scope="row"><a href="#work" data-skill="{esc(skill)}">{esc(skill)}</a></th>{cells}</tr>'
        )
    return (
        '<div class="matrix-scroll" tabindex="0" role="region" aria-label="Skills by project">'
        f'<table class="matrix"><thead><tr><td></td>{head}</tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div>'
    )


def hero_slides() -> str:
    """The evidence card in the hero: one example per tab, the first shown by default."""
    tabs, panels = [], []
    for index, slide in enumerate(c.HERO_SLIDES):
        first = index == 0
        tabs.append(
            f'<button type="button" role="tab" id="tab-{index}" aria-controls="slide-{index}" '
            f'aria-selected="{"true" if first else "false"}"{"" if first else ' tabindex="-1"'}>'
            f'{esc(slide["tab"])}<span class="tab-progress"></span></button>'
        )
        panels.append(
            f'<div class="slide" id="slide-{index}"{"" if first else " hidden"}>'
            f'<p class="evidence-title">{esc(slide["title"])}</p>{bars(slide)}'
            f'<p class="slide-caption">{inline(slide["caption"])} '
            f'<a href="{project_url(slide["slug"], "")}">Read the case study</a></p></div>'
        )
    return (
        '<figure class="evidence hero-evidence" data-slides>'
        '<div class="slides-head"><p class="evidence-label" id="slides-label">For example</p>'
        f'<div class="tabs" role="tablist" aria-labelledby="slides-label" hidden>{"".join(tabs)}</div></div>'
        f'<div class="slides">{"".join(panels)}</div></figure>'
    )


def skill_filter() -> str:
    chips = ['<button type="button" class="chip" aria-pressed="true" data-skill="">All</button>']
    for skill, slugs in c.SKILLS:
        chips.append(
            f'<button type="button" class="chip" aria-pressed="false" data-skill="{esc(skill)}" '
            f'aria-label="{esc(skill)}, {len(slugs)} of {len(c.PROJECTS)} projects">{esc(skill)}'
            f'<span class="chip-n" aria-hidden="true">{len(slugs)}</span></button>'
        )
    return (
        '<div class="filter" data-filter hidden><p id="filter-label">Filter by skill</p>'
        f'<div class="chips" role="group" aria-labelledby="filter-label">{"".join(chips)}</div>'
f'<p class="filter-status" role="status" data-filter-status>{len(c.PROJECTS)} projects</p></div>'
    )


def home() -> str:
    rows = "".join(work_row(p) for p in c.PROJECTS)
    more = "".join(
        f'<li data-reveal><p class="kicker">{esc(m["kicker"])}</p>'
        f'<h3><a href="{m["url"]}">{esc(m["title"])}</a></h3><p>{inline(m["text"])}</p></li>'
        for m in c.MORE
    )
    toolkit = "".join(f"<div><dt>{esc(name)}</dt><dd>{esc(text)}</dd></div>" for name, text in c.TOOLKIT)
    about = "".join(f"<p>{inline(text)}</p>" for text in c.ABOUT)
    body = f"""
<section class="hero hero-home">
  <div class="wrap hero-grid">
    <div class="hero-copy">
      <h1>{words(c.SITE["headline"])}</h1>
      <p class="intro">{inline(c.SITE["intro"])}</p>
      <p class="actions">
        <a class="btn btn-solid" href="mailto:{c.SITE["email"]}">Email me</a>
        <a class="btn" href="{c.SITE["linkedin"]}">LinkedIn</a>
        <a class="btn" href="{c.SITE["github"]}">GitHub</a>
      </p>
    </div>
    {hero_slides()}
  </div>
</section>

<section id="work" class="section">
  <div class="wrap">
    <div class="section-head" data-reveal>
      <h2>Selected work</h2>
      <p>Each project says what it found, and beside it, the check behind the claim.</p>
    </div>
    {skill_filter()}
    <div class="work">{rows}
    </div>
  </div>
</section>

<section id="more" class="section">
  <div class="wrap">
    <div class="section-head" data-reveal>
      <h2>More on GitHub</h2>
      <p>Graduate coursework and research, with the code in its own repositories.</p>
    </div>
    <ul class="more">{more}</ul>
  </div>
</section>

<section id="skills" class="section">
  <div class="wrap">
    <div class="section-head" data-reveal>
      <h2>Skills, and where to see them</h2>
      <p>A filled square means the project uses that skill. Choose a skill to filter the work above, or a project name to open it.</p>
    </div>
    {skills_matrix()}
    <dl class="toolkit" data-reveal>{toolkit}</dl>
  </div>
</section>

<section id="about" class="section">
  <div class="wrap about">
    <div data-reveal>
      <h2>About</h2>
      {about}
    </div>
    <div data-reveal>
      <h2>Contact</h2>
      <ul class="contact">
        <li><span>Email</span><a href="mailto:{c.SITE["email"]}">{c.SITE["email"]}</a></li>
        <li><span>LinkedIn</span><a href="{c.SITE["linkedin"]}">linkedin.com/in/mo-maghaireh</a></li>
        <li><span>GitHub</span><a href="{c.SITE["github"]}">github.com/mohdaktham</a></li>
        <li><span>Location</span>Toronto, Ontario</li>
      </ul>
    </div>
  </div>
</section>
"""
    return layout(
        title=f'{c.SITE["name"]}, data analyst in Toronto',
        description=c.SITE["description"],
        body=body,
        root="",
        path="",
        page="home",
    )


# -- case-study pages --------------------------------------------------------

def figure(fig: dict, project_dir: Path, root: str) -> str:
    if fig.get("root"):
        src = root + fig["src"]
        width, height = fig["size"]
    else:
        src = fig["src"]
        width, height = png_size(project_dir / fig["src"])
    plate = "" if fig.get("root") else " plate"
    return (
        f'<figure class="fig{plate}"><img src="{src}" alt="{esc(fig["alt"])}" '
        f'width="{width}" height="{height}" loading="lazy">'
        f'<figcaption>{inline(fig["caption"])}</figcaption></figure>'
    )


MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]
STATUS_LABEL = {"baseline": "Baseline", "green": "Green", "amber": "Amber", "red": "Red",
                "pending": "Pending"}
AUC_FLOOR, AUC_TOP = 0.6, 1.0
CSI_WATCH, CSI_ACT = 0.10, 0.25


def monitor(spec: dict, project_dir: Path) -> str:
    """An explorable chart of the monitoring report, drawn from the project's own CSV."""
    with (project_dir / spec["csv"]).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    count = len(rows)
    csi_top = math.ceil(max(float(r["top_csi"]) for r in rows) * 10) / 10
    baseline = float(rows[0]["auc"])

    def auc_y(value: float) -> float:
        return (value - AUC_FLOOR) / (AUC_TOP - AUC_FLOOR) * 100

    months, points, data = [], [], []
    for index, row in enumerate(rows):
        year, month = row["month"].split("-")
        name = MONTHS[int(month) - 1]
        auc, csi = float(row["auc"]), float(row["top_csi"])
        level = "act" if csi > CSI_ACT else "watch" if csi > CSI_WATCH else "calm"
        status = row["status"]
        provisional = row["labels_mature"] != "True"
        entry = {
            "month": row["month"],
            "name": f"{name} {year}",
            "status": status,
            "statusLabel": STATUS_LABEL[status],
            "note": spec["notes"][row["month"]],
            "auc": f"{auc:.3f}",
            "aucLabel": "AUC, provisional" if provisional else "AUC",
            "caught": f'{float(row["detection_rate"]) * 100:.1f}%',
            "psi": f'{float(row["score_psi"]):.3f}',
            "csi": f"{csi:.2f}",
            "feature": row["top_feature"],
        }
        data.append(entry)
        points.append((index, auc_y(auc), provisional))
        selected = row["month"] == spec["start"]
        months.append(
            f'<button type="button" class="month s-{status}" aria-pressed="{"true" if selected else "false"}" '
            f'data-index="{index}" style="--i:{index}" '
            f'aria-label="{name} {year}: {STATUS_LABEL[status].lower()}. AUC {auc:.3f}. Largest input shift {csi:.2f}.">'
            f'<span class="auc-track"><span class="dot" style="bottom:{auc_y(auc):.1f}%"></span></span>'
            f'<span class="csi-track"><span class="csi-bar csi-{level}" style="height:{max(csi / csi_top * 100, 1.5):.1f}%"></span></span>'
            f'<span class="month-name">{name[:3]}</span></button>'
        )

    def x(index: int) -> float:
        return (index + 0.5) / count * 100

    firm = " ".join(f"{x(i):.2f},{100 - y:.2f}" for i, y, provisional in points if not provisional)
    last_firm = max(i for i, _, provisional in points if not provisional)
    loose = " ".join(f"{x(i):.2f},{100 - y:.2f}" for i, y, _ in points if i >= last_firm)
    grid = "".join(
        f'<line x1="0" x2="100" y1="{100 - auc_y(v):.2f}" y2="{100 - auc_y(v):.2f}" class="grid-line"/>'
        for v in (0.6, 0.8, 1.0)
    )
    base_y = 100 - auc_y(baseline)
    svg = (
        '<svg class="auc-svg" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">'
        f'{grid}<line x1="0" x2="100" y1="{base_y:.2f}" y2="{base_y:.2f}" class="ref-line"/>'
        f'<polyline points="{firm}" class="auc-line"/><polyline points="{loose}" class="auc-line loose"/></svg>'
    )
    ticks = "".join(
        f'<span class="tick" style="bottom:{auc_y(v):.1f}%">{v:.1f}</span>' for v in (0.6, 0.8, 1.0)
    )
    limits = "".join(
        f'<span class="limit" style="bottom:{v / csi_top * 100:.2f}%"><span>{label} {v:.2f}</span></span>'
        for v, label in ((CSI_WATCH, "watch"), (CSI_ACT, "investigate"))
    )
    start = next(d for d in data if d["month"] == spec["start"])
    legend = "".join(
        f'<li><span class="key s-{status}"></span>{label}</li>'
        for status, label in (("green", "Green"), ("amber", "Amber"), ("red", "Red"),
                              ("pending", "Pending, labels not mature"))
    )
    fields = "".join(
        f'<div><dt data-f="{key}Label">{esc(label)}</dt><dd data-f="{key}">{esc(value)}</dd></div>'
        for key, label, value in (
            ("auc", start["aucLabel"], start["auc"]),
            ("caught", "Fraud cases caught", start["caught"]),
            ("psi", "Score shift (PSI)", start["psi"]),
            ("csi", "Largest input shift (CSI)", start["csi"]),
        )
    )
    return f"""<figure class="evidence monitor" data-monitor>
  <div class="monitor-head">
    <p class="evidence-title">{esc(spec["title"])}</p>
    <p class="monitor-hint">{esc(spec["hint"])}</p>
    <button type="button" class="replay" data-replay hidden>Replay the year</button>
  </div>
  <p class="panel-label">Ranking power (AUC)</p>
  <div class="monitor-plot" style="--n:{count}">
    <div class="auc-axis" aria-hidden="true">{ticks}</div>
    <div class="auc-layer" aria-hidden="true">{svg}<span class="ref-label" style="bottom:{auc_y(baseline):.1f}%">baseline {baseline:.3f}</span></div>
    <p class="panel-label csi-label">Largest shift in any input (CSI)</p>
    <div class="csi-layer" aria-hidden="true">{limits}</div>
    <div class="months" role="group" aria-label="Months">{"".join(months)}</div>
  </div>
  <ul class="monitor-legend">{legend}</ul>
  <div class="monitor-detail" data-detail aria-live="polite">
    <p class="detail-head"><span class="pill s-{start["status"]}" data-f="pill"><span class="key"></span><span data-f="statusLabel">{start["statusLabel"]}</span></span><strong data-f="name">{start["name"]}</strong></p>
    <p class="detail-note" data-f="note">{esc(start["note"])}</p>
    <dl class="detail-stats">{fields}</dl>
    <p class="detail-feature">Input that moved most: <code data-f="feature">{esc(start["feature"])}</code></p>
  </div>
  <figcaption>{inline(spec["caption"])}</figcaption>
  <script type="application/json" data-monitor-data>{json.dumps(data).replace("</", "<\\/")}</script>
</figure>"""


def section(spec: dict, project_dir: Path, root: str) -> str:
    parts = [f'<h2 id="{anchor(spec["h"])}">{esc(spec["h"])}</h2>']
    parts += [f"<p>{inline(text)}</p>" for text in spec.get("p", [])]
    if "monitor" in spec:
        parts.append(monitor(spec["monitor"], project_dir))
    for tag in ("ul", "ol"):
        if tag in spec:
            items = "".join(f"<li>{inline(item)}</li>" for item in spec[tag])
            parts.append(f"<{tag}>{items}</{tag}>")
    if "table" in spec:
        head = "".join(f'<th scope="col">{esc(cell)}</th>' for cell in spec["table"]["head"])
        rows = "".join(
            "<tr>" + "".join(f"<td>{inline(cell)}</td>" for cell in row) + "</tr>"
            for row in spec["table"]["rows"]
        )
        parts.append(
            '<div class="table-scroll" tabindex="0" role="region" '
            f'aria-label="{esc(spec["h"])}"><table><thead><tr>{head}</tr></thead>'
            f"<tbody>{rows}</tbody></table></div>"
        )
    if "code" in spec:
        parts.append(f'<pre><code>{esc(spec["code"])}</code></pre>')
    figs = "".join(figure(fig, project_dir, root) for fig in spec.get("figs", []))
    return f'<section class="block">{"".join(parts)}</section>{figs}'


def project_page(project: dict, previous: dict, following: dict) -> str:
    root = "../../"
    project_dir = ROOT / "projects" / project["slug"]
    buttons = "".join(
        f'<a class="btn{" btn-solid" if index == 0 else ""}" href="{url}">{esc(label)}</a>'
        for index, (label, url) in enumerate(project["links"])
    )
    hero_image = ""
    if "hero_image" in project:
        image = project["hero_image"]
        width, height = image["size"]
        hero_image = (
            f'<figure class="fig lead-shot"><img src="{root}{image["src"]}" '
            f'alt="{esc(image["alt"])}" width="{width}" height="{height}"></figure>'
        )
    check = ""
    if "check" in project:
        check = (
            '<figure class="evidence check"><p class="evidence-title">The check</p>'
            f'{bars(project["check"])}<figcaption>{inline(project["check"]["caption"])}</figcaption></figure>'
        )
    sections = "".join(section(spec, project_dir, root) for spec in project["sections"])
    contents = "".join(
        f'<li><a href="#{anchor(spec["h"])}">{esc(spec["h"])}</a></li>' for spec in project["sections"]
    )
    body = f"""
<article class="case">
  <header class="case-head">
    <div class="wrap">
      <p class="crumb"><a href="{root}#work">All work</a></p>
      <p class="kicker">{esc(project["kicker"])}</p>
      <h1 style="view-transition-name:title-{project["slug"]}">{esc(project["title"])}</h1>
      <p class="lede">{inline(project["summary"])}</p>
      <p class="context">{inline(project["context"])}</p>
      <p class="tools">{esc(", ".join(project["tools"]))}</p>
      <p class="actions">{buttons}</p>
    </div>
  </header>
  <div class="wrap case-body">
    <div class="case-main">
      {hero_image}
      {stats(project["stats"], "stats stat-strip")}
      {check}
      {sections}
    </div>
    <nav class="toc" aria-label="On this page" data-toc>
      <p>On this page</p>
      <ol>{contents}</ol>
    </nav>
  </div>
  <nav class="pager" aria-label="Other projects">
    <div class="wrap pager-inner">
      <a href="{project_url(previous["slug"], root)}"><span>Previous</span>{esc(previous["title"])}</a>
      <a href="{project_url(following["slug"], root)}"><span>Next</span>{esc(following["title"])}</a>
    </div>
  </nav>
</article>
"""
    return layout(
        title=f'{project["title"]} | {c.SITE["name"]}',
        description=project["finding"],
        body=body,
        root=root,
        path=f'projects/{project["slug"]}/',
        page="case",
    )


def not_found() -> str:
    body = f"""
<section class="hero">
  <div class="wrap">
    <h1>{words("That page isn't here.")}</h1>
    <p class="intro">The link may be old. Every project is listed on the home page.</p>
    <p class="actions"><a class="btn btn-solid" href="/">Go to the home page</a></p>
  </div>
</section>
"""
    # GitHub Pages serves 404.html from any path, so its links are absolute.
    return layout(
        title=f'Page not found | {c.SITE["name"]}',
        description="Page not found.",
        body=body,
        root="/",
        path="404.html",
    )


def main() -> None:
    written = []

    def write(relative: str, text: str) -> None:
        target = ROOT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        written.append(relative)

    write("index.html", home())
    write("404.html", not_found())
    count = len(c.PROJECTS)
    for index, project in enumerate(c.PROJECTS):
        previous = c.PROJECTS[(index - 1) % count]
        following = c.PROJECTS[(index + 1) % count]
        write(f'projects/{project["slug"]}/index.html', project_page(project, previous, following))

    for slugs in (slugs for _, slugs in c.SKILLS):
        missing = [slug for slug in slugs if slug not in BY_SLUG]
        if missing:
            raise SystemExit(f"SKILLS refers to unknown projects: {missing}")

    print(f"Wrote {len(written)} pages:")
    for relative in written:
        print(f"  {relative}")


if __name__ == "__main__":
    main()
