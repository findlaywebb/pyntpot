"""The casing union model: its membership rules, its stack rules, and `BasemapStyle` refusing both."""

import pytest

from pyntpot.ink import Casing, Glow, Reserve
from pyntpot.ink.colour import Colour
from pyntpot.maps import EffectStack
from pyntpot.maps.casing_unions import membership_problems, union_problems
from pyntpot.maps.style_groups import BasemapStyle

_WHITE = EffectStack(effects=(Casing(width_px=2.0),))
_PAPER = EffectStack(effects=(Reserve(width_px=2.0, pool=0.2),))


class TestMembership:
    """What is wrong with a union before any stack is read."""

    def test_good_unions_have_no_problem(self) -> None:
        """Water and road unions, and a union of one, are fine."""
        assert membership_problems([("major", "medium"), ("road_major", "lane"), ("track",)]) == ()

    def test_an_empty_union_names_no_class(self) -> None:
        """An empty union is a problem at its index with no member."""
        assert membership_problems([("major",), ()]) == ((1, None, "names no class"),)

    def test_an_unknown_class_names_the_nearest(self) -> None:
        """A misspelt class is refused with the nearest basemap class."""
        assert membership_problems([("lnae",)]) == (
            (0, 0, "'lnae' is not a basemap line class; did you mean lane?"),
        )

    def test_the_route_joins_no_union(self) -> None:
        """The route is refused with the reason."""
        assert membership_problems([("route",)]) == (
            (0, 0, "the route is cased at compose from its own mask and joins no union"),
        )

    def test_a_class_in_two_unions_is_refused_at_the_later(self) -> None:
        """A class already in an earlier union is refused at its later place."""
        assert membership_problems([("lane",), ("track", "lane")]) == (
            (1, 1, "lane is already in casing_unions.0"),
        )

    def test_a_class_twice_in_one_union_is_refused(self) -> None:
        """A class repeated inside one union names that union as the earlier place."""
        assert membership_problems([("lane", "lane")]) == (
            (0, 1, "lane is already in casing_unions.0"),
        )

    def test_water_and_road_do_not_mix(self) -> None:
        """A union across water and road names one of each."""
        assert membership_problems([("major", "lane")]) == (
            (
                0,
                None,
                (
                    "mixes water (major) and road (lane); a union lies within one group, "
                    "so a road over a river still reads as a crossing"
                ),
            ),
        )


class TestAgainstTheStacks:
    """What is wrong with a union given the basemap's stacks."""

    def test_matching_casings_are_fine(self) -> None:
        """Two members with equal casings, and two with equal reserves, raise nothing."""
        assert union_problems({"major": _WHITE, "minor": _WHITE}, [("major", "minor")]) == ()
        assert union_problems({"lane": _PAPER, "track": _PAPER}, [("lane", "track")]) == ()

    def test_a_glow_beside_the_ring_is_not_compared(self) -> None:
        """Members may differ in their glows: only the ring is shared."""
        glowing = EffectStack(effects=(Casing(width_px=2.0), Glow(spread_px=1.0, strength=0.5)))
        assert union_problems({"lane": _WHITE, "track": glowing}, [("lane", "track")]) == ()

    def test_a_member_with_no_ring_is_named(self) -> None:
        """A member with no stack, or only a glow, has no casing or reserve."""
        message = (
            "track has no casing or reserve; give it one in line_effects, or drop it from the union"
        )
        assert union_problems({"lane": _WHITE}, [("lane", "track")]) == ((0, 1, message),)

    def test_casings_that_differ_in_colour_are_refused(self) -> None:
        """Two casing colours name both members and their colour and strength."""
        dark = EffectStack(effects=(Casing(width_px=2.0, colour=Colour("#fbf6e8"), strength=0.9),))
        found = union_problems({"road_major": dark, "lane": _WHITE}, [("road_major", "lane")])
        assert found == (
            (
                0,
                None,
                (
                    "road_major's casing is #fbf6e8 at 0.9 and lane's is #ffffff at 1; "
                    "a union takes one colour and strength"
                ),
            ),
        )

    def test_casings_that_differ_in_strength_alone_are_refused(self) -> None:
        """Equal colours with unequal strengths are refused too."""
        faint = EffectStack(effects=(Casing(width_px=2.0, strength=0.5),))
        found = union_problems({"lane": faint, "track": _WHITE}, [("lane", "track")])
        assert len(found) == 1
        assert "a union takes one colour and strength" in found[0][2]

    def test_widths_may_differ(self) -> None:
        """Members may ring at their own widths."""
        wide = EffectStack(effects=(Casing(width_px=5.0),))
        assert union_problems({"lane": _WHITE, "track": wide}, [("lane", "track")]) == ()

    def test_a_casing_and_a_reserve_are_refused(self) -> None:
        """A union of a casing and a reserve is all-or-nothing."""
        found = union_problems({"lane": _WHITE, "track": _PAPER}, [("lane", "track")])
        assert found == ((0, None, "a union is all casings or all reserves, with one pool"),)

    def test_reserves_with_different_pools_are_refused(self) -> None:
        """Two reserves with different pools are refused."""
        other = EffectStack(effects=(Reserve(width_px=2.0, pool=0.4),))
        found = union_problems({"lane": _PAPER, "track": other}, [("lane", "track")])
        assert found == ((0, None, "a union is all casings or all reserves, with one pool"),)

    def test_membership_comes_first(self) -> None:
        """The membership problems precede the stack problems."""
        found = union_problems({}, [("lnae",), ("lane",)])
        assert [message[:6] for _, _, message in found] == ["'lnae'", "lane h"]


class TestBasemapStyle:
    """`BasemapStyle` refuses in Python what the loader refuses in a file."""

    def test_good_unions_are_held_in_the_order_given(self) -> None:
        """A valid set is held as given; the style normalises nothing."""
        style = BasemapStyle(
            line_effects={"lane": _WHITE, "road_major": _WHITE},
            casing_unions=(("lane", "road_major"),),
        )
        assert style.casing_unions == (("lane", "road_major"),)

    @pytest.mark.parametrize(
        ("unions", "match"),
        [
            ((("route",),), "joins no union"),
            ((("lnae",),), "did you mean lane"),
            ((("lane",), ("lane",)), "already in casing_unions.0"),
            ((("major", "lane"),), "mixes water"),
            (((),), "names no class"),
            ((("track",),), "track has no casing or reserve"),
        ],
        ids=["route", "unknown", "duplicate", "mixed", "empty", "no-ring"],
    )
    def test_a_bad_union_is_refused(self, unions: tuple[tuple[str, ...], ...], match: str) -> None:
        """Each problem raises `ValueError` naming it, prefixed with the field."""
        with pytest.raises(ValueError, match=f"casing_unions: .*{match}"):
            BasemapStyle(line_effects={"lane": _WHITE}, casing_unions=unions)

    def test_a_stack_with_the_ring_off_leaves_a_member_without_one(self) -> None:
        """A member whose stack is empty is refused, since `line_effects` drops it."""
        with pytest.raises(ValueError, match="lane has no casing or reserve"):
            BasemapStyle(line_effects={"lane": EffectStack()}, casing_unions=(("lane",),))
