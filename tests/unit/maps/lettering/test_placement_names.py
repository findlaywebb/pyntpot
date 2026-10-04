"""One name, once: the repeat and near-duplicate guards."""

import math

from pyntpot.ink.polyline import length
from pyntpot.letters.setting import DEFAULT_LINE_PX
from pyntpot.maps.lettering.label import (
    TIER_LANDMARK,
    TIER_RIVER,
    TIER_SETTLEMENT,
    TIER_SPAN,
    Label,
)
from pyntpot.maps.lettering.picks_rivers import pick_rivers
from pyntpot.maps.lettering.placement_along import RIVER_REPEAT_FRAC
from pyntpot.maps.lettering.placement_names import (
    MAJOR_RIVER_LABELS,
    NAME_ALLOWANCE,
    NEAR_DUPLICATE_M,
    _one_place,
    dedupe_names,
)

from support.basemaps import hung_card, label_basemap
from support.lettering import sheet_card


def _named(name, kind, tier, x, y):
    """One label at a point, for the repeat and near-duplicate guards."""
    return Label(
        name=name, kind=kind, why="", px=float(x), py=float(y), tier=tier, size=DEFAULT_LINE_PX
    )


def test_the_major_river_carries_its_name_twice_and_the_others_once():
    """A long feature is met in pieces, so it is named in pieces."""
    # Only the major one: a tributary that runs a third of the card twice-named is
    # repetition rather than help. And the two have to be far apart, or they read
    # as one name written twice.
    big = [[round(float(x), 1), 0.0] for x in range(0, 4000, 25)]
    small = [[500.0, -round(float(y), 1)] for y in range(0, 900, 25)]
    lines = {
        "rivers": [
            {"n": "River Lyn", "c": "major", "d": big},
            {"n": "Heddon", "c": "medium", "d": small},
        ]
    }

    # A tenth of a pixel a metre, the card's top edge 400 m north of the origin.
    card = hung_card(400, 300, 10.0, top=400.0)

    route = [(float(x), 60.0) for x in range(0, 400, 10)]
    got = pick_rivers(label_basemap(), lines, card, route)
    names = [label.name for label in got]
    assert names.count("Lyn") == MAJOR_RIVER_LABELS == 2
    assert names.count("Heddon") == 1
    a, b = [label for label in got if label.name == "Lyn"]
    apart = math.dist((a.px, a.py), (b.px, b.py))
    assert apart > length(a.baseline) * RIVER_REPEAT_FRAC * 0.9


def test_a_settlement_is_lettered_once_however_many_pools_found_it():
    """The name Elm arrived as a settlement and again as the nearest named feature."""
    # The settlement pool and the landmark pool have never known about each
    # other, so a village could be lettered twice, the second
    # time at the end of a long leader from the top of the sheet. The guard is in
    # the one funnel both pools go through.
    elm_settlement = _named("Elm", "settlement", TIER_SETTLEMENT, 495, 168)
    elm_landmark = _named("Elm", "place", TIER_LANDMARK, 495, 168)
    kept = dedupe_names([elm_settlement, elm_landmark], sheet_card())
    assert [label.name for label in kept] == ["Elm"]
    assert kept[0] is elm_settlement, "the lower tier is the one that survives"


def test_the_repeat_guard_is_per_kind_so_the_major_river_keeps_both_names():
    """A long river is read in pieces and is deliberately named twice."""
    # A guard that were one number for the whole sheet would either letter the
    # Lyn once or letter Elm twice, so the allowance belongs to the family.
    river_repeats = [
        _named("Lyn", "river", TIER_RIVER, 100, 100),
        _named("Lyn", "river", TIER_RIVER, 300, 260),
    ]
    towns = [
        _named("Grasmere", "settlement", TIER_SETTLEMENT, 40, 40),
        _named("Grasmere", "settlement", TIER_SETTLEMENT, 340, 240),
    ]
    kept = dedupe_names(river_repeats + towns, sheet_card())
    names = [label.name for label in kept]
    assert names.count("Lyn") == MAJOR_RIVER_LABELS == 2
    assert names.count("Grasmere") == 1
    assert NAME_ALLOWANCE["water"] == MAJOR_RIVER_LABELS


def test_two_names_for_one_place_keep_the_shorter_more_general_one():
    """High Cup Nick and High Cup Nick Cairn are the same headland."""
    # Five metres apart, and one name is the other with a structure on the end of
    # it. The tiers rank what a name is, so a tie between two landmarks is broken
    # by the shorter and more general name: the headland, not the chimney
    # standing on it.
    headland = _named("High Cup Nick", "viewpoint", TIER_LANDMARK, 248, 554)
    chimney = _named("High Cup Nick Cairn", "ruin", TIER_LANDMARK, 249, 553)
    kept = dedupe_names([chimney, headland], sheet_card())
    assert [label.name for label in kept] == ["High Cup Nick"]


def test_a_town_and_a_monument_in_it_are_two_places_and_both_letter():
    """The string relationship alone is not enough, and neither is the distance."""
    # Monmouth and Monmouth War Memorial stand in the same word relationship as
    # High Cup Nick and its chimney. What tells them apart is 485 m against five.
    town = _named("Monmouth", "settlement", TIER_SETTLEMENT, 294, 592)
    memorial = _named(
        "Monmouth War Memorial", "monument", TIER_LANDMARK, 294 + NEAR_DUPLICATE_M * 2.0, 592
    )
    kept = dedupe_names([town, memorial], sheet_card())
    assert len(kept) == 2, "far enough apart to be a town and a thing in it"
    # And near enough, they are one place again.
    close = _named(
        "Monmouth War Memorial", "monument", TIER_LANDMARK, 294 + NEAR_DUPLICATE_M * 0.1, 592
    )
    assert [label.name for label in dedupe_names([town, close], sheet_card())] == ["Monmouth"]


def test_a_shared_word_is_not_a_shared_place():
    """Two names that only overlap in the middle are two names."""
    assert _one_place("High Cup Nick", "High Cup Nick Cairn")
    assert _one_place("Grasmere", "Upper Grasmere"), "a qualifier is stripped"
    assert not _one_place("High Cup Nick", "High Cup Nicks")
    assert not _one_place("Abergavenny", "Lyn Valley Walk")
    assert not _one_place("Monmouth", "Monmouth Castle Field Museum")


def test_a_span_name_is_never_deduped():
    """A span's name is prose about a stretch, not a name for somewhere."""
    twice = [
        _named("the steady middle hour", "climb", TIER_SPAN, 100, 100),
        _named("the steady middle hour", "fast", TIER_SPAN, 110, 100),
    ]
    assert len(dedupe_names(twice, sheet_card())) == 2
