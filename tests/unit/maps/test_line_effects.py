"""The effect stack, the line classes and the presets: one of a kind, no off effect, seven classes."""

import dataclasses

import pytest

from pyntpot.ink import Casing, Glow, Reserve, Shadow
from pyntpot.ink.brush_style import BrushStyle
from pyntpot.maps import EffectStack
from pyntpot.maps.line_effects import (
    BUILT_IN_PRESETS,
    LINE_CLASSES,
    ROAD_GROUP,
    WATER_GROUP,
    checked_line_effects,
    ring_effect,
)
from pyntpot.maps.style_groups import BasemapStyle


class TestTheStack:
    """What a stack keeps and refuses."""

    @pytest.mark.parametrize(
        "pair",
        [
            (Casing(width_px=1.0), Casing(width_px=2.0)),
            (Glow(spread_px=1.0, strength=0.5), Glow(spread_px=2.0, strength=0.5)),
            (Shadow(offset_px=1.0, strength=0.5), Shadow(offset_px=2.0, strength=0.5)),
        ],
        ids=["casing", "glow", "shadow"],
    )
    def test_two_of_a_kind_are_refused(self, pair: tuple[Casing | Glow | Shadow, ...]) -> None:
        """A stack with two effects of one kind raises `ValueError` naming the kind."""
        with pytest.raises(ValueError, match="at most one"):
            EffectStack(effects=pair)

    def test_one_of_each_kind_keeps_its_order(self) -> None:
        """A casing, a glow and a shadow are kept in the order given."""
        effects = (
            Shadow(offset_px=1.0, strength=0.4),
            Casing(width_px=1.0),
            Glow(spread_px=1.0, strength=0.5),
        )
        assert EffectStack(effects=effects).effects == effects

    @pytest.mark.parametrize(
        "off",
        [
            Casing(width_px=0.0),
            Casing(width_px=-0.0),
            Casing(width_px=2.0, strength=0.0),
            Glow(spread_px=2.0, blur_px=2.0, strength=0.0),
            Shadow(offset_px=2.0, blur_px=2.0, strength=0.0),
        ],
        ids=["casing-0", "casing-minus-0", "casing-no-strength", "glow", "shadow"],
    )
    def test_an_off_effect_is_dropped(self, off: Casing | Glow | Shadow) -> None:
        """A stack of one off effect equals the empty stack."""
        assert EffectStack(effects=(off,)) == EffectStack()

    def test_the_off_effects_go_and_the_rest_stay(self) -> None:
        """An off effect among live ones is dropped and the others keep their order."""
        live = Glow(spread_px=1.0, strength=0.5)
        stack = EffectStack(effects=(Casing(width_px=0.0), live))
        assert stack.effects == (live,)

    def test_a_list_is_held_as_a_tuple(self) -> None:
        """Effects given as a list are held as a tuple, so the stack hashes."""
        stack = EffectStack(effects=[Casing(width_px=1.0)])  # ty: ignore[invalid-argument-type]
        assert isinstance(stack.effects, tuple)
        assert hash(stack) == hash(EffectStack(effects=(Casing(width_px=1.0),)))

    def test_a_non_effect_is_refused(self) -> None:
        """Something that is no casing, glow, shadow or reserve raises `TypeError`."""
        with pytest.raises(TypeError, match="not a Casing, Glow, Shadow or Reserve"):
            EffectStack(effects=("cased",))  # ty: ignore[invalid-argument-type]

    def test_a_reserve_is_held(self) -> None:
        """A stack takes a reserve, in order beside a glow."""
        reserve = Reserve(width_px=2.0, pool=0.3)
        glow = Glow(spread_px=1.0, strength=0.5)
        assert EffectStack(effects=(reserve, glow)).effects == (reserve, glow)

    def test_a_reserve_of_width_zero_is_off(self) -> None:
        """A reserve of width 0 is dropped, so the stack equals the empty one."""
        assert EffectStack(effects=(Reserve(width_px=0.0, pool=0.5),)) == EffectStack()

    @pytest.mark.parametrize("order", [0, 1], ids=["casing-first", "reserve-first"])
    def test_a_casing_and_a_reserve_are_refused(self, order: int) -> None:
        """A stack takes a casing or a reserve, not both, in either order."""
        pair = (Casing(width_px=1.0), Reserve(width_px=1.0))
        with pytest.raises(ValueError, match="a casing or a reserve, not both"):
            EffectStack(effects=pair[::1] if order == 0 else pair[::-1])

    def test_two_reserves_are_refused(self) -> None:
        """A stack takes at most one reserve."""
        with pytest.raises(ValueError, match="at most one reserve"):
            EffectStack(effects=(Reserve(width_px=1.0), Reserve(width_px=2.0)))

    @pytest.mark.parametrize(
        ("effects", "expected"),
        [
            ((Glow(spread_px=1.0, strength=0.5), Casing(width_px=1.0)), Casing(width_px=1.0)),
            ((Reserve(width_px=2.0),), Reserve(width_px=2.0)),
            ((Shadow(offset_px=1.0, strength=0.3),), None),
        ],
        ids=["casing-after-a-glow", "reserve", "neither"],
    )
    def test_the_ring_effect_is_the_casing_or_reserve(
        self, effects: tuple[Casing | Glow | Shadow | Reserve, ...], expected: object
    ) -> None:
        """`ring_effect` finds the stack's casing or reserve wherever it sits, or `None`."""
        assert ring_effect(EffectStack(effects=effects)) == expected

    def test_no_stack_has_no_ring_effect(self) -> None:
        """A class with no stack has no ring effect."""
        assert ring_effect(None) is None

    def test_a_stack_is_frozen_and_keyword_only(self) -> None:
        """A stack refuses assignment and positional effects."""
        stack = EffectStack()
        with pytest.raises(dataclasses.FrozenInstanceError):
            stack.effects = ()  # ty: ignore[invalid-assignment]
        with pytest.raises(TypeError):
            EffectStack(())  # ty: ignore[too-many-positional-arguments]


