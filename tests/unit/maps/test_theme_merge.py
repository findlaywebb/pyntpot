"""`merge`: an override replaces only the keys it names, and a table merges per key."""

import copy
import dataclasses

from pyntpot.ink.brush_style import BrushStyle
from pyntpot.maps.style_groups import CoverStyle
from pyntpot.maps.theme_merge import merge


class TestMerge:
    """What an override keeps and what it replaces."""

    def test_a_nested_key_replaces_only_itself(self) -> None:
        """An override of one group key keeps the group's other keys and the other groups."""
        base = {"wash": {"blooms": True, "wet_bleed_px": 20.0}, "card": {"display_px": 900}}
        assert merge(base, {"wash": {"blooms": False}}) == {
            "wash": {"blooms": False, "wet_bleed_px": 20.0},
            "card": {"display_px": 900},
        }

    def test_a_tuple_replaces_whole(self) -> None:
        """A tuple in the override replaces the base's tuple, never merging by position."""
        base = {"card": {"dark_grid": (80, 60), "display_px": 900}}
        assert merge(base, {"card": {"dark_grid": (40,)}}) == {
            "card": {"dark_grid": (40,), "display_px": 900}
        }

    def test_a_dict_entry_merges_per_key(self) -> None:
        """Overriding `cover.pigments.wood` keeps the other fourteen pigments."""
        pigments = CoverStyle().pigments
        merged = merge(
            {"cover": {"pigments": pigments}}, {"cover": {"pigments": {"wood": "#123456"}}}
        )
        got = merged["cover"]
        assert isinstance(got, dict)
        assert got["pigments"] == {**pigments, "wood": "#123456"}
        assert len(got["pigments"]) == 15

    def test_a_table_entry_deep_merges(self) -> None:
        """Overriding `brush.brush_overrides.lane.pool` keeps `lane.jitter_px`."""
        base = {"brush": dataclasses.asdict(BrushStyle())}
        merged = merge(base, {"brush": {"brush_overrides": {"lane": {"pool": 2.0}}}})
        brush = merged["brush"]
        assert isinstance(brush, dict)
        lane = brush["brush_overrides"]["lane"]
        assert lane["pool"] == 2.0
        assert lane["jitter_px"] == BrushStyle().brush_overrides["lane"]["jitter_px"]

    def test_the_inputs_are_unchanged(self) -> None:
        """Merging leaves both the base and the override as they were."""
        base = {"wash": {"blooms": True, "wet_bleed_px": 20.0}, "card": {"display_px": 900}}
        over = {"wash": {"blooms": False}, "ribbon": {"ribbon_mult": 1.5}}
        before = (copy.deepcopy(base), copy.deepcopy(over))
        merge(base, over)
        assert (base, over) == before

    def test_a_leaf_between_two_tables_is_outside_the_model(self) -> None:
        """A leaf where the other inputs hold a table breaks associativity, so the model forbids it."""
        a = {"k": {"x": 1}}
        b = {"k": 5}
        c = {"k": {"y": 2}}
        assert merge(merge(a, b), c) == {"k": {"y": 2}}
        assert merge(a, merge(b, c)) == {"k": {"x": 1, "y": 2}}
