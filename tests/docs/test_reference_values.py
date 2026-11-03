"""The reference pages' tables and synopsis hold the values the code holds, cell by cell.

Each check reads its facts from the code and compares them with the page's cells: the
style-field tables with `Style.default()` and the group dataclasses, the command line's
synopsis with `build_parser()`'s usage, the pigment tables with `PIGMENTS` and its
neighbours, and the brush tables with the brush sheet's tables. Presence of a name is
`tests/architecture/test_reference_pages.py`'s check; this one checks what a page says
about it. Nothing here renders a page or builds the site.
"""

import argparse
import dataclasses
import json
import re
from collections.abc import Mapping, Sequence

from pyntpot.ink import PAINTERS_PIGMENTS, PAINTERS_TRANSPARENCY, PIGMENTS, TRANSPARENCY
from pyntpot.ink.brush import BRUSH_COLOURS, BRUSH_TREATMENTS, PEN_ROWS
from pyntpot.maps.cli import build_parser
from pyntpot.maps.style import Style

from support.site_pages import DOCS, fenced_blocks

REFERENCE = DOCS / "reference"

_GROUP_HEADING = re.compile(r"^## `(?P<group>\w+)`$", re.MULTILINE)
_GROUP_LINE = re.compile(
    r"^`(?P<cls>\w+)`(?:, from `(?P<pkg>pyntpot[\w.]*)`)?,"
    r" read as `Style\.default\(\)\.(?P<group>\w+)`\."
)
_CHOICES = re.compile(r'^`"\w+"`(?: or `"\w+"`)+$')
_SECTION = re.compile(r"^## ", re.MULTILINE)
_COLOUR_COLUMN = re.compile(r"`(?P<column>\w)` (?P<colour>#[0-9a-f]{6})")


def _tables(text: str) -> list[tuple[list[str], list[list[str]]]]:
    """Return each pipe table in `text` as its header cells and body rows, in page order."""
    tables: list[tuple[list[str], list[list[str]]]] = []
    rows: list[list[str]] = []
    for line in [*text.splitlines(), ""]:
        if line.startswith("|"):
            rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
        elif rows:
            tables.append((rows[0], rows[2:]))
            rows = []
    return tables


def _table(text: str, header: list[str]) -> list[list[str]]:
    """Return the body rows of the one table in `text` with exactly these header cells."""
    found = [rows for head, rows in _tables(text) if head == header]
    assert len(found) == 1, f"expected one table headed {header}, found {len(found)}"
    return found[0]


def _code(cell: str) -> str:
    """Return a cell's text with one pair of surrounding backticks removed."""
    return cell[1:-1] if len(cell) > 1 and cell[0] == cell[-1] == "`" else cell


def _is_record(value: object) -> bool:
    """Return whether a value is a mapping or a dataclass instance, which a theme writes as a table."""
    return isinstance(value, Mapping) or (
        dataclasses.is_dataclass(value) and not isinstance(value, type)
    )


_SCALAR_TYPES: tuple[tuple[type, str], ...] = (
    (bool, "boolean"),
    (int, "integer"),
    (float, "number"),
    (str, "string"),
)


