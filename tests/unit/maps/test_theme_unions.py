"""A theme's `casing_unions:`: the shape, every located error, the merge and the order at load."""

from pathlib import Path

import pytest

from pyntpot.maps import Style, ThemeError
from pyntpot.maps.cli import main
from pyntpot.maps.style import _groups
from pyntpot.maps.theme_check import check_theme_scoped
from pyntpot.maps.theme_scope import ThemeScope

from support.paths import FIXTURE_DIR
from support.theme_files import theme_file, write_theme

_RINGS = "line_effects:\n  major: {casing: {width_px: 2}}\n  minor: {casing: {width_px: 2}}\n"
_ROADS = (
    "line_effects:\n  road_major: {casing: {width_px: 2}}\n  lane: {casing: {width_px: 2}}\n"
    "  track: {casing: {width_px: 2}}\n"
)


def _check(text: str) -> tuple[dict[str, object], list[tuple[int | None, str, str]]]:
    """The table and the (line, key, message) problems of checking `text` as one file."""
    table, problems, _ = check_theme_scoped(theme_file(text), _groups(), ThemeScope.built_in())
    return table, [(p.line, p.key, p.message) for p in problems]


def _problems(root: Path, text: str) -> list[tuple[str, int | None, str, str]]:
    """The file name, line, key and message of every problem loading `text` raises."""
    with pytest.raises(ThemeError) as caught:
        Style.from_theme(write_theme(root, "t.yaml", text))
    return [(p.path.name, p.line, p.key, p.message) for p in caught.value.problems]


class TestTheShape:
    """The value is a list of lists of class names."""

    @pytest.mark.parametrize(
        ("text", "key"),
        [
            ("casing_unions: lane\n", "casing_unions"),
            ("casing_unions: {a: b}\n", "casing_unions"),
            ("casing_unions: [lane]\n", "casing_unions.0"),
            ("casing_unions: [[lane], [3]]\n", "casing_unions.1"),
        ],
        ids=["string", "table", "flat", "number"],
    )
    def test_a_value_that_is_no_list_of_lists_is_refused(self, text: str, key: str) -> None:
        """A bad shape is a problem at the union (or the key) on the key's line."""
        _, problems = _check(text)
        assert problems == [(1, key, "is a list of lists of line classes")]

    def test_a_valid_table_lands_in_the_basemap(self) -> None:
        """A checked file puts the unions under `basemap.casing_unions` as tuples."""
        table, problems = _check("casing_unions: [[major, minor]]\n")
        assert problems == []
        assert table == {"basemap": {"casing_unions": (("major", "minor"),)}}

    def test_an_empty_list_is_kept_to_clear_an_inherited_set(self) -> None:
        """`casing_unions: []` is an explicit empty tuple, so it replaces in the merge."""
        table, problems = _check("casing_unions: []\n")
        assert problems == []
        assert table == {"basemap": {"casing_unions": ()}}

    def test_a_union_of_one_is_allowed(self) -> None:
        """A single class is a union."""
        _, problems = _check("casing_unions: [[lane]]\n")
        assert problems == []

    def test_naming_it_under_basemap_is_refused(self) -> None:
        """`basemap.casing_unions` is a located error naming the top-level key."""
        _, problems = _check("basemap:\n  roads: all\n  casing_unions: []\n")
        assert problems == [(3, "basemap.casing_unions", "set only by the top-level casing_unions")]


