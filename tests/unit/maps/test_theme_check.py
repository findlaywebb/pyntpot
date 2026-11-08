"""Checking a theme against the model: keys, strict values, brush ids, colours and sub-tables."""

import dataclasses
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import pytest

from pyntpot.maps import Style
from pyntpot.maps.style import _groups
from pyntpot.maps.theme_check import RENAMED_KEYS, build_group, check_theme
from pyntpot.maps.theme_errors import ThemeProblem
from pyntpot.maps.theme_read import ThemeFile

from support.planted_groups import Glow, Ink
from support.theme_files import theme_file


@dataclass(frozen=True, kw_only=True)
class _Marks:
    """A test-local group: a dict field with no vocabulary, and a tuple of a `Literal`.

    Attributes:
        sizes: Any name to a size.
        kinds: Each mark's kind.
    """

    sizes: dict[str, float] = field(default_factory=dict)
    kinds: tuple[Literal["dot", "dash"], ...] = ()


def _check(
    text: str,
    groups: dict[str, type] | None = None,
    renamed: dict[tuple[str, ...], str] | None = None,
) -> tuple[dict[str, object], tuple[ThemeProblem, ...]]:
    """Check the inline theme `text` against `groups`, the style's own by default."""
    theme = theme_file(text)
    groups = _groups() if groups is None else groups
    if renamed is None:
        return check_theme(theme, groups)
    return check_theme(theme, groups, renamed=renamed)


def _found(text: str, groups: dict[str, type] | None = None) -> list[tuple[str, int | None, str]]:
    """Each problem checking `text` finds, as its key, line and message."""
    _table, problems = _check(text, groups)
    return [(problem.key, problem.line, problem.message) for problem in problems]


def _table(text: str, groups: dict[str, type] | None = None) -> dict[str, object]:
    """The checked table of `text`, asserting it has no problem."""
    table, problems = _check(text, groups)
    assert problems == ()
    return table


class TestTopLevelKeys:
    """The top level holds `extends` and the group names, and nothing else."""

    def test_extends_and_a_group_are_kept(self):
        """A valid `extends` and group come back as given."""
        table = _table("extends: sepia\nwash:\n  blooms: false\n")
        assert table == {"extends": "sepia", "wash": {"blooms": False}}

    def test_extends_must_be_a_string(self):
        """An `extends` that is not a string is refused and dropped."""
        table, problems = _check("extends: 5\n")
        assert table == {}
        assert [(p.key, p.line, p.message) for p in problems] == [
            ("extends", 1, "extends is a theme name or a .yaml path")
        ]

    def test_an_unknown_group_suggests_the_nearest(self):
        """A misspelt group name is refused with the group it was nearest."""
        assert _found("wsh:\n  blooms: false\n") == [("wsh", 1, "unknown key; did you mean wash?")]

    def test_an_unknown_group_with_no_near_name(self):
        """A group name near nothing is refused with no suggestion."""
        assert _found("zzzzzz: 1\n") == [("zzzzzz", 1, "unknown key")]

    def test_a_group_given_a_leaf_is_refused(self):
        """A group set to a scalar is told it is a table of keys."""
        assert _found("wash: 5\n") == [("wash", 1, "is a table of keys")]


