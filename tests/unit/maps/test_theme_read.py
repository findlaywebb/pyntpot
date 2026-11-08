"""Reading a theme file: the YAML features a theme may not use, syntax errors, and plain data out."""

from pathlib import Path

import pytest

from pyntpot.maps.theme_read import ThemeFile, read_theme

PATH = Path("t.yaml")


def _read(text: str) -> ThemeFile:
    """Read `text` as the theme file `t.yaml`."""
    return read_theme(PATH, text)


def _found(text: str) -> list[tuple[str, int | None, str]]:
    """Each problem reading `text` finds, as its key, line and message."""
    theme = _read(text)
    assert all(problem.path == PATH for problem in theme.problems)
    return [(problem.key, problem.line, problem.message) for problem in theme.problems]


ANCHOR = "anchors are not allowed; use extends"
ALIAS = "aliases are not allowed; use extends"
TAG = "tags are not allowed"
DIRECTIVE = "directives are not allowed: a theme is YAML 1.2"


class TestTheWalkRejectsYamlFeatures:
    """The event walk reports every YAML feature a theme may not use, at its line and key."""

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("a: &x 1\n", [("a", 1, ANCHOR)]),
            ("a: &x {b: 1}\n", [("a", 1, ANCHOR)]),
            ("a: &x [1]\n", [("a", 1, ANCHOR)]),
            ("&x a: 1\n", [("a", 1, ANCHOR)]),
            ("a: 1\nb: *x\n", [("b", 2, ALIAS)]),
            ("a: &x 1\nb: *x\n", [("a", 1, ANCHOR), ("b", 2, ALIAS)]),
        ],
        ids=["anchor-scalar", "anchor-mapping", "anchor-sequence", "anchor-key", "alias", "both"],
    )
    def test_anchors_and_aliases(self, text: str, expected: list[tuple[str, int, str]]) -> None:
        """An anchor and an alias are one problem each, never two for one alias."""
        assert _found(text) == expected

    def test_merge_key(self) -> None:
        """A `<<` merge key is refused in favour of `extends`."""
        assert _found("wash:\n  <<: {blooms: true}\n") == [
            ("wash.<<", 2, "merge keys are not allowed; use extends")
        ]

    @pytest.mark.parametrize(
        "text",
        ["a: !!str 5\n", "a: !foo 5\n", "a: !foo {b: 1}\n", "a: !foo [1]\n"],
        ids=["core-tag", "local-tag", "mapping-tag", "sequence-tag"],
    )
    def test_tags(self, text: str) -> None:
        """Any explicit tag, on a scalar, mapping or sequence, is refused."""
        assert _found(text) == [("a", 1, TAG)]

    @pytest.mark.parametrize(
        "text",
        ["%YAML 1.1\n---\na: no\n", "%TAG !x! tag:example.com,2000:\n---\na: 1\n"],
        ids=["yaml-version", "tag-directive"],
    )
    def test_directives(self, text: str) -> None:
        """A `%YAML` or `%TAG` directive is refused, so a theme is always read as YAML 1.2."""
        assert _found(text) == [("", 2, DIRECTIVE)]

    def test_second_document(self) -> None:
        """A second document in one file is refused at its `---` line."""
        assert _found("a: 1\n---\nb: 2\n") == [("", 2, "one document per theme file")]

    def test_complex_key(self) -> None:
        """A key that is a sequence is refused: keys are strings."""
        assert _found("wash:\n  ? [a, b]\n  : 1\n") == [("wash", 2, "keys are strings")]

    def test_duplicates_at_every_depth(self) -> None:
        """Every duplicate key is reported at its own line, with its key path, at any depth."""
        text = "wash:\n  blooms: true\n  blooms: false\ncard:\n  display_px: 1\n  display_px: 2\n"
        assert _found(text) == [
            ("wash.blooms", 3, "duplicate key"),
            ("card.display_px", 6, "duplicate key"),
        ]

    def test_every_repeat_of_a_key(self) -> None:
        """A key given three times is two duplicates, not one."""
        assert _found("a: 1\na: 2\na: 3\n") == [
            ("a", 2, "duplicate key"),
            ("a", 3, "duplicate key"),
        ]

    def test_same_key_in_sibling_mappings_is_no_duplicate(self) -> None:
        """A key repeated in two different mappings, or in mappings inside a sequence, is fine."""
        assert _found("a:\n  x: 1\nb:\n  x: 2\nc: [{x: 1}, {x: 2}]\n") == []

    def test_walk_problems_load_nothing(self) -> None:
        """A file with a walk problem reads as an empty table with no lines."""
        theme = _read("wash:\n  blooms: true\n  blooms: false\n")
        assert theme.table == {}
        assert theme.lines == {}


class TestSyntaxErrorsEndTheWalk:
    """A syntax error ends the walk with one located problem, after the problems found before it."""

    def test_unclosed_flow_sequence(self) -> None:
        """An unclosed `[` is one parser problem, with a line and the key being read."""
        theme = _read("wash:\n  blooms: [1, 2\n")
        assert [(p.key, p.line) for p in theme.problems] == [("wash.blooms", 3)]
        assert "expected ',' or ']'" in theme.problems[0].message
        assert theme.table == {}

    def test_tab_indent(self) -> None:
        """A tab where indentation belongs is one scanner problem at its line."""
        theme = _read("wash:\n\tblooms: true\n")
        assert [(p.key, p.line) for p in theme.problems] == [("wash", 2)]
        assert "'\\t'" in theme.problems[0].message

    def test_alias_before_a_syntax_error(self) -> None:
        """Problems the walk found before the syntax error are kept, in line order."""
        found = _found("a: 1\nb: *x\nc: [1\n")
        assert found[0] == ("b", 2, ALIAS)
        assert [(key, line) for key, line, _ in found[1:]] == [("c", 4)]


