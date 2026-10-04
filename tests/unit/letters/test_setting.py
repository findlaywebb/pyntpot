"""Tests for the hand's setting and its marks: construction, identity and defaults."""

import dataclasses
from typing import Any

import pytest

from pyntpot.letters.setting import DEFAULT_LINE_PX, Mark, Setting

#: A straight line a name could be written along, in card pixels.
LINE = ((10.0, 40.0), (60.0, 38.0), (110.0, 41.0))


class TestSetting:
    """A setting is one frozen, hashable request that says plainly how it is set."""

    def test_a_setting_along_a_line_keeps_what_it_was_given(self) -> None:
        """A name along a line carries its text, size, path and manner unchanged."""
        setting = Setting("Grasmere", 14.0, path=LINE, slant=0.22, tracking=0.24, ink="water")
        assert setting.text == "Grasmere"
        assert setting.size == 14.0
        assert setting.path == LINE
        assert setting.anchor is None
        assert (setting.slant, setting.tracking, setting.ink) == (0.22, 0.24, "water")

    def test_a_flat_setting_defaults_to_one_upright_row_in_map_ink(self) -> None:
        """A flat setting with only an anchor is upright, untracked, map ink, washed."""
        setting = Setting("Keswick", 20.0, anchor=(40.0, 30.0))
        assert setting.align == "start"
        assert (setting.slant, setting.tracking) == (0.0, 0.0)
        assert setting.ink == "map"
        assert setting.lines == ()
        assert setting.wash is True

    def test_equal_settings_are_equal_and_hash_alike(self) -> None:
        """Two settings built from the same values are one key."""
        one = Setting("Aviemore", 16.0, anchor=(5.0, 6.0), lines=("Avie", "more"))
        two = Setting("Aviemore", 16.0, anchor=(5.0, 6.0), lines=("Avie", "more"))
        assert one == two
        assert hash(one) == hash(two)
        assert len({one, two}) == 1

    def test_a_changed_field_is_a_different_setting(self) -> None:
        """Any one field changed makes a setting that is not equal to the first."""
        one = Setting("Settle", 16.0, anchor=(5.0, 6.0))
        assert dataclasses.replace(one, ink="route") != one
        assert dataclasses.replace(one, align="middle") != one

    def test_a_setting_is_frozen(self) -> None:
        """A setting cannot be changed after it is built."""
        setting = Setting("Hawes", 16.0, anchor=(5.0, 6.0))
        with pytest.raises(dataclasses.FrozenInstanceError):
            delattr(setting, "text")

    @pytest.mark.parametrize(
        "kwargs",
        [
            {},
            {"anchor": (1.0, 2.0), "path": LINE},
            {"path": ((1.0, 2.0),)},
            {"path": LINE, "lines": ("Tw", "eed")},
            {"path": LINE, "align": "middle"},
        ],
        ids=["neither", "both", "one-point-path", "path-with-lines", "path-with-align"],
    )
    def test_an_unclear_setting_is_refused(self, kwargs: dict[str, Any]) -> None:
        """A setting that is not plainly flat or plainly along one line is refused."""
        with pytest.raises(ValueError, match=r"setting|path"):
            Setting("Tweed", 14.0, **kwargs)


class TestMark:
    """A mark is one stroke in card pixels with pinned defaults."""

    def test_a_mark_defaults_to_a_washed_glyph_in_map_ink_at_the_line_size(self) -> None:
        """A mark given only points is a glyph, map ink, 20 px, no pen tilt, washed."""
        mark = Mark(pts=[(0.0, 0.0), (1.0, 1.0)])
        assert mark.role == "glyph"
        assert mark.ink == "map"
        assert mark.size == 20.0
        assert mark.pen == 0.0
        assert mark.wash is True

    def test_the_default_line_size_is_twenty_pixels(self) -> None:
        """The default type size is the pinned 20 display pixels."""
        assert DEFAULT_LINE_PX == 20.0
