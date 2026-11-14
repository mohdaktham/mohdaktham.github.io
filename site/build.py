"""
Builds the portfolio site.

    python site/build.py

Reads the text in site/content.py and writes index.html, 404.html and one
case-study page per project (projects/<slug>/index.html). It uses only the
Python standard library, and the generated pages are committed, so GitHub
Pages serves them as they are with no build step of its own.
"""

from __future__ import annotations

import html
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


# -- evidence: bars, stats and images ---------------------------------------

def bars(spec: dict) -> str:
    top = spec.get("max") or max(bar["value"] for bar in spec["bars"])
    summary = "; ".join(f'{bar["label"]} {bar["display"]}' for bar in spec["bars"])
    rows = "".join(
        f'<div class="bar"><span class="bar-label">{esc(bar["label"])}</span>'
        f'<span class="bar-track"><span class="bar-fill tone-{bar["tone"]}" '
        f'style="width:{bar["value"] / top * 100:.1f}%"></span></span>'
        f'<span class="bar-value">{esc(bar["display"])}</span></div>'
        for bar in spec["bars"]
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

def layout(*, title: str, description: str, body: str, root: str, path: str) -> str:
    home = root or "./"
    url = f'{c.SITE["url"]}/{path}'
    return f"""<!doctype html>
<html lang="en">
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
<script>try{{var t=localStorage.getItem("theme");if(t)document.documentElement.dataset.theme=t}}catch(e){{}}</script>
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
    return f"""
    <article class="work-row">
      <div class="claim">
        <p class="kicker">{esc(project["kicker"])}</p>
        <h3><a href="{url}">{esc(project["title"])}</a></h3>
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
    for skill, slugs in c.SKILLS:
        cells = "".join(
            '<td><span class="mark" aria-label="yes"></span></td>'
            if p["slug"] in slugs
            else '<td><span class="sr">no</span></td>'
            for p in c.PROJECTS
        )
        rows.append(f'<tr><th scope="row">{esc(skill)}</th>{cells}</tr>')
    return (
        '<div class="matrix-scroll" tabindex="0" role="region" aria-label="Skills by project">'
        f'<table class="matrix"><thead><tr><td></td>{head}</tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div>'
    )


def home() -> str:
    hero = c.HERO_EVIDENCE
    link_text, link_slug = hero["link"]
    rows = "".join(work_row(p) for p in c.PROJECTS)
    more = "".join(
        f'<li><p class="kicker">{esc(m["kicker"])}</p>'
        f'<h3><a href="{m["url"]}">{esc(m["title"])}</a></h3><p>{inline(m["text"])}</p></li>'
        for m in c.MORE
    )
    toolkit = "".join(f"<div><dt>{esc(name)}</dt><dd>{esc(text)}</dd></div>" for name, text in c.TOOLKIT)
    about = "".join(f"<p>{inline(text)}</p>" for text in c.ABOUT)
    body = f"""
<section class="hero">
  <div class="wrap hero-grid">
    <div>
      <h1>{esc(c.SITE["headline"])}</h1>
      <p class="intro">{inline(c.SITE["intro"])}</p>
      <p class="actions">
        <a class="btn btn-solid" href="mailto:{c.SITE["email"]}">Email me</a>
        <a class="btn" href="{c.SITE["linkedin"]}">LinkedIn</a>
        <a class="btn" href="{c.SITE["github"]}">GitHub</a>
      </p>
    </div>
    <figure class="evidence hero-evidence">
      <p class="evidence-title">{esc(hero["title"])}</p>
      {bars(hero)}
      <figcaption>{inline(hero["caption"])} <a href="{project_url(link_slug, "")}">{esc(link_text)}</a></figcaption>
    </figure>
  </div>
</section>

<section id="work" class="section">
  <div class="wrap">
    <div class="section-head">
      <h2>Selected work</h2>
      <p>Each project says what it found, and beside it, the check behind the claim.</p>
    </div>
    <div class="work">{rows}
    </div>
  </div>
</section>

<section id="more" class="section">
  <div class="wrap">
    <div class="section-head">
      <h2>More on GitHub</h2>
      <p>Graduate coursework and research, with the code in its own repositories.</p>
    </div>
    <ul class="more">{more}</ul>
  </div>
</section>

<section id="skills" class="section">
  <div class="wrap">
    <div class="section-head">
      <h2>Skills, and where to see them</h2>
      <p>A filled square means the project uses that skill. Choose a project name to open it.</p>
    </div>
    {skills_matrix()}
    <dl class="toolkit">{toolkit}</dl>
  </div>
</section>

<section id="about" class="section">
  <div class="wrap about">
    <div>
      <h2>About</h2>
      {about}
    </div>
    <div>
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


def section(spec: dict, project_dir: Path, root: str) -> str:
    parts = [f'<h2 id="{anchor(spec["h"])}">{esc(spec["h"])}</h2>']
    parts += [f"<p>{inline(text)}</p>" for text in spec.get("p", [])]
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
      <h1>{esc(project["title"])}</h1>
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
    <nav class="toc" aria-label="On this page">
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
    )


def not_found() -> str:
    body = """
<section class="hero">
  <div class="wrap">
    <h1>That page isn't here.</h1>
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