def _scalar_value(value: bool | int | float | str) -> str:
    """Return how the style-field table writes a boolean, a number or a string."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    return repr(value)


def toml_value(value: object) -> str:
    """Return how the style-field table writes a default value."""
    if isinstance(value, bool | int | float | str):
        return _scalar_value(value)
    if _is_record(value):
        return "table"
    assert isinstance(value, Sequence), f"no TOML rendering for {value!r}"
    if value and all(_is_record(item) for item in value):
        return "table"
    return "[" + ", ".join(toml_value(item) for item in value) + "]"


def toml_type(value: object) -> str:
    """Return the TOML type the style-field table names for a default value."""
    for kind, name in _SCALAR_TYPES:
        if isinstance(value, kind):
            return name
    return "table" if toml_value(value) == "table" else "array"


def _collapse(usage: str) -> str:
    """Return a usage text with every whitespace run, newlines included, as one space, stripped."""
    return " ".join(usage.split())


def _parsers() -> list[argparse.ArgumentParser]:
    """Return the command's parser, then each subcommand parser in its subparsers' order."""
    parser = build_parser()
    found = [parser]
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for sub in action.choices.values():
                assert isinstance(sub, argparse.ArgumentParser)
                found.append(sub)
    return found


class TestStyleFieldTables:
    """Each group section of `style-fields.md` holds the group's fields, defaults, types and dataclass."""

    def _sections(self) -> dict[str, str]:
        """Return each group section's text after its heading, by group name."""
        text = (REFERENCE / "style-fields.md").read_text()
        sections: dict[str, str] = {}
        for heading in _GROUP_HEADING.finditer(text):
            rest = text[heading.end() :]
            following = _SECTION.search(rest)
            sections[heading["group"]] = rest[: following.start() if following else None]
        return sections

    def test_every_group_has_a_section(self) -> None:
        """The page has one section per style group, in the style's group order."""
        assert list(self._sections()) == list(Style.model_fields)

    def test_the_rows_are_the_group_fields(self) -> None:
        """Each section's field rows are the group dataclass's fields, none twice."""
        style = Style.default()
        wrong: list[str] = []
        for group, section in self._sections().items():
            rows = [_code(row[0]) for row in _table(section, ["Field", "Type", "Default", "Sets"])]
            fields = [spec.name for spec in dataclasses.fields(getattr(style, group))]
            if sorted(rows) != sorted(fields) or len(set(rows)) != len(rows):
                wrong.append(f"{group}: rows {rows}, fields {fields}")
        assert not wrong, "\n".join(wrong)

    def test_every_default_and_type_is_the_default_style(self) -> None:
        """Each row's Default and Type cells are the packaged default style's value and its TOML type."""
        style = Style.default()
        wrong: list[str] = []
        for group, section in self._sections().items():
            values = getattr(style, group)
            for field, kind, default, _ in _table(section, ["Field", "Type", "Default", "Sets"]):
                name = _code(field)
                if not hasattr(values, name):
                    continue
                value = getattr(values, name)
                if _code(default) != toml_value(value):
                    wrong.append(f"{group}.{name}: Default {default}, style {toml_value(value)}")
                choices = toml_type(value) == "string" and _CHOICES.match(kind) is not None
                if kind != toml_type(value) and not (choices and toml_value(value) in kind):
                    wrong.append(f"{group}.{name}: Type {kind}, style {toml_type(value)}")
        assert not wrong, "\n".join(wrong)

    def test_every_group_line_names_its_dataclass(self) -> None:
        """Each section's first line names the group's dataclass and how to read the group from a style."""
        style = Style.default()
        wrong: list[str] = []
        for group, section in self._sections().items():
            line = section.strip().splitlines()[0]
            found = _GROUP_LINE.match(line)
            cls = type(getattr(style, group)).__name__
            if found is None or found["cls"] != cls or found["group"] != group:
                wrong.append(f"{group}: {line!r} does not name `{cls}` read as `.{group}`")
        assert not wrong, "\n".join(wrong)

    def test_a_default_renders_as_the_table_writes_it(self) -> None:
        """Booleans, numbers, strings, records and sequences render as the page's Default cells do."""
        assert [
            toml_value(True),
            toml_value(26.0),
            toml_value(11),
            toml_value("Eryri"),
            toml_value({"wood": 0.05}),
            toml_value((80, 60)),
            toml_value(("name:cy", "name")),
            toml_value(()),
            toml_value(({"a": 1},)),
        ] == [
            "true",
            "26.0",
            "11",
            '"Eryri"',
            "table",
            "[80, 60]",
            '["name:cy", "name"]',
            "[]",
            "table",
        ]


