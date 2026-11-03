"""The glossary's reader and generator: `GLOSSARY.md` in, the site's glossary files out.

The one reader of `GLOSSARY.md`'s format. The file holds three sections: "Terms a reader
meets" (`###` groups of Term, Meaning, In the code, Tooltip tables), "Terms a contributor
meets" (one Term, Meaning, In the code table) and "Retired words" (Retired, Say instead).
From it this module writes two committed files: `docs/reference/glossary.md`, the site's
glossary page (reader terms only, an anchor `term-<slug>` per term), and
`docs/includes/abbreviations.md`, one `*[form]: meaning` definition per Tooltip form,
which the site appends to every page so `abbr` underlines each form.

Key names:

- `Term`, `Retired`, `Glossary`: the parsed rows.
- `parse`: `GLOSSARY.md`'s text to a `Glossary`, refusing any other shape.
- `plain`, `anchor`: a Meaning without Markdown, and a term's anchor id.
- `glossary_page`, `abbreviations`: the two files' text.
- `main`: writes both files; run as `PYTHONPATH=tests uv run python -m support.glossary`.

Stdlib only. It does not build the site, resolve the "In the code" names, or check that a
Tooltip form avoids everyday words; the docs tests do those. Cells hold no `|`; a reader
row's Tooltip is `no` (no forms) or comma-separated forms, never empty.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from support import REPO_ROOT

_log = logging.getLogger(__name__)

#: The command that regenerates both files from `GLOSSARY.md`.
REGENERATE = "PYTHONPATH=tests uv run python -m support.glossary"

#: Words too common to underline on every page: never a Tooltip form.
EVERYDAY_WORDS = frozenset(
    {
        "map", "maps", "card", "cards", "route", "routes", "hand", "wash", "washes",
        "track", "tracks", "plate", "plates", "style", "theme", "sheet", "brush", "span",
        "water", "mark", "setting", "terms", "reference", "label", "labels", "place",
        "places", "face", "layers", "density", "pigment", "credit", "manifest",
        "candidate", "canvas", "lettering", "tip", "body", "pool", "trace", "landmark",
        "landmarks", "provider", "annotations", "edge", "line", "name", "names",
    }
)  # fmt: skip

_GLOSSARY = REPO_ROOT / "GLOSSARY.md"
_PAGE = REPO_ROOT / "docs" / "reference" / "glossary.md"
_ABBREVIATIONS = REPO_ROOT / "docs" / "includes" / "abbreviations.md"

_COMMENT = f"<!-- Generated from GLOSSARY.md by tests/support/glossary.py. Edit GLOSSARY.md, then run: {REGENERATE} -->"
_INTRO = (
    "Every term these docs use, what it means and where it lives in the code. The docs use "
    "one name for each of these and no other. A term underlined on a page shows its meaning "
    "when you point at it. The source is "
    "[GLOSSARY.md](https://github.com/findlaywebb/pyntpot/blob/main/GLOSSARY.md) in the "
    "repository."
)

_READER = "Terms a reader meets"
_CONTRIBUTOR = "Terms a contributor meets"
_RETIRED = "Retired words"
_HEADERS = {
    _READER: ("Term", "Meaning", "In the code", "Tooltip"),
    _CONTRIBUTOR: ("Term", "Meaning", "In the code"),
    _RETIRED: ("Retired", "Say instead"),
}
_SEPARATOR = re.compile(r"^\|(?:\s*:?-+:?\s*\|)+$")
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")


@dataclass(frozen=True)
class Term:
    """One glossary row: its name, Meaning (Markdown), "In the code" names, Tooltip forms, section and group.

    `code` holds the bare dotted names, backticks stripped, in cell order. `tooltip` is
    empty for a contributor row and for a reader row whose Tooltip is `no`. `group` is the
    reader `###` heading, empty for a contributor row.
    """

    name: str
    meaning: str
    code: tuple[str, ...]
    tooltip: tuple[str, ...]
    audience: Literal["reader", "contributor"]
    group: str


@dataclass(frozen=True)
class Retired:
    """One retired word and what to say instead."""

    word: str
    instead: str


@dataclass(frozen=True)
class Glossary:
    """Every term in file order, reader then contributor, and the retired words."""

    terms: tuple[Term, ...]
    retired: tuple[Retired, ...]


def _cells(line: str) -> tuple[str, ...]:
    """Return a table line's cells, stripped."""
    return tuple(cell.strip() for cell in line.strip().strip("|").split("|"))


def _names(cell: str) -> tuple[str, ...]:
    """Return a comma-separated cell's entries, backticks stripped, empty for an empty cell."""
    return tuple(part.strip().strip("`") for part in cell.split(",") if part.strip())