class TestTheContentIsPlainData:
    """A clean file reads as plain dicts, tuples and scalars, with the line of every key."""

    @pytest.mark.parametrize("text", ["", "# only a comment\n"], ids=["empty", "comment"])
    def test_empty_file_is_an_empty_table(self, text: str) -> None:
        """A file with no content is an empty table and no problem."""
        theme = _read(text)
        assert (theme.table, theme.lines, theme.problems) == ({}, {}, ())

    @pytest.mark.parametrize("text", ["- wash\n", "5\n"], ids=["sequence", "scalar"])
    def test_top_level_must_be_a_mapping(self, text: str) -> None:
        """A top level that is not a mapping is one problem on line 1."""
        assert _found(text) == [("", 1, "a theme is a mapping of style groups")]
        assert _read(text).table == {}

    def test_types(self) -> None:
        """Mappings become dicts, sequences tuples, and scalars their plain built-in types."""
        theme = _read('a:\n  n: 5\n  x: 0.5\n  b: true\n  s: "q"\n  t: [1, 2.5]\n  h: 0x10\n')
        assert theme.table == {"a": {"n": 5, "x": 0.5, "b": True, "s": "q", "t": (1, 2.5), "h": 16}}
        inner = theme.table["a"]
        assert isinstance(inner, dict)
        assert [type(value) for value in inner.values()] == [int, float, bool, str, tuple, int]
        assert [type(value) for value in inner["t"]] == [int, float]
        assert theme.problems == ()

    def test_no_is_a_string(self) -> None:
        """`no` reads as the string `"no"` under YAML 1.2, so the checker can refuse it."""
        assert _read("wash:\n  blooms: no\n").table == {"wash": {"blooms": "no"}}

    def test_nested_line(self) -> None:
        """A key three levels deep records its own line, as do its parents."""
        theme = _read("cover:\n  pigments:\n\n    wood: '#556b2f'\n")
        assert theme.lines == {
            ("cover",): 1,
            ("cover", "pigments"): 2,
            ("cover", "pigments", "wood"): 4,
        }

    def test_flow_mapping_line(self) -> None:
        """The keys of a flow mapping get the flow's line."""
        theme = _read("brush:\n  overrides:\n    stroke: {jitter_px: 0.4}\n")
        assert theme.lines[("brush", "overrides", "stroke", "jitter_px")] == 3

    def test_non_string_key(self) -> None:
        """A key that loads as a number is refused and left out of the table."""
        theme = _read("a: 1\n5: x\n")
        assert _found("a: 1\n5: x\n") == [("5", 2, "keys are strings")]
        assert theme.table == {"a": 1}

    @pytest.mark.parametrize(
        "text", ["wash:\n  blooms:\n", "wash:\n  blooms: ~\n"], ids=["bare", "tilde"]
    )
    def test_no_value(self, text: str) -> None:
        """A key with no value is one problem at its line, and is dropped from the table."""
        assert _found(text) == [("wash.blooms", 2, "has no value")]
        assert _read(text).table == {"wash": {}}

    def test_conversion_problems_in_line_order(self) -> None:
        """Problems the conversion finds come back in line order."""
        found = _found("b:\n  x:\n5: 1\na:\n")
        assert [line for _, line, _ in found] == [2, 3, 4]


DATE = "a theme value is never a date; quote it if a string was meant"


class TestTheWalkReadsEveryScalar:
    """Each plain scalar reads as a string, number, bool or null, or is a problem at its line."""

    def test_impossible_date(self) -> None:
        """`2001-02-30` is a problem at its line, not a raised `ValueError`."""
        assert _found("wash:\n  a: 2001-02-30\n") == [("wash.a", 2, DATE)]

    def test_unreadable_number(self) -> None:
        """`0b_` is a problem at its line, not a raised `IndexError`."""
        assert _found("wash:\n  a: 0b_\n") == [("wash.a", 2, "cannot read `0b_` as a number")]

    def test_valid_date(self) -> None:
        """A valid date such as `2024-01-01` is refused: a theme value is never a date."""
        theme = _read("a: 2024-01-01\n")
        assert [(p.key, p.line, p.message) for p in theme.problems] == [("a", 1, DATE)]
        assert theme.table == {}

    def test_quoted_date_is_a_string(self) -> None:
        """A quoted date is the string it spells."""
        assert _read("a: '2024-01-01'\n").table == {"a": "2024-01-01"}

    def test_other_tags_are_refused(self) -> None:
        """A plain `=` or a `<<` value resolves outside the theme's types and is refused."""
        assert [(key, line) for key, line, _ in _found("a: =\nb: <<\n")] == [("a", 1), ("b", 2)]

    def test_ordinary_scalars_read(self) -> None:
        """An ordinary int, float and bool still read as themselves, with no problem."""
        theme = _read("a: 5\nb: 0.5\nc: true\nd: 1_000\n")
        assert theme.table == {"a": 5, "b": 0.5, "c": True, "d": 1000}
        assert theme.problems == ()

    def test_null_in_a_sequence_stays(self) -> None:
        """A null inside a sequence reads as `None`, for the checker to refuse."""
        assert _read("a: [1, ~]\n").table == {"a": (1, None)}

    def test_bad_scalars_reported_together(self) -> None:
        """Several bad scalars are each reported, at their own line and key."""
        assert _found("a: 0b_\nb:\n  c: 2001-02-30\n  d: 0x_\n2024-01-01: 1\n") == [
            ("a", 1, "cannot read `0b_` as a number"),
            ("b.c", 3, DATE),
            ("b.d", 4, "cannot read `0x_` as a number"),
            ("2024-01-01", 5, DATE),
        ]