class TestUnknownKeys:
    """An unknown key at any level is refused, with the nearest known key when there is one."""

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("wash:\n  blom: true\n", ("wash.blom", 2, "unknown key; did you mean blooms?")),
            (
                "cover:\n  cover_cfg:\n    wod: [0.1, 0.2]\n",
                ("cover.cover_cfg.wod", 3, "unknown key; did you mean wood?"),
            ),
            (
                "brush:\n  brush_overrides:\n    lane:\n      jiter_px: 0.3\n",
                ("brush.brush_overrides.lane.jiter_px", 4, "unknown key; did you mean jitter_px?"),
            ),
            (
                "brush:\n  brush_overrides:\n    lnae:\n      pool: 1.0\n",
                ("brush.brush_overrides.lnae", 3, "unknown key; did you mean lane?"),
            ),
            ("wash:\n  qqqqqqq: 1\n", ("wash.qqqqqqq", 2, "unknown key")),
        ],
        ids=["group-key", "dict-entry", "override-key", "override-entry", "no-suggestion"],
    )
    def test_an_unknown_key(self, text: str, expected: tuple[str, int, str]):
        """The unknown key is named by its dotted path and line, with its suggestion."""
        assert _found(text) == [expected]

    def test_a_dict_field_given_a_leaf_is_refused(self):
        """A dict field set to a scalar is told it is a table of keys."""
        assert _found("cover:\n  pigments: red\n") == [("cover.pigments", 2, "is a table of keys")]

    def test_an_entry_after_an_unknown_entry_is_checked(self):
        """An unknown entry of a dict field leaves the entries after it checked and kept."""
        table, problems = _check("cover:\n  pigments:\n    wod: '#556b2f'\n    wood: '#556b2f'\n")
        assert [(p.key, p.line) for p in problems] == [("cover.pigments.wod", 3)]
        assert table == {"cover": {"pigments": {"wood": "#556b2f"}}}

    def test_an_override_entry_given_a_leaf_is_refused(self):
        """A `brush_overrides` entry set to a scalar is told it is a table of keys."""
        found = _found("brush:\n  brush_overrides:\n    lane: 1\n")
        assert found == [("brush.brush_overrides.lane", 3, "is a table of keys")]

    def test_a_renamed_key_names_its_new_name(self):
        """A key in the renamed table is told what it is called now, with no suggestion."""
        table, problems = _check("wash:\n  bloom: true\n", renamed={("wash", "bloom"): "blooms"})
        assert table == {"wash": {}}
        assert [(p.key, p.line, p.message) for p in problems] == [
            ("wash.bloom", 2, "renamed to blooms")
        ]

    def test_the_old_route_ink_key_says_it_was_renamed(self):
        """The route ink's old key is refused at its line with its new name."""
        assert _found("route_ink:\n  style: pen\n") == [
            ("route_ink.style", 2, "renamed to drawn_as")
        ]

    def test_the_real_renamed_table_holds_the_route_ink_row(self):
        """The real renamed table holds the route ink's `drawn_as` row and nothing else."""
        assert RENAMED_KEYS == {("route_ink", "style"): "drawn_as"}


