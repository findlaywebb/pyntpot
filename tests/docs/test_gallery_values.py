"""The gallery pages' tables hold the values the code holds, cell by cell.

The pigment gallery's tables are compared with `PIGMENT_REGISTRY`, the glaze pairs with the
script's own pairs, and the palettes table with the bundled palettes. The brush gallery's
tables are compared with the brush tables: every id sits in the treatment row and colour
column its name says, under the ink the tables give that column. Presence of a name on a
page is `tests/docs/test_reference_pages.py`'s check; this one checks what the page says
about it.
"""

import re

import pytest

from pyntpot.ink import PIGMENT_REGISTRY
from pyntpot.ink.brush_sheet import BRUSH_COLOURS, BRUSH_TREATMENTS
from pyntpot.maps import Palette

from support.examples import load_example
from support.site_pages import DOCS

REFERENCE = DOCS / "reference"
_HEADING = re.compile(r"^## (?P<title>.+)$", re.MULTILINE)
_CODE = re.compile(r"`([^`]+)`")
_COLUMN_HEADER = re.compile(r"^`(?P<letter>\w)` (?P<ink>#[0-9a-f]{6})$")


def _sections(page: str) -> dict[str, str]:
    """Return a page's `##` sections by title, each holding its text to the next heading."""
    text = (REFERENCE / page).read_text()
    marks = list(_HEADING.finditer(text))
    ends = [m.start() for m in marks[1:]] + [len(text)]
    return {m["title"]: text[m.end() : end] for m, end in zip(marks, ends, strict=True)}


def _table(section: str) -> tuple[list[str], list[list[str]]]:
    """Return a section's pipe table as its header cells and body rows."""
    rows = [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in section.splitlines()
        if line.startswith("|")
    ]
    return rows[0], rows[2:]


def _code(cell: str) -> str:
    """Return the text of a cell that is one code span."""
    found = _CODE.fullmatch(cell)
    assert found is not None, f"{cell!r} is not one code span"
    return str(found[1])


def _code_all(cell: str) -> list[str]:
    """Return every code span of a cell, in order."""
    return [str(span) for span in _CODE.findall(cell)]


class TestPigmentGalleryTables:
    """The pigment gallery's tables match the registry, the glaze pairs and the palettes."""

    @pytest.mark.parametrize(
        ("title", "figure"),
        [("Map pigments", "roles"), ("Painter's pigments", "painters")],
        ids=["roles", "painters"],
    )
    def test_the_pigment_gallery_table_matches_the_registry(self, title, figure):
        """Each row of a wash table is the registry's pigment: name, hex, transparency and Colour Index code, in row order."""
        namespace = load_example("pigment_gallery", "example_pigment_gallery")
        names = namespace["wash_rows"](figure, 360).names
        header, rows = _table(_sections("pigment-gallery.md")[title])
        assert header == ["Row", "Name", "Colour", "Transparency", "Colour Index"]
        assert [_code(row[1]) for row in rows] == list(names)
        for index, row in enumerate(rows, start=1):
            pigment = PIGMENT_REGISTRY.get(_code(row[1]))
            assert row[0] == str(index)
            assert _code(row[2]) == str(pigment.colour)
            assert row[3] == f"{pigment.transparency:.2f}"
            expected = "none" if pigment.colour_index is None else f"`{pigment.colour_index}`"
            assert row[4] == expected

    def test_the_glaze_table_lists_the_scripts_pairs(self):
        """The glaze table's columns are the script's pairs, in order, first pigment then second."""
        pairs = load_example("pigment_gallery", "example_pigment_gallery")["GLAZE_PAIRS"]
        header, rows = _table(_sections("pigment-gallery.md")["Glaze pairs"])
        assert header == ["Column", "First", "Second"]
        assert [(_code(r[1]), _code(r[2])) for r in rows] == list(pairs)
        assert [r[0] for r in rows] == [str(i) for i in range(1, len(pairs) + 1)]

    def test_the_palettes_table_lists_every_alias_and_its_pigment(self):
        """The palettes table has a row for each alias of each bundled palette, naming the pigment (or hex) it binds."""
        header, rows = _table(_sections("pigment-gallery.md")["Palettes"])
        assert header == ["Palette", "Alias", "Pigment"]
        listed = [(_code(r[0]), _code(r[1]), _code(r[2])) for r in rows]
        expected = [
            (name, alias, pigment.name)
            for name in Palette.names()
            for alias, pigment in Palette.named(name).pigments.items()
        ]
        assert listed == expected


class TestBrushGalleryTables:
    """The brush gallery's tables put every id in its own treatment row and colour column."""

    @staticmethod
    def _cells() -> list[tuple[str, str, str, str]]:
        """Return (figure, id, column letter, ink) for every id in the page's tables."""
        found: list[tuple[str, str, str, str]] = []
        for title, section in _sections("brush-gallery.md").items():
            if "|" not in section:
                continue
            header, rows = _table(section)
            inks = [_COLUMN_HEADER.match(cell.replace("**", "")) for cell in header[1:]]
            assert all(inks), f"{title}: a column header is not `letter` #ink: {header}"
            for row in rows:
                for cell, ink in zip(row[1:], inks, strict=True):
                    assert ink is not None
                    for brush_id in _code_all(cell):
                        found.append((row[0], brush_id, ink["letter"], ink["ink"]))
        return found

    def test_every_id_sits_in_its_own_row_and_column_with_its_ink(self):
        """A table cell holds ids of its prefix, treatment number and column letter, and its header gives the column's ink."""
        for row, brush_id, letter, ink in self._cells():
            prefix, number = brush_id[:3], brush_id[3]
            assert row.split()[0] == number, (row, brush_id)
            assert brush_id.endswith(f"-{letter}"), (letter, brush_id)
            assert BRUSH_COLOURS[prefix][letter] == ink, (brush_id, ink)

    def test_the_brush_gallery_table_lists_every_id(self):
        """Every id the brush tables make is in exactly one table cell of the page."""
        listed = [brush_id for _, brush_id, _, _ in self._cells()]
        expected = {
            f"{prefix}{row}-{letter}"
            for prefix, columns in BRUSH_COLOURS.items()
            for letter in columns
            for row in BRUSH_TREATMENTS
        }
        assert len(listed) == len(set(listed)) == len(expected)
        assert set(listed) == expected

    def test_the_rows_name_the_eight_treatments_in_order(self):
        """Each table's first column is the treatment number and kind, 1 wet to 8 light nib."""
        kinds = load_example("brush_gallery", "example_brush_gallery")["KINDS"]
        expected = [f"{n} {kind}" for n, kind in enumerate(kinds, start=1)]
        for title, section in _sections("brush-gallery.md").items():
            if "|" in section:
                assert [row[0] for row in _table(section)[1]] == expected, title