class TestTheLocatedErrors:
    """Each membership problem names its file, key path and the line of the `casing_unions` key."""

    @pytest.mark.parametrize(
        ("value", "key", "message"),
        [
            ("[[lane], []]", "casing_unions.1", "names no class"),
            (
                "[[lnae]]",
                "casing_unions.0.0",
                "'lnae' is not a basemap line class; did you mean lane?",
            ),
            (
                "[[route]]",
                "casing_unions.0.0",
                "the route is cased at compose from its own mask and joins no union",
            ),
            ("[[lane], [track, lane]]", "casing_unions.1.1", "lane is already in casing_unions.0"),
            ("[[lane, lane]]", "casing_unions.0.1", "lane is already in casing_unions.0"),
            (
                "[[major, lane]]",
                "casing_unions.0",
                (
                    "mixes water (major) and road (lane); a union lies within one group, "
                    "so a road over a river still reads as a crossing"
                ),
            ),
        ],
        ids=["empty", "unknown", "route", "two-unions", "twice", "mixed"],
    )
    def test_a_membership_problem_is_located(self, value: str, key: str, message: str) -> None:
        """The problem sits on the line of the `casing_unions` key."""
        _, problems = _check(f"\ncasing_unions: {value}\n")
        assert problems == [(2, key, message)]

    def test_a_shape_error_keeps_the_written_index(self) -> None:
        """A malformed union is skipped, and a later problem keeps its written index."""
        _, problems = _check("casing_unions: [[3], [lnae]]\n")
        assert [key for _, key, _ in problems] == ["casing_unions.0", "casing_unions.1.0"]


class TestAfterTheMerge:
    """A union is checked against the final stacks, and located in the nearest file that writes it."""

    def test_a_member_with_no_ring_is_refused(self, tmp_path: Path) -> None:
        """A union member with no casing or reserve fails at the union's key."""
        text = _RINGS + "casing_unions: [[major, medium]]\n"
        assert _problems(tmp_path, text) == [
            (
                "t.yaml",
                4,
                "casing_unions.0",
                (
                    "medium has no casing or reserve; give it one in line_effects, "
                    "or drop it from the union"
                ),
            )
        ]

    def test_differing_colours_are_refused(self, tmp_path: Path) -> None:
        """Casing colours that differ fail, naming both."""
        text = (
            "line_effects:\n  road_major: {casing: {width_px: 2, colour: '#ffffff', strength: 0.9}}\n"
            "  lane: {casing: {width_px: 2, colour: '#fbf6e8'}}\n"
            "casing_unions: [[road_major, lane]]\n"
        )
        assert _problems(tmp_path, text) == [
            (
                "t.yaml",
                4,
                "casing_unions.0",
                (
                    "road_major's casing is #ffffff at 0.9 and lane's is #fbf6e8 at 1; "
                    "a union takes one colour and strength"
                ),
            )
        ]

    def test_a_casing_and_a_reserve_are_refused(self, tmp_path: Path) -> None:
        """A union of a casing and a reserve fails."""
        text = (
            "line_effects:\n  lane: {casing: {width_px: 2}}\n  track: {reserve: {width_px: 2}}\n"
            "casing_unions: [[lane, track]]\n"
        )
        assert _problems(tmp_path, text)[0][2:] == (
            "casing_unions.0",
            "a union is all casings or all reserves, with one pool",
        )

    def test_a_child_that_turns_a_member_off_fails_at_the_parents_unions(
        self, tmp_path: Path
    ) -> None:
        """A child's `track: {}` leaves the parent's union with a member without a ring."""
        write_theme(tmp_path, "parent.yaml", _ROADS + "casing_unions: [[lane, track]]\n")
        child = write_theme(
            tmp_path, "child.yaml", "extends: parent.yaml\nline_effects:\n  track: {}\n"
        )
        with pytest.raises(ThemeError) as caught:
            Style.from_theme(child)
        (problem,) = caught.value.problems
        assert (problem.path.name, problem.line, problem.key) == (
            "parent.yaml",
            5,
            "casing_unions.0",
        )
        assert problem.message.startswith("track has no casing or reserve")

    def test_the_nearest_writer_is_blamed(self, tmp_path: Path) -> None:
        """When the child rewrites the unions, its own file and key line are named."""
        write_theme(tmp_path, "parent.yaml", _ROADS + "casing_unions: [[lane]]\n")
        child = write_theme(
            tmp_path,
            "child.yaml",
            "extends: parent.yaml\nline_effects:\n  track: {}\ncasing_unions: [[lane], [track]]\n",
        )
        with pytest.raises(ThemeError) as caught:
            Style.from_theme(child)
        (problem,) = caught.value.problems
        assert (problem.path.name, problem.line, problem.key) == (
            "child.yaml",
            4,
            "casing_unions.1",
        )

    def test_the_written_index_is_reported_not_the_sorted_one(self, tmp_path: Path) -> None:
        """Unions sort by first member at load, but a problem names the union as written."""
        text = _ROADS.replace("  track: {casing: {width_px: 2}}\n", "") + (
            "casing_unions: [[lane, track], [road_major]]\n"
        )
        (problem,) = _problems(tmp_path, text)
        assert problem[2] == "casing_unions.0"


