"""Reading a theme file: the YAML features a theme may not use, syntax errors, and plain data out."""

from pathlib import Path

import pytest

from pyntpot.maps.theme_walk import MAX_DEPTH

from support.theme_files import theme_file

PATH = Path("t.yaml")


def _found(text: str) -> list[tuple[str, int | None, str]]:
    """Each problem reading `text` finds, as its key, line and message."""
    theme = theme_file(text)
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

    def test_a_non_specific_tag_is_refused_alone(self) -> None:
        """A `!` tag on a date is the tag problem alone: its value is not read as a date."""
        assert _found("a: ! 2024-01-01\n") == [("a", 1, TAG)]

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
        theme = theme_file("wash:\n  blooms: true\n  blooms: false\n")
        assert theme.table == {}
        assert theme.lines == {}


class TestSyntaxErrorsEndTheWalk:
    """A syntax error ends the walk with one located problem, after the problems found before it."""

    def test_unclosed_flow_sequence(self) -> None:
        """An unclosed `[` is one parser problem, with a line and the key being read."""
        theme = theme_file("wash:\n  blooms: [1, 2\n")
        assert [(p.key, p.line) for p in theme.problems] == [("wash.blooms", 3)]
        assert "expected ',' or ']'" in theme.problems[0].message
        assert theme.table == {}

    def test_tab_indent(self) -> None:
        """A tab where indentation belongs is one scanner problem at its line."""
        theme = theme_file("wash:\n\tblooms: true\n")
        assert [(p.key, p.line) for p in theme.problems] == [("wash", 2)]
        assert "'\\t'" in theme.problems[0].message

    def test_the_message_is_the_problem_alone(self) -> None:
        """A syntax error's message is the parser's problem, without its own location text."""
        theme = theme_file("wash:\n  blooms: [1, 2\n")
        assert theme.problems[0].message == "expected ',' or ']', but got '<stream end>'"

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
        theme = theme_file(text)
        assert (theme.table, theme.lines, theme.problems) == ({}, {}, ())

    def test_an_empty_file_keeps_its_path(self) -> None:
        """A file with no content is still read as the path the caller named."""
        assert theme_file("").path == PATH

    @pytest.mark.parametrize("text", ["- wash\n", "5\n"], ids=["sequence", "scalar"])
    def test_top_level_must_be_a_mapping(self, text: str) -> None:
        """A top level that is not a mapping is one problem on line 1."""
        assert _found(text) == [("", 1, "a theme is a mapping of style groups")]
        assert theme_file(text).table == {}

    def test_a_top_level_that_is_not_a_mapping_records_no_lines(self) -> None:
        """A top level that is not a mapping records no key lines: an empty mapping."""
        assert theme_file("- wash\n").lines == {}

    def test_types(self) -> None:
        """Mappings become dicts, sequences tuples, and scalars their plain built-in types."""
        theme = theme_file('a:\n  n: 5\n  x: 0.5\n  b: true\n  s: "q"\n  t: [1, 2.5]\n  h: 0x10\n')
        assert theme.table == {"a": {"n": 5, "x": 0.5, "b": True, "s": "q", "t": (1, 2.5), "h": 16}}
        inner = theme.table["a"]
        assert isinstance(inner, dict)
        assert [type(value) for value in inner.values()] == [int, float, bool, str, tuple, int]
        assert [type(value) for value in inner["t"]] == [int, float]
        assert theme.problems == ()

    def test_no_is_a_string(self) -> None:
        """`no` reads as the string `"no"` under YAML 1.2, so the checker can refuse it."""
        assert theme_file("wash:\n  blooms: no\n").table == {"wash": {"blooms": "no"}}

    def test_nested_line(self) -> None:
        """A key three levels deep records its own line, as do its parents."""
        theme = theme_file("cover:\n  pigments:\n\n    wood: '#556b2f'\n")
        assert theme.lines == {
            ("cover",): 1,
            ("cover", "pigments"): 2,
            ("cover", "pigments", "wood"): 4,
        }

    def test_flow_mapping_line(self) -> None:
        """The keys of a flow mapping get the flow's line."""
        theme = theme_file("brush:\n  overrides:\n    stroke: {jitter_px: 0.4}\n")
        assert theme.lines[("brush", "overrides", "stroke", "jitter_px")] == 3

    def test_non_string_key(self) -> None:
        """A key that would load as a number is refused in the walk, so nothing loads."""
        assert _found("a: 1\n5: x\n") == [("5", 2, "keys are strings")]
        assert theme_file("a: 1\n5: x\n").table == {}

    def test_a_key_after_one_with_no_value_is_read(self) -> None:
        """A key after one with no value is still read, with its line."""
        theme = theme_file("a:\nb: 2\n")
        assert theme.table == {"b": 2}
        assert theme.lines == {("a",): 1, ("b",): 2}

    def test_no_value_in_a_mapping_inside_a_sequence(self) -> None:
        """A key with no value in a mapping inside a sequence is reported at its key."""
        assert _found("a: [{b: }]\n") == [("a.b", 1, "has no value")]
        assert theme_file("a: [{b: }]\n").table == {"a": ({},)}

    @pytest.mark.parametrize(
        "text", ["wash:\n  blooms:\n", "wash:\n  blooms: ~\n"], ids=["bare", "tilde"]
    )
    def test_no_value(self, text: str) -> None:
        """A key with no value is one problem at its line, and is dropped from the table."""
        assert _found(text) == [("wash.blooms", 2, "has no value")]
        assert theme_file(text).table == {"wash": {}}

    def test_conversion_problems_in_line_order(self) -> None:
        """Problems the conversion finds come back in line order."""
        found = _found("b:\n  x:\nc: [{d: }]\na:\n")
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

    def test_unreadable_float(self) -> None:
        """`._` resolves as a float that cannot be read: a problem at its line, not a raise."""
        assert _found("a: ._\n") == [("a", 1, "cannot read `._` as a number")]

    def test_a_date_in_a_sequence_is_at_the_sequence_key(self) -> None:
        """A date inside a sequence is reported at the key holding the sequence."""
        assert _found("a:\n  b: [1, 2024-01-01]\n") == [("a.b", 2, DATE)]

    def test_a_value_after_a_complex_key_is_at_the_mapping(self) -> None:
        """A bad value after a key that is not a scalar is reported at the enclosing mapping."""
        assert _found("a:\n  ? [x, y]\n  : 2024-01-01\n") == [
            ("a", 2, "keys are strings"),
            ("a", 3, DATE),
        ]

    def test_valid_date(self) -> None:
        """A valid date such as `2024-01-01` is refused: a theme value is never a date."""
        theme = theme_file("a: 2024-01-01\n")
        assert [(p.key, p.line, p.message) for p in theme.problems] == [("a", 1, DATE)]
        assert theme.table == {}

    def test_quoted_date_is_a_string(self) -> None:
        """A quoted date is the string it spells."""
        assert theme_file("a: '2024-01-01'\n").table == {"a": "2024-01-01"}

    def test_other_tags_are_refused(self) -> None:
        """A plain `=` or a `<<` value resolves outside the theme's types and is refused."""
        assert [(key, line) for key, line, _ in _found("a: =\nb: <<\n")] == [("a", 1), ("b", 2)]

    def test_ordinary_scalars_read(self) -> None:
        """An ordinary int, float and bool still read as themselves, with no problem."""
        theme = theme_file("a: 5\nb: 0.5\nc: true\nd: 1_000\n")
        assert theme.table == {"a": 5, "b": 0.5, "c": True, "d": 1000}
        assert theme.problems == ()

    def test_null_in_a_sequence_stays(self) -> None:
        """A null inside a sequence reads as `None`, for the checker to refuse."""
        assert theme_file("a: [1, ~]\n").table == {"a": (1, None)}

    def test_bad_scalars_reported_together(self) -> None:
        """Several bad scalars are each reported, at their own line and key."""
        assert _found("a: 0b_\nb:\n  c: 2001-02-30\n  d: 0x_\n2024-01-01: 1\n") == [
            ("a", 1, "cannot read `0b_` as a number"),
            ("b.c", 3, DATE),
            ("b.d", 4, "cannot read `0x_` as a number"),
            ("2024-01-01", 5, "keys are strings"),
        ]


