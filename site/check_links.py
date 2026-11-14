"""
Checks the generated site for broken internal links and missing images.

    python site/check_links.py

Every href and src on every generated page must point at a file that exists
in the repository, and every #anchor must exist on its target page. External
links are listed but not fetched.
"""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent


class Collector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if value is None:
                continue
            if name in ("href", "src"):
                self.links.append(value)
            elif name == "id":
                self.ids.add(value)


def parse(path: Path) -> Collector:
    collector = Collector()
    collector.feed(path.read_text(encoding="utf-8"))
    return collector


def main() -> int:
    pages = [ROOT / "index.html", ROOT / "404.html", *sorted(ROOT.glob("projects/*/index.html"))]
    parsed = {page: parse(page) for page in pages}
    problems: list[str] = []
    external: set[str] = set()

    for page, collector in parsed.items():
        for link in collector.links:
            parts = urlsplit(link)
            if parts.scheme in ("http", "https", "mailto"):
                external.add(link)
                continue
            path = unquote(parts.path)
            if path.startswith("/"):
                target = ROOT / path.lstrip("/")
            else:
                target = (page.parent / path).resolve() if path else page
            if target.is_dir():
                target = target / "index.html"
            where = page.relative_to(ROOT)
            if not target.exists():
                problems.append(f"{where}: {link} does not exist")
            elif parts.fragment and target.suffix == ".html":
                ids = parsed[target].ids if target in parsed else parse(target).ids
                if parts.fragment not in ids:
                    problems.append(f"{where}: {link} has no matching id")

    print(f"Checked {len(pages)} pages, {sum(len(c.links) for c in parsed.values())} links.")
    print(f"External links (not fetched): {len(external)}")
    for problem in problems:
        print(f"  BROKEN  {problem}")
    if not problems:
        print("No broken internal links.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