class TestCliSynopsis:
    """The synopsis on `cli.md` is the parser's own usage, one line per parser."""

    def test_the_synopsis_is_the_parser_usage(self) -> None:
        """The synopsis block's lines equal each parser's usage, whitespace collapsed."""
        text = (REFERENCE / "cli.md").read_text()
        _, _, rest = text.partition("## Synopsis\n")
        block = fenced_blocks(rest)[0]
        lines = [_collapse(line) for line in block.code.splitlines() if line.strip()]
        expected = [_collapse(p.format_usage().removeprefix("usage: ")) for p in _parsers()]
        assert lines == expected

    def test_collapsing_joins_a_wrapped_usage(self) -> None:
        """The usage argparse wraps at 80 columns collapses to the one line it prints when wide."""
        wrapped = (
            "pyntpot map [-h] -o OUTPUT --cache CACHE --contact CONTACT\n"
            "                   [--style STYLE] [--margin-m MARGIN_M] [--no-attribution]\n"
            "                   track\n"
        )
        assert _collapse(wrapped) == (
            "pyntpot map [-h] -o OUTPUT --cache CACHE --contact CONTACT"
            " [--style STYLE] [--margin-m MARGIN_M] [--no-attribution] track"
        )


class TestPigmentTables:
    """The pigment tables on `pigments.md` hold the pigment tables' colours and transparencies."""

    def test_the_map_pigments_are_the_table(self) -> None:
        """Each strip row's colour and transparency are its key's in `PIGMENTS` and `TRANSPARENCY`."""
        text = (REFERENCE / "pigments.md").read_text()
        rows = _table(text, ["Strip", "Key", "Colour", "Transparency"])
        assert [_code(row[1]) for row in rows] == list(PIGMENTS)
        for _, key, colour, transparency in rows:
            assert _code(colour) == PIGMENTS[_code(key)], key
            assert float(transparency) == TRANSPARENCY[_code(key)], key

    def test_the_painters_pigments_are_the_table(self) -> None:
        """Each painter's row's colour and transparency are its key's in the painter's tables."""
        text = (REFERENCE / "pigments.md").read_text()
        rows = _table(text, ["Key", "Colour", "Transparency"])
        assert [_code(row[0]) for row in rows] == list(PAINTERS_PIGMENTS)
        for key, colour, transparency in rows:
            assert _code(colour) == PAINTERS_PIGMENTS[_code(key)], key
            assert float(transparency) == PAINTERS_TRANSPARENCY[_code(key)], key


class TestBrushTables:
    """The treatment and ink tables on `brushes.md` hold the brush sheet's tables."""

    def test_every_treatment_row_is_the_sheet(self) -> None:
        """Each treatment row's numbers are `BRUSH_TREATMENTS`' and its kind is nib exactly for `PEN_ROWS`."""
        text = (REFERENCE / "brushes.md").read_text()
        header = ["Row", "Darkness", "Bristles", "Gap", "Dry", "Texture", "Kind"]
        rows = _table(text, header)
        assert [_code(row[0]) for row in rows] == list(BRUSH_TREATMENTS)
        for row, darkness, bristles, gap, dry, texture, kind in rows:
            treatment = BRUSH_TREATMENTS[_code(row)]
            assert float(darkness) == treatment["darkness"], row
            assert int(bristles) == treatment["bristles"], row
            assert float(gap) == treatment["gap"], row
            assert float(dry) == treatment["dry"], row
            assert float(texture) == treatment["texture"], row
            assert (kind == "nib") == (_code(row) in PEN_ROWS), row

    def test_every_prefix_row_is_the_sheet_colours(self) -> None:
        """Each prefix row's column letters and colours are `BRUSH_COLOURS`' for the prefix, in order."""
        text = (REFERENCE / "brushes.md").read_text()
        rows = _table(text, ["Prefix", "Columns"])
        assert [_code(row[0]) for row in rows] == list(BRUSH_COLOURS)
        for prefix, columns in rows:
            found = {m["column"]: m["colour"] for m in _COLOUR_COLUMN.finditer(columns)}
            assert list(found.items()) == list(BRUSH_COLOURS[_code(prefix)].items()), prefix
