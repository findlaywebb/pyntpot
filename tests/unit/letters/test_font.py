"""Tests for the outline font: both routes draw every glyph, and the real map strings come back whole."""

from __future__ import annotations

import pytest

from pyntpot.letters.font import DEFAULT_FONT, load
from pyntpot.letters.trace import CENTRELINE, OUTLINE

#: Every string this map actually letters, so the alphabet sheet and the tests
#: cover the same ground the card does.
MAP_STRINGS = (
    "Monmouth",
    "Monmouth Castle",
    "Abergavenny",
    "Grasmere",
    "Lyn",
    "Heddon",
    "A361",
    "A3052",
    "the long climb out of Aviemore",
    "the A39 drag to St Anne's Cross",
)


class TestRoutes:
    """Centreline and outline are two answers, and neither drops a letter."""

    @pytest.mark.parametrize("route", [CENTRELINE, OUTLINE], ids=[CENTRELINE, OUTLINE])
    def test_both_letterform_routes_draw_every_glyph_of_a_name(self, route: str) -> None:
        """Every glyph of a name has an advance and ink on each route, none a stray point."""
        face = load(route=route)
        for ch in "Abergavenny 12%":
            glyph = face.glyph(ch)
            assert glyph.advance > 0
            assert glyph.ink or ch == " ", f"{ch!r} came back blank on {route}"
            for path in glyph.paths:
                assert len(path) >= 2


class TestFace:
    """The vendored face is found and measures real strings."""

    def test_the_vendored_face_is_found_beside_the_package(self) -> None:
        """The default face resolves to the vendored file and opens through the cached loader."""
        assert DEFAULT_FONT.is_file()
        assert load().name == "PatrickHand-Regular"

    @pytest.mark.parametrize("text", MAP_STRINGS, ids=MAP_STRINGS)
    def test_every_name_this_map_letters_comes_back_whole(self, text: str) -> None:
        """Every glyph of a real map string has width, and ink unless it is a space."""
        face = load()
        assert face.measure(text, 20.0)[0] > 0
        for ch in text:
            glyph = face.glyph(ch)
            assert glyph.advance > 0, f"{ch!r} in {text!r} has no advance"
            assert glyph.ink or ch == " ", f"{ch!r} in {text!r} came back blank"