class TestTheMerge:
    """A child replaces, clears or keeps its parent's unions; the load normalises the order."""

    def test_a_child_replaces_the_whole_set(self, tmp_path: Path) -> None:
        """A child's `casing_unions` replaces its parent's, never joining it."""
        write_theme(tmp_path, "parent.yaml", _ROADS + "casing_unions: [[road_major, lane]]\n")
        child = write_theme(
            tmp_path, "child.yaml", "extends: parent.yaml\ncasing_unions: [[track]]\n"
        )
        assert Style.from_theme(child).basemap.casing_unions == (("track",),)

    def test_an_empty_list_clears_an_inherited_set(self, tmp_path: Path) -> None:
        """`casing_unions: []` turns the inherited unions off."""
        write_theme(tmp_path, "parent.yaml", _ROADS + "casing_unions: [[road_major, lane]]\n")
        child = write_theme(tmp_path, "child.yaml", "extends: parent.yaml\ncasing_unions: []\n")
        assert Style.from_theme(child).basemap.casing_unions == ()

    def test_a_child_that_writes_nothing_inherits_them(self, tmp_path: Path) -> None:
        """A child that does not name `casing_unions` keeps its parent's."""
        write_theme(tmp_path, "parent.yaml", _ROADS + "casing_unions: [[road_major, lane]]\n")
        child = write_theme(tmp_path, "child.yaml", "extends: parent.yaml\n")
        assert Style.from_theme(child).basemap.casing_unions == (("road_major", "lane"),)

    def test_members_and_unions_are_put_in_class_order(self, tmp_path: Path) -> None:
        """Members sort by the group's class order and unions by their first member."""
        text = (
            _ROADS
            + _RINGS.split("\n", 1)[1]
            + "casing_unions: [[track, lane], [minor, major], [road_major]]\n"
        )
        style = Style.from_theme(write_theme(tmp_path, "t.yaml", text))
        assert style.basemap.casing_unions == (
            ("major", "minor"),
            ("road_major",),
            ("lane", "track"),
        )

    def test_two_orders_of_one_picture_share_every_digest(self, tmp_path: Path) -> None:
        """Themes that differ only in the written order have equal styles and digests."""
        one = Style.from_theme(
            write_theme(tmp_path, "a.yaml", _ROADS + "casing_unions: [[lane, track]]\n")
        )
        two = Style.from_theme(
            write_theme(tmp_path, "b.yaml", _ROADS + "casing_unions: [[track, lane]]\n")
        )
        assert one == two
        assert (one.digest(), one.base_digest()) == (two.digest(), two.base_digest())


class TestTheCommandLine:
    """`pyntpot map --style` exits 2 on a bad union before any request."""

    @pytest.mark.parametrize(
        ("text", "shown"),
        [
            ("casing_unions: [[route]]\n", "joins no union"),
            ("casing_unions: [[lnae]]\n", "did you mean lane?"),
            (_ROADS + "casing_unions: [[lane, major]]\n", "mixes water (major) and road (lane)"),
            ("casing_unions: [[lane]]\n", "lane has no casing or reserve"),
        ],
        ids=["route", "unknown", "mixed", "no-ring"],
    )
    def test_a_bad_union_exits_2_and_fetches_nothing(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture, text: str, shown: str
    ) -> None:
        """The theme is refused with its message, no cache is made and nothing is written."""
        style = write_theme(tmp_path, "bad.yaml", text)
        cache = tmp_path / "cache"
        argv = ["map", str(FIXTURE_DIR / "track.gpx"), "--cache", str(cache), "--contact", "t"]
        argv += ["--style", str(style), "--no-attribution", "-o", str(tmp_path / "out.png")]
        assert main(argv) == 2
        assert shown in caplog.text
        assert not cache.exists()