class TestStrictValues:
    """Each leaf is validated strictly against its field's type, with a message from its error."""

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("wash:\n  blooms: no\n", ("wash.blooms", 2, "'no' is not a boolean (true or false)")),
            ("wash:\n  blooms: 1\n", ("wash.blooms", 2, "1 is not a boolean (true or false)")),
            ('card:\n  display_px: "900"\n', ("card.display_px", 2, "'900' is not a whole number")),
            ("wash:\n  bloom_max: 5.5\n", ("wash.bloom_max", 2, "5.5 is not a whole number")),
            ('wash:\n  wet_bleed_px: "5"\n', ("wash.wet_bleed_px", 2, "'5' is not a number")),
            ("wash:\n  wet_bleed_px: true\n", ("wash.wet_bleed_px", 2, "True is not a number")),
            ("face:\n  label_face: 5\n", ("face.label_face", 2, "5 is not a string")),
            ("brush:\n  blotch_m: 5\n", ("brush.blotch_m", 2, "5 is not a list")),
            (
                "basemap:\n  roads: some\n",
                ("basemap.roads", 2, "'some' is not one of 'all', 'key', 'major'"),
            ),
            (
                "cover:\n  cover_cfg:\n    wood: [0.1, 0.2, 0.3]\n",
                ("cover.cover_cfg.wood", 3, "a list of 2 values, not 3"),
            ),
            ("card:\n  dark_grid: [80]\n", ("card.dark_grid", 2, "a list of 2 values, not 1")),
            (
                "card:\n  dark_grid: [80, 60, 40]\n",
                ("card.dark_grid", 2, "a list of 2 values, not 3"),
            ),
            ("card:\n  dark_grid: [80, x]\n", ("card.dark_grid", 2, "'x' is not a whole number")),
            (
                "brush:\n  brushes:\n    lane: LAN9-z\n",
                ("brush.brushes.lane", 3, "'LAN9-z' is not a brush on the sheet"),
            ),
            (
                "route:\n  route_pen_brush: MAJ9-a\n",
                ("route.route_pen_brush", 2, "'MAJ9-a' is not a brush on the sheet"),
            ),
            (
                "route_ink:\n  colour: red\n",
                ("route_ink.colour", 2, "'red' is not a # and six hexadecimal digits"),
            ),
            (
                "cover:\n  pigments:\n    wood: '#a8c28'\n",
                ("cover.pigments.wood", 3, "'#a8c28' is not a # and six hexadecimal digits"),
            ),
        ],
        ids=[
            "yaml-no",
            "int-for-bool",
            "string-for-int",
            "float-for-int",
            "string-for-float",
            "bool-for-float",
            "int-for-string",
            "leaf-for-tuple",
            "literal",
            "dict-entry-too-long",
            "too-short",
            "too-long",
            "tuple-item",
            "brush-id-entry",
            "brush-id",
            "colour",
            "colour-entry",
        ],
    )
    def test_a_wrong_value(self, text: str, expected: tuple[str, int, str]):
        """The wrong value is refused once, at its key and line, with what is wrong."""
        assert _found(text) == [expected]

    def test_drawn_as_takes_pen_or_solid(self):
        """A route ink `drawn_as` other than `pen` or `solid` is refused with both choices."""
        assert _found("route_ink:\n  drawn_as: pne\n") == [
            ("route_ink.drawn_as", 2, "'pne' is not one of 'pen', 'solid'")
        ]

    def test_a_list_missing_every_value_is_reported_once(self):
        """An empty list for a pair is one problem, though both positions are missing."""
        assert _found("card:\n  dark_grid: []\n") == [
            ("card.dark_grid", 2, "a list of 2 values, not 0")
        ]

    def test_an_error_with_no_message_of_its_own_reads_pydantic_s(self):
        """A `Literal` inside a list, refused, reads pydantic's own message."""
        found = _found("marks:\n  kinds: [dot, ring]\n", {"marks": _Marks})
        assert found == [("marks.kinds", 2, "Input should be 'dot' or 'dash'")]

    def test_a_dict_field_with_no_vocabulary_takes_any_key(self):
        """A dict field the vocabularies do not list takes any key, its values still checked."""
        table = _table("marks:\n  sizes:\n    anything: 2\n", {"marks": _Marks})
        assert table == {"marks": {"sizes": {"anything": 2.0}}}

    def test_an_unlisted_error_type_reads_pydantic_s_message(self):
        """A null inside a list reads as not a number, from the error type."""
        assert _found("brush:\n  blotch_m: [1.0, null]\n") == [
            ("brush.blotch_m", 2, "None is not a number")
        ]

    def test_a_colour_may_be_upper_case(self):
        """Upper-case hexadecimal digits are hexadecimal digits, so the colour is kept."""
        assert _table("route_ink:\n  colour: '#C22050'\n") == {"route_ink": {"colour": "#C22050"}}

    def test_an_int_in_a_float_field_is_a_float(self):
        """An integer given for a float field comes back as a plain `float`."""
        table = _table("wash:\n  wet_bleed_px: 20\n")
        wash = table["wash"]
        assert isinstance(wash, dict)
        value = wash["wet_bleed_px"]
        assert value == 20.0
        assert type(value) is float

    def test_a_dict_entry_is_converted(self):
        """A dict field's entries are converted to its value type, a tuple of floats."""
        table = _table("cover:\n  cover_cfg:\n    wood: [1, 0.3]\n")
        assert table == {"cover": {"cover_cfg": {"wood": (1.0, 0.3)}}}

    def test_valid_leaves_beside_an_error_are_kept(self):
        """The valid leaves of a file with an error come back converted; the invalid one is dropped."""
        table, problems = _check("wash:\n  blooms: no\n  wet_bleed_px: 20\n")
        assert len(problems) == 1
        assert table == {"wash": {"wet_bleed_px": 20.0}}

    def test_every_problem_is_reported_in_line_order(self):
        """Three problems in one file are all reported, in the order of their lines."""
        text = "route_ink:\n  colour: red\nwash:\n  blom: true\n  blooms: no\n"
        assert [line for _key, line, _message in _found(text)] == [2, 4, 5]

    def test_the_reader_s_problems_are_not_repeated(self):
        """A file whose read found a problem gives no problem of its own and no table."""
        problem = ThemeProblem(path=Path("t.yaml"), key="", line=1, message="duplicate key")
        theme = ThemeFile(path=Path("t.yaml"), table={}, lines={}, problems=(problem,))
        assert check_theme(theme, _groups()) == ({}, ())

    def test_a_problem_with_no_line_takes_its_ancestor_s(self):
        """A key path with no line of its own is placed at its nearest ancestor's line."""
        theme = ThemeFile(
            path=Path("t.yaml"), table={"wash": {"blooms": "no"}}, lines={("wash",): 3}, problems=()
        )
        _table, problems = check_theme(theme, _groups())
        assert [(p.key, p.line) for p in problems] == [("wash.blooms", 3)]

    def test_a_problem_with_no_line_anywhere_has_none(self):
        """A key path none of whose keys has a line gives a problem with no line."""
        theme = ThemeFile(path=Path("t.yaml"), table={"wash": 5}, lines={}, problems=())
        _table, problems = check_theme(theme, _groups())
        assert [(p.key, p.line) for p in problems] == [("wash", None)]

    def test_a_problem_with_no_line_comes_before_line_one(self):
        """A problem with no line sorts before one on line 1, whatever the table's order."""
        theme = ThemeFile(
            path=Path("t.yaml"),
            table={"wash": {"blooms": "no"}, "paper": 5},
            lines={("wash",): 1},
            problems=(),
        )
        _table, problems = check_theme(theme, _groups())
        assert [(p.key, p.line) for p in problems] == [("paper", None), ("wash.blooms", 1)]

    def test_a_problem_names_its_file(self):
        """Each problem carries the theme file's path."""
        _table, problems = check_theme(theme_file("wash: 5\n", "mine.yaml"), _groups())
        assert [p.path for p in problems] == [Path("mine.yaml")]


