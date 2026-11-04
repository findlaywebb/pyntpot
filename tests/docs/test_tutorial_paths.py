"""The tutorials read as one path, in nav order, and each page leads on past the tutorials.

Each tutorial page, taken in the nav's order under "Tutorials", ends with a `Next:` line
linking the next page; the last one links the how-to guides. Each tutorial page that is
not a section index links a how-to guide, a reference page or an explanation. A new
tutorial page in the nav is covered with no test edit. This does not check link anchors
(the strict build does) or the wording around the links.
"""

import re
from pathlib import Path

from support.site_pages import DOCS, MKDOCS, links, nav, resolve

_NEXT = re.compile(r"^Next: \[[^\]]+\]\((?P<href>[^)]+)\)")
_LEAD_ON = tuple(DOCS / part for part in ("how-to", "reference", "explanation"))


def _tutorial_pages() -> list[Path]:
    """Return the tutorial pages in nav order."""
    entries = nav(MKDOCS.read_text())
    return [DOCS / entry.path for entry in entries if entry.sections[:1] == ("Tutorials",)]


def test_every_tutorial_page_ends_with_the_next_page_in_nav_order() -> None:
    """Each tutorial page's last line is `Next:` linking the next page; the last links the how-to index."""
    pages = _tutorial_pages()
    assert pages, "the nav has no Tutorials section"
    wrong: list[str] = []
    for page, following in zip(pages, [*pages[1:], DOCS / "how-to" / "index.md"], strict=True):
        last = next(line for line in reversed(page.read_text().splitlines()) if line.strip())
        found = _NEXT.match(last)
        target = resolve(page, found["href"]) if found else None
        if target != following.resolve():
            wrong.append(
                f"{page.relative_to(DOCS)}: ends {last!r}, want a Next: to {following.relative_to(DOCS)}"
            )
    assert not wrong, "\n".join(wrong)


def test_every_tutorial_page_but_an_index_leads_on_to_a_guide_reference_or_explanation() -> None:
    """Each non-index tutorial page links a page under `how-to/`, `reference/` or `explanation/`."""
    pages = [page for page in _tutorial_pages() if page.name != "index.md"]
    assert pages, "the nav has no tutorial pages besides indexes"
    stranded: list[str] = []
    for page in pages:
        targets = (resolve(page, href) for href in links(page.read_text()))
        if not any(t is not None and t.is_relative_to(root) for t in targets for root in _LEAD_ON):
            stranded.append(page.relative_to(DOCS).as_posix())
    assert not stranded, f"tutorial pages that lead nowhere past the tutorials: {stranded}"
