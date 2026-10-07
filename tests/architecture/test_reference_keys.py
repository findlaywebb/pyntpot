"""Reference gate: every reference entry's sites cite its key, and every cited key has an entry."""

import ast
import re
from pathlib import Path

import pytest

from ._ast_checks import PACKAGES, REPO_ROOT, _source_files

REFERENCES = REPO_ROOT / "docs" / "explanation" / "references.md"

_ENTRY_HEADING = re.compile(r"^## `([a-z][a-z0-9-]*)`")
_IMPLEMENTED_IN = "- Implemented in: "
_DOTTED_PATH = re.compile(r"`([A-Za-z_][\w.]*)`")
_CITATION = re.compile(
    r"^Source: `([a-z][a-z0-9-]*)` in docs/explanation/references\.md\.$", re.MULTILINE
)


def entries(text: str) -> dict[str, list[str]]:
    """Map each entry key in ``references.md`` text to its ``Implemented in:`` dotted paths.

    Raises:
        ValueError: A key heading appears more than once.
    """
    parsed: dict[str, list[str]] = {}
    key: str | None = None
    for line in text.splitlines():
        if line.startswith("## "):
            heading = _ENTRY_HEADING.match(line)
            key = str(heading.group(1)) if heading else None
            if key is not None:
                if key in parsed:
                    msg = f"references.md has two entries keyed {key!r}"
                    raise ValueError(msg)
                parsed[key] = []
        elif key is not None and line.startswith(_IMPLEMENTED_IN):
            parsed[key].extend(_DOTTED_PATH.findall(line[len(_IMPLEMENTED_IN) :]))
    return parsed


def entries_without_sites(parsed: dict[str, list[str]]) -> list[str]:
    """Return, sorted, every key whose list of implementing paths is empty."""
    return sorted(key for key, paths in parsed.items() if not paths)


_DocOwner = ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef


def _keys_in(node: _DocOwner) -> list[str]:
    doc = ast.get_docstring(node) or ""
    return [str(key) for key in _CITATION.findall(doc)]


def cited_keys(module: str, tree: ast.Module) -> dict[str, list[str]]:
    """Map qualified names in one module to the keys their docstrings cite.

    Walks the module docstring, top-level functions and classes, and the
    methods defined directly in those classes; nested functions are never
    sites and are not read. Names that cite nothing are left out.
    """
    found: dict[str, list[str]] = {}
    sites: list[tuple[str, _DocOwner]] = [(module, tree)]
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            sites.append((f"{module}.{node.name}", node))
        if isinstance(node, ast.ClassDef):
            sites.extend(
                (f"{module}.{node.name}.{member.name}", member)
                for member in node.body
                if isinstance(member, ast.FunctionDef | ast.AsyncFunctionDef)
            )
    for name, node in sites:
        keys = _keys_in(node)
        if keys:
            found[name] = keys
    return found