class TestASubTable:
    """A dataclass-typed field is a sub-table, checked by the same rules as a group."""

    GROUPS: dict[str, type] = {"route_ink": Ink}  # noqa: RUF012

    def test_a_sub_table_is_converted(self):
        """A sub-table's leaves are converted into a nested dict."""
        table = _table("route_ink:\n  glow:\n    px: 3\n", self.GROUPS)
        assert table == {"route_ink": {"glow": {"px": 3.0}}}

    def test_an_unknown_sub_table_suggests_the_nearest(self):
        """A misspelt sub-table name suggests the field it was nearest."""
        found = _found("route_ink:\n  glo:\n    px: 3\n", self.GROUPS)
        assert found == [("route_ink.glo", 2, "unknown key; did you mean glow?")]

    def test_a_sub_table_given_a_leaf_is_refused(self):
        """A sub-table set to a scalar is told it is a table of keys."""
        assert _found("route_ink:\n  glow: 5\n", self.GROUPS) == [
            ("route_ink.glow", 2, "is a table of keys")
        ]

    def test_an_unknown_key_in_a_sub_table(self):
        """An unknown key in a sub-table is named by its full path and line."""
        found = _found("route_ink:\n  glow:\n    pxx: 1\n", self.GROUPS)
        assert found == [("route_ink.glow.pxx", 3, "unknown key; did you mean px?")]

    def test_a_wrong_value_in_a_sub_table(self):
        """A sub-table's leaf is checked strictly."""
        found = _found("route_ink:\n  glow:\n    px: '3'\n", self.GROUPS)
        assert found == [("route_ink.glow.px", 3, "'3' is not a number")]


class TestBuildGroup:
    """`build_group` builds a group from a full, checked table, sub-tables included."""

    def test_a_sub_table_is_built_as_its_dataclass(self):
        """A nested dict for a dataclass-typed field is built as that dataclass."""
        table = {"glow": {"colour": "#ffffff", "px": 3.0}, "px": 5.4}
        assert build_group(Ink, table) == Ink(glow=Glow(px=3.0))

    def test_a_group_that_is_no_dataclass_is_refused(self):
        """Building a group from a class that is not a dataclass is a programming error."""
        with pytest.raises(TypeError, match="is not a dataclass"):
            build_group(int, {})

    @pytest.mark.parametrize("name", list(Style.model_fields), ids=list(Style.model_fields))
    def test_every_group_rebuilds_from_its_fields(self, name: str):
        """Each real group built from its own fields as a table equals its default."""
        group = _groups()[name]
        assert build_group(group, dataclasses.asdict(group())) == group()