class TestTheClasses:
    """The line classes and their draw groups."""

    def test_the_classes_are_the_brush_classes_and_the_route(self) -> None:
        """`LINE_CLASSES` is the brush table's seven classes and `route`."""
        assert frozenset(BrushStyle().brushes) | {"route"} == LINE_CLASSES
        assert len(LINE_CLASSES) == 8

    def test_the_groups_are_the_basemap_classes_in_painting_order(self) -> None:
        """The water group, then the road group, are the seven classes in order."""
        assert WATER_GROUP == ("major", "medium", "minor", "coast")
        assert ROAD_GROUP == ("road_major", "lane", "track")
        assert (*WATER_GROUP, *ROAD_GROUP) == tuple(BrushStyle().brushes)


class TestThePresets:
    """The three built-in presets."""

    def test_the_names(self) -> None:
        """The presets are `cased`, `halo` and `lifted`."""
        assert list(BUILT_IN_PRESETS) == ["cased", "halo", "lifted"]

    def test_each_preset_is_one_live_effect_of_its_kind(self) -> None:
        """`cased` is a casing, `halo` a glow and `lifted` a shadow, each on."""
        kinds = {name: [type(e) for e in stack.effects] for name, stack in BUILT_IN_PRESETS.items()}
        assert kinds == {"cased": [Casing], "halo": [Glow], "lifted": [Shadow]}


class TestTheBasemapTable:
    """`BasemapStyle.line_effects` refuses a key outside the seven classes and drops empties."""

    def test_the_route_key_is_refused(self) -> None:
        """`route` is set on `route_ink.effects`, so the basemap refuses it."""
        with pytest.raises(ValueError, match="'route' is not a basemap line class"):
            BasemapStyle(line_effects={"route": EffectStack()})

    def test_a_misspelt_key_names_the_nearest_class_and_the_seven(self) -> None:
        """`majr` is refused with `major` suggested and every class listed."""
        with pytest.raises(
            ValueError, match=r"'majr'.*did you mean major\?.*the classes are major"
        ) as caught:
            BasemapStyle(line_effects={"majr": EffectStack()})
        assert "road_major, lane, track" in str(caught.value)

    def test_an_empty_stack_is_dropped(self) -> None:
        """A class with an empty or all-off stack is absent, so the table equals `{}`."""
        off = EffectStack(effects=(Casing(width_px=0.0),))
        built = BasemapStyle(line_effects={"major": off, "lane": EffectStack()})
        assert built.line_effects == {}
        assert built == BasemapStyle()

    def test_a_live_stack_is_kept(self) -> None:
        """A class with a live stack stays, beside no empty one."""
        cased = BUILT_IN_PRESETS["cased"]
        built = BasemapStyle(line_effects={"major": cased, "lane": EffectStack()})
        assert built.line_effects == {"major": cased}

    def test_the_helper_does_not_mutate_its_input(self) -> None:
        """`checked_line_effects` returns a new table and leaves the one given."""
        given = {"major": EffectStack()}
        assert checked_line_effects(given) == {}
        assert given == {"major": EffectStack()}
