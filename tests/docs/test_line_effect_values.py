"""The line effects reference page's tables hold the values the code holds, row by row.

The classes table is compared with `LINE_CLASSES` and the water and road groups, the fields
table with the effect value types' fields, defaults and `EFFECT_RANGES`, the presets table with
`BUILT_IN_PRESETS`, and the draw order list with the group orders. The prose is not checked.
"""

import dataclasses
import re

from pyntpot.ink import Casing, Glow, PenCasing, Shadow
from pyntpot.ink.effect_types import EFFECT_RANGES
from pyntpot.maps.line_effects import BUILT_IN_PRESETS, LINE_CLASSES, ROAD_GROUP, WATER_GROUP

from support.site_pages import DOCS

PAGE = DOCS / "reference" / "line-effects.md"
_HEADING = re.compile(r"^## (?P<title>.+)$", re.MULTILINE)
_CODE = re.compile(r"`([^`]+)`")
_TYPES = {"casing": Casing, "glow": Glow, "shadow": Shadow, "pen casing": PenCasing}


def _sections() -> dict[str, str]:
    """Return the page's `##` sections by title, each holding its text to the next heading."""
    text = PAGE.read_text()
    marks = list(_HEADING.finditer(text))
    ends = [m.start() for m in marks[1:]] + [len(text)]
    return {m["title"]: text[m.end() : end] for m, end in zip(marks, ends, strict=True)}


def _rows(section: str) -> tuple[list[str], list[list[str]]]:
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


def test_the_line_effects_page_matches_the_presets_and_classes() -> None:
    """The classes, the digest each moves, the fields, the presets and the draw order are what the code holds."""
    sections = _sections()
    _check_classes(sections["Line classes"])
    _check_fields(sections["Effect fields"])
    _check_presets(sections["Preset expansions"])
    _check_draw_order(sections["Draw order"])


def _check_classes(section: str) -> None:
    """Each class is a row in draw order, with its table, group and the digests it moves."""
    header, rows = _rows(section)
    assert header == ["Class", "Table", "Group", "Digests it moves", "A change costs"]
    names = [_code(row[0]) for row in rows]
    assert names == [*WATER_GROUP, *ROAD_GROUP, "route"]
    assert set(names) == LINE_CLASSES
    for name, row in zip(names, rows, strict=True):
        if name == "route":
            assert (_code(row[1]), row[2], row[3]) == (
                "route_ink.effects",
                "route",
                "`digest` only",
            )
            assert "one compose" in row[4]
        else:
            group = "water" if name in WATER_GROUP else "road"
            assert (_code(row[1]), row[2]) == ("basemap.line_effects", group)
            assert re.findall(r"`(\w+)`", row[3]) == [
                "base_digest",
                "digest",
            ]
            assert "painted again" in row[4]


def _check_fields(section: str) -> None:
    """Each field row names a real field, its range from `EFFECT_RANGES` and its default."""
    header, rows = _rows(section)
    assert header == ["Effect", "Field", "Unit", "Range", "Default"]
    seen: dict[str, list[str]] = {}
    for effect, field, _, span, default in rows:
        cls = _TYPES[effect]
        fields = {f.name: f for f in dataclasses.fields(cls)}
        seen.setdefault(effect, []).append(_code(field))
        spec = fields[_code(field)]
        if _code(field) in EFFECT_RANGES:
            low, high = EFFECT_RANGES[_code(field)]
            assert span == f"{low:g} to {high:g}"
        else:
            assert span == ""
        built = getattr(cls(), spec.name)
        assert _code(default) == (str(built) if spec.name == "colour" else repr(built))
    for effect, cls in _TYPES.items():
        assert seen[effect] == [f.name for f in dataclasses.fields(cls)]


def _check_presets(section: str) -> None:
    """Each preset row is the named preset's one effect and its non-default numbers."""
    header, rows = _rows(section)
    assert header == ["Preset", "Effect", "Values"]
    assert [_code(row[0]) for row in rows] == list(BUILT_IN_PRESETS)
    for row in rows:
        (effect,) = BUILT_IN_PRESETS[_code(row[0])].effects
        assert row[1] == type(effect).__name__.lower()
        written = {name: float(value) for name, value in re.findall(r"`(\w+)` ([\d.]+)", row[2])}
        held = {
            f.name: getattr(effect, f.name)
            for f in dataclasses.fields(effect)
            if f.name != "colour" and getattr(effect, f.name) != f.default
        }
        assert written == held


def _check_draw_order(section: str) -> None:
    """The draw order lists the water group, then the road group, then the route, each group in its order."""
    steps = [line for line in section.splitlines() if re.match(r"\d\. ", line)]
    assert len(steps) == 3
    water, road, route = steps
    for step, group in ((water, WATER_GROUP), (road, ROAD_GROUP)):
        named = re.findall(r"`(\w+)`", step)
        assert named == list(group)
    assert "route" in route