def _row(section: str, group: str, cells: tuple[str, ...], number: int) -> Term | Retired:
    """Return the record one table row holds, raising `ValueError` on a shape the section forbids."""
    if section == _RETIRED:
        return Retired(word=cells[0], instead=cells[1])
    if section == _CONTRIBUTOR:
        return Term(cells[0], cells[1], _names(cells[2]), (), "contributor", "")
    if not group:
        raise ValueError(f"GLOSSARY.md line {number}: a reader row outside a ### group")
    if not cells[3]:
        raise ValueError(f"GLOSSARY.md line {number}: a reader row with an empty Tooltip")
    tooltip = () if cells[3] == "no" else _names(cells[3])
    return Term(cells[0], cells[1], _names(cells[2]), tooltip, "reader", group)


def _heading(line: str, number: int, section: str) -> tuple[str, str]:
    """Return the section and group a `##` or `###` heading opens, raising `ValueError` on one the format forbids."""
    if line.startswith("## "):
        name = line[3:].strip()
        if name not in _HEADERS:
            raise ValueError(f"GLOSSARY.md line {number}: unknown section {line!r}")
        return name, ""
    if section != _READER:
        raise ValueError(f"GLOSSARY.md line {number}: a group outside {_READER!r}")
    return section, line[4:].strip()


def _check_header(line: str, number: int, section: str) -> None:
    """Raise `ValueError` unless `line` is the header of `section`'s table."""
    if not section:
        raise ValueError(f"GLOSSARY.md line {number}: a table outside a section")
    if _cells(line) != _HEADERS[section]:
        raise ValueError(f"GLOSSARY.md line {number}: expected the header {_HEADERS[section]}")


def _table_row(line: str, number: int, section: str, group: str) -> Term | Retired:
    """Return the record a table row holds, raising `ValueError` on the wrong number of cells."""
    cells = _cells(line)
    if len(cells) != len(_HEADERS[section]):
        raise ValueError(
            f"GLOSSARY.md line {number}: {len(cells)} cells, expected {len(_HEADERS[section])}"
        )
    return _row(section, group, cells, number)


def parse(text: str) -> Glossary:
    """Return the glossary `text` holds.

    Raises:
        ValueError: naming the line, for an unknown `##` section, a `###` group outside the
            reader section, a table outside a section, a table header other than the
            section's, a row with the wrong number of cells, or a reader row whose Tooltip
            is empty.
    """
    section, group, header_seen = "", "", False
    records: list[Term | Retired] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if line.startswith(("## ", "### ")):
            section, group = _heading(line, number, section)
            header_seen = False
        elif not line.startswith("|"):
            header_seen = header_seen and bool(line.strip())
        elif not header_seen:
            _check_header(line, number, section)
            header_seen = True
        elif not _SEPARATOR.match(line.strip()):
            records.append(_table_row(line, number, section, group))
    return Glossary(
        terms=tuple(r for r in records if isinstance(r, Term)),
        retired=tuple(r for r in records if isinstance(r, Retired)),
    )


def plain(markdown: str) -> str:
    """Return `markdown` as plain text: backticks dropped, links to their text, emphasis dropped, whitespace collapsed."""
    text = _LINK.sub(r"\1", markdown.replace("`", ""))
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    return " ".join(text.split())


def anchor(term: str) -> str:
    """Return the anchor id of `term` on the glossary page: `term-` and its lowercased runs of `[a-z0-9]`, joined by `-`."""
    return "term-" + re.sub(r"[^a-z0-9]+", "-", term.lower()).strip("-")


def glossary_page(glossary: Glossary) -> str:
    """Return the site's glossary page: a section per reader group, a row per reader term with its anchor."""
    blocks = [f"{_COMMENT}\n# Glossary", _INTRO]
    readers = [term for term in glossary.terms if term.audience == "reader"]
    for group in dict.fromkeys(term.group for term in readers):
        rows = [
            f'| <span id="{anchor(t.name)}"></span>{t.name} | {t.meaning} | '
            + ", ".join(f"`{name}`" for name in t.code)
            + " |"
            for t in readers
            if t.group == group
        ]
        table = "| Term | Meaning | In the code |\n| --- | --- | --- |\n" + "\n".join(rows)
        blocks += [f"## {group}", table]
    return "\n\n".join(blocks) + "\n"


def abbreviations(glossary: Glossary) -> str:
    """Return the abbreviations file: one `*[form]: plain meaning` per Tooltip form, a blank line between.

    The blank lines keep `abbr`'s block parser fast: it is roughly quadratic over a dense
    run of definitions, and the site runs it on every page and every API docstring.
    """
    lines = [_COMMENT]
    lines += [f"*[{form}]: {plain(t.meaning)}" for t in glossary.terms for form in t.tooltip]
    return "\n\n".join(lines) + "\n"


def _write(path: Path, text: str) -> None:
    """Write `text` to `path`, creating its directory, and log the path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    _log.info("wrote %s", path.relative_to(REPO_ROOT))


def main() -> None:
    """Write the glossary page and the abbreviations file from `GLOSSARY.md`."""
    glossary = parse(_GLOSSARY.read_text(encoding="utf-8"))
    _write(_PAGE, glossary_page(glossary))
    _write(_ABBREVIATIONS, abbreviations(glossary))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
