"""The site's nav and its section index pages agree, and `mkdocs.yml` has the site's shape.

Each nav section that opens with an `index.md` lists its pages in nav order. The
performance log is a maintainer runbook, not a site page. The strict build validates
anchors, with `nav:` the file's last top-level key, and the snippet includes directory is
excluded from the site.
"""

import re

from support.site_pages import DOCS, MKDOCS, NavEntry, excluded, links, nav, resolve, site_pages

_TOP_LEVEL_KEY = re.compile(r"^(?P<key>[A-Za-z_]\w*):", re.MULTILINE)


def _section_pages(entries: list[NavEntry], section: tuple[str, ...], index: str) -> list[str]:
    """Return the pages a section's index lists: its own pages, then each subsection's index, in nav order."""
    pages: list[str] = []
    opened: set[tuple[str, ...]] = set()
    for entry in entries:
        if entry.sections == section:
            if entry.path != index:
                pages.append(entry.path)
        elif len(entry.sections) == len(section) + 1 and entry.sections[:-1] == section:
            if entry.sections not in opened and entry.path.endswith("index.md"):
                pages.append(entry.path)
            opened.add(entry.sections)
    return pages


def _indexed_sections(entries: list[NavEntry]) -> list[tuple[tuple[str, ...], str]]:
    """Return each nav section whose first entry is an `index.md`, with that index's path."""
    seen: set[tuple[str, ...]] = set()
    sections: list[tuple[tuple[str, ...], str]] = []
    for entry in entries:
        if entry.sections and entry.sections not in seen:
            seen.add(entry.sections)
            if entry.path.endswith("index.md"):
                sections.append((entry.sections, entry.path))
    return sections


def test_every_section_index_lists_its_pages_in_nav_order() -> None:
    """Each section's index links its pages, first occurrences only, in the nav's order."""
    entries = nav(MKDOCS.read_text())
    sections = _indexed_sections(entries)
    assert sections, "the nav has no section that opens with an index page"
    wrong: list[str] = []
    for section, index in sections:
        expected = [DOCS / p for p in _section_pages(entries, section, index)]
        index_page = DOCS / index
        targets = (resolve(index_page, href) for href in links(index_page.read_text()))
        listed = list(dict.fromkeys(t for t in targets if t in expected))
        if listed != expected:
            names = [p.relative_to(DOCS).as_posix() for p in listed]
            want = [p.relative_to(DOCS).as_posix() for p in expected]
            wrong.append(f"{' > '.join(section)}: {index} lists {names}, nav has {want}")
    assert not wrong, "\n".join(wrong)


def test_the_performance_log_is_a_runbook_and_no_site_page_links_it() -> None:
    """The performance log lives in `docs/runbooks/`, off the nav and linked from no site page."""
    assert (DOCS / "runbooks" / "performance.md").is_file()
    in_nav = [e.path for e in nav(MKDOCS.read_text()) if e.path.endswith("performance.md")]
    assert not in_nav, f"nav entries for the performance log: {in_nav}"
    linking = [
        page.relative_to(DOCS).as_posix()
        for page in site_pages()
        for href in links(page.read_text())
        if (target := resolve(page, href)) is not None and target.name == "performance.md"
    ]
    assert not linking, f"site pages linking the performance log: {linking}"


def test_the_strict_build_validates_anchors() -> None:
    """`mkdocs.yml` sets `validation: anchors: warn` before `nav:`, and `nav:` is the last key."""
    text = MKDOCS.read_text()
    keys = [found["key"] for found in _TOP_LEVEL_KEY.finditer(text)]
    assert keys[-1] == "nav", f"the last top-level key is {keys[-1]!r}, not 'nav'"
    assert "validation" in keys, "mkdocs.yml has no `validation:` key"
    assert keys.index("validation") < keys.index("nav")
    block = text.split("\nvalidation:\n", maxsplit=1)[1]
    block = block[: next(_TOP_LEVEL_KEY.finditer(block)).start()]
    assert re.search(r"^\s+anchors:\s*warn\s*$", block, re.MULTILINE), (
        "`validation:` does not set `anchors: warn`"
    )


def test_the_includes_directory_is_not_a_site_page() -> None:
    """`exclude_docs` lists `includes/`, and no site page sits under `docs/includes/`."""
    assert "includes/" in excluded(MKDOCS.read_text())
    under = [p for p in site_pages() if p.is_relative_to(DOCS / "includes")]
    assert not under, f"site pages under docs/includes/: {under}"