def _module_name(path: Path) -> str:
    parts = list(path.relative_to(PACKAGES).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _trees() -> dict[str, ast.Module]:
    return {
        _module_name(path): ast.parse(path.read_text(), filename=str(path))
        for path in _source_files(PACKAGES)
    }


def _all_citations() -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for module, tree in _trees().items():
        found.update(cited_keys(module, tree))
    return found


def _resolve(dotted: str, trees: dict[str, ast.Module]) -> str | None:
    """Return the qualified site name a dotted path resolves to by file, or None."""
    parts = dotted.split(".")
    for cut in range(len(parts), 0, -1):
        module = ".".join(parts[:cut])
        if module not in trees:
            continue
        node: ast.AST = trees[module]
        for name in parts[cut:]:
            match = [
                child
                for child in getattr(node, "body", [])
                if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
                and child.name == name
            ]
            if not match:
                return None
            node = match[0]
        return dotted
    return None


def test_every_site_cites_its_key() -> None:
    """Every path in every reference entry resolves to a site whose docstring cites that key."""
    trees = _trees()
    citations = _all_citations()
    unresolved: list[str] = []
    uncited: list[str] = []
    for key, paths in entries(REFERENCES.read_text()).items():
        for path in paths:
            if _resolve(path, trees) is None:
                unresolved.append(f"{key}: {path}")
            elif key not in citations.get(path, []):
                uncited.append(f"{key}: {path}")
    assert not unresolved, f"Implemented in: paths that resolve to no site: {unresolved}"
    assert not uncited, f"sites that do not cite their entry's key: {uncited}"


def test_every_cited_key_has_an_entry_listing_the_site() -> None:
    """Every citation line in src names an entry, and that entry lists the citing site."""
    parsed = entries(REFERENCES.read_text())
    stray = [
        f"{site}: {key}"
        for site, keys in _all_citations().items()
        for key in keys
        if site not in parsed.get(key, [])
    ]
    assert not stray, f"citations with no entry listing the site: {stray}"


def test_every_entry_lists_a_site() -> None:
    """No entry in references.md lacks an Implemented in: site."""
    assert entries_without_sites(entries(REFERENCES.read_text())) == []


_TWO_ENTRY_FILE = """\
# References

Intro line.

## `zhang-suen` Zhang-Suen thinning

- Canonical source: Zhang, T. Y.; Suen, C. Y. (1984). A fast parallel algorithm.
- Design input: original design reading not recorded; the canonical source stands in.
- Implemented in: `pyntpot.letters.skeleton.thin`

## `kubelka-munk` Kubelka-Munk glazing

- Canonical source: Kubelka; Munk (1931). *Zeitschrift für technische Physik* 12, 593.
- Implemented in: `pyntpot.ink.pigment.km_rt`, `pyntpot.ink.pigment.km_plate`
- Note: one line.

## Read during design, no technique here

- Read during design: Stadia Maps (n.d.). Stamen Watercolor.
"""

_FAKE_ENTRY_FILE = """\
## `chaikin` Chaikin corner cutting

- Canonical source: Chaikin, G. M. (1974). An algorithm for high-speed curve generation.
- Implemented in: `pyntpot.ink.polyline.smooth`

## `fake-entry` Fake technique

- Canonical source: Nobody, A. (2000). Nothing.

## Read during design, no technique here

- Read during design: Stadia Maps (n.d.). Stamen Watercolor.
"""


def test_entries_parses_a_two_entry_file() -> None:
    """The parser maps both keyed headings to their paths and skips the closing section."""
    assert entries(_TWO_ENTRY_FILE) == {
        "zhang-suen": ["pyntpot.letters.skeleton.thin"],
        "kubelka-munk": ["pyntpot.ink.pigment.km_rt", "pyntpot.ink.pigment.km_plate"],
    }


_DUPLICATED_ENTRY_FILE = """\
## `chaikin` Chaikin corner cutting

- Implemented in: `pyntpot.ink.polyline.smooth`

## `chaikin` Chaikin corner cutting, again

- Implemented in: `pyntpot.letters.skeleton.thin`
"""


def test_entries_rejects_a_duplicated_key_heading() -> None:
    """A key heading that appears twice is an error, not a silent overwrite of the first's paths."""
    with pytest.raises(ValueError, match="chaikin"):
        entries(_DUPLICATED_ENTRY_FILE)


def test_entries_without_sites_names_an_entry_with_no_site() -> None:
    """An entry with no Implemented in: line parses to an empty list and is named."""
    parsed = entries(_FAKE_ENTRY_FILE)
    assert parsed["fake-entry"] == []
    assert entries_without_sites(parsed) == ["fake-entry"]


def test_cited_keys_reads_a_citation_line() -> None:
    """Citation lines are read from module, function, class and method docstrings, not nested ones."""
    source = '''\
"""Module.

Source: `fbm` in docs/explanation/references.md.
"""


def smooth():
    """Smooth a line.

    Source: `chaikin` in docs/explanation/references.md.
    Source: `catmull-rom` in docs/explanation/references.md.

    Returns:
        The line.
    """

    def inner():
        """Inner.

        Source: `nested-key` in docs/explanation/references.md.
        """


class Sheet:
    """A sheet."""

    def pits(self):
        """Pits.

        Source: `granulation` in docs/explanation/references.md.
        """
'''
    assert cited_keys("pyntpot.ink.demo", ast.parse(source)) == {
        "pyntpot.ink.demo": ["fbm"],
        "pyntpot.ink.demo.smooth": ["chaikin", "catmull-rom"],
        "pyntpot.ink.demo.Sheet.pits": ["granulation"],
    }