SPECIAL = "special characters are not allowed"


class TestEveryCharacterIsReported:
    """A character no YAML file may hold is a problem for the file, at its line, never a raise."""

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("wash:\n  blooms: tr\x00ue\n", ("", 2, f"unacceptable character #x0000: {SPECIAL}")),
            ("a: 1\nb: \x9f\n", ("", 2, f"unacceptable character #x009f: {SPECIAL}")),
            ("\x01", ("", 1, f"unacceptable character #x0001: {SPECIAL}")),
            ("a: 1\r\nb: 2\r\nc: \x08\n", ("", 3, f"unacceptable character #x0008: {SPECIAL}")),
        ],
        ids=["nul", "c1-control", "first-character", "crlf-lines"],
    )
    def test_a_control_character(self, text: str, expected: tuple[str, int, str]) -> None:
        """A NUL or a C0 or C1 control character is one problem at its own line."""
        assert _found(text) == [expected]
        assert theme_file(text).table == {}

    def test_far_into_a_long_file(self) -> None:
        """A control character past the reader's first chunk is still at its own line."""
        text = "a: 1\n" * 3000 + "b: \x9f\n"
        assert [line for _, line, _ in _found(text)][-1] == 3001


class TestKeysAreStrings:
    """A plain key that resolves to anything but a string is refused in the walk, so none loads."""

    @pytest.mark.parametrize(
        ("text", "keys"),
        [
            ("null: 1\n~: 2\n", ["null", "~"]),
            ("true: 1\nTrue: 2\n", ["true", "True"]),
            ("card:\n  1: a\n  0x1: b\n", ["card.1", "card.0x1"]),
            ("1.5: a\n.inf: b\n", ["1.5", ".inf"]),
        ],
        ids=["null", "bool", "int", "float"],
    )
    def test_keys_equal_once_resolved(self, text: str, keys: list[str]) -> None:
        """Keys spelled apart that resolve alike are each refused as keys, never a raised duplicate."""
        assert [(key, message) for key, _, message in _found(text)] == [
            (key, "keys are strings") for key in keys
        ]

    def test_an_empty_key(self) -> None:
        """An empty plain key resolves to null and is refused as a key."""
        assert _found("? \n: 1\n") == [("", 1, "keys are strings")]

    def test_a_date_key(self) -> None:
        """A key that resolves to a date is refused as a key, not as a value."""
        assert _found("2024-01-01: 1\n") == [("2024-01-01", 1, "keys are strings")]

    @pytest.mark.parametrize(
        "text",
        ["'5': a\n\"5\": b\n", 'a: 1\n"a": 2\n', 'a: 1\n"\\x61": 2\n'],
        ids=["quoted", "plain-and-quoted", "escaped"],
    )
    def test_string_keys_with_one_text_collide(self, text: str) -> None:
        """Two string keys with the same text are a duplicate, however each is quoted."""
        assert [(line, message) for _, line, message in _found(text)] == [(2, "duplicate key")]

    def test_a_quoted_null_and_a_plain_null_do_not_collide(self) -> None:
        """A quoted `null` is a string key; the plain `null` after it is refused as no string."""
        assert _found("'null': 1\nnull: 2\n") == [("null", 2, "keys are strings")]
        assert _found("null: 1\n'null': 2\n") == [("null", 1, "keys are strings")]

    def test_quoted_keys_that_look_alike_are_strings(self) -> None:
        """Quoted `null`, `~` and `true` are three string keys, and none of them a duplicate."""
        theme = theme_file("'null': 1\n'~': 2\n'true': 3\n")
        assert theme.table == {"null": 1, "~": 2, "true": 3}
        assert theme.problems == ()


class TestNestingIsBounded:
    """A mapping or sequence nested past `MAX_DEPTH` is one problem, never a `RecursionError`."""

    @pytest.mark.parametrize(
        "text",
        ["a: " + "[" * 2000 + "]" * 2000 + "\n", "a: " + "{b: " * 600 + "1" + "}" * 600 + "\n"],
        ids=["sequences", "mappings"],
    )
    def test_deep_flow_nesting(self, text: str) -> None:
        """Thousands of nested flow collections are one problem at the first too deep."""
        assert [message for _, _, message in _found(text)] == [f"nested more than {MAX_DEPTH} deep"]

    def test_the_cap_itself_reads(self) -> None:
        """`MAX_DEPTH` open collections read; one more is the problem."""
        inside = "a: " + "[" * (MAX_DEPTH - 1) + "]" * (MAX_DEPTH - 1) + "\n"
        assert _found(inside) == []
        past = "a: " + "[" * MAX_DEPTH + "]" * MAX_DEPTH + "\n"
        assert _found(past) == [("a", 1, f"nested more than {MAX_DEPTH} deep")]
