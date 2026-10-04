"""What the map names: the named lines, the settlements and the rivers a card picks."""

import math

from pyntpot.maps.basemap import River, Road
from pyntpot.maps.lettering.picks_lines import named_lines
from pyntpot.maps.lettering.picks_rivers import pick_rivers
from pyntpot.maps.lettering.picks_settlements import (
    pick_settlements,
    settlement_budget,
    settlements,
)

from support.basemaps import label_basemap, tiny_basemap, tiny_style, wide_card


def test_the_named_lines_keep_what_a_name_can_be_set_along():
    """Named roads and watercourses become named lines; unnamed ones do not.

    The geo payload is transient and re-deriving it at label time costs seven
    seconds and a network the renderer must not need, so the centrelines a
    curved baseline is taken from are read from the basemap the plates came from.
    """
    basemap = tiny_basemap(
        roads=(
            Road(((0.0, 0.0), (300.0, 4.0), (600.0, 0.0)), "major", "major", "primary", "A39", ""),
            Road(((0.0, 90.0), (600.0, 90.0)), "minor", "minor", "unclassified", "", ""),
        ),
        rivers=(
            River(((0.0, 40.0), (400.0, 44.0), (800.0, 40.0)), "major", "River Lyn", 0.0, 0.0),
        ),
        coastline=(((0.0, 10.0), (900.0, 12.0)),),
    )
    geom = named_lines(basemap, tiny_style().lettering.label_geom_tol_px)
    assert [r["n"] for r in geom["roads"]] == ["A39"]
    assert [r["n"] for r in geom["rivers"]] == ["River Lyn"]
    assert len(geom["coast"]) == 1
    assert all(len(line["d"]) >= 2 for line in geom["roads"] + geom["rivers"])


def _labelled_card(**basemap_over):
    """A tiny basemap and the card that projects into it, for the label rules."""
    basemap = tiny_basemap(**basemap_over)
    card = basemap.card
    route = [(float(x), 40.0 + 30.0 * math.sin(x / 260.0)) for x in range(0, 1400, 40)]
    return basemap, card, [card.xy(x, y) for x, y in route]


def _place_node(name, kind, x, y, off):
    """One settlement as `journal_candidates` writes it into the basemap."""
    return {
        "name": name,
        "class": "place",
        "lat": 0.0,
        "lng": 0.0,
        "x": x,
        "y": y,
        "distance_m": off,
        "tags": {"place": kind},
    }


def test_upper_and_lower_are_one_place_under_their_shared_stem():
    """A reader says Grasmere; OSM has two nodes and neither is called that."""
    basemap, _card, _route_px = _labelled_card(
        candidates=[
            _place_node("Upper Grasmere", "village", 200.0, 44.0, 241),
            _place_node("Lower Grasmere", "village", 340.0, 40.0, 70),
        ],
    )
    found = settlements(basemap)
    assert [e["name"] for e in found] == ["Grasmere"]
    # Positioned on the member the route actually came nearest.
    assert found[0]["off_route_m"] == 70


def test_the_settlements_are_chosen_by_rank_and_by_route_not_by_distance():
    """A distance sort spends every slot inside one town. This one does not."""
    basemap, card, route_px = _labelled_card(
        candidates=[
            _place_node("Little Combes", "hamlet", 100.0, 42.0, 4),
            _place_node("Tarns Bridge", "hamlet", 180.0, 44.0, 18),
            _place_node("Abergavenny", "town", 600.0, 45.0, 3),
            _place_node("Monmouth", "town", 1100.0, 20.0, 441),
            _place_node("Faraway", "village", 700.0, 60.0, 4000),
        ],
    )
    picked = [label.name for label in pick_settlements(basemap, card, route_px)]
    assert "Abergavenny" in picked and "Monmouth" in picked
    assert "Faraway" not in picked, "over 1.5 km off the route is not this ride"
    assert len(picked) <= settlement_budget(card.w)


def test_a_hamlet_alone_in_empty_country_is_not_worth_a_name():
    """A floor, so a run through nowhere gets one label or none, not three."""
    basemap, card, route_px = _labelled_card(
        candidates=[
            _place_node("Brendon", "hamlet", 300.0, 44.0, 700),
        ],
    )
    assert pick_settlements(basemap, card, route_px) == []


def test_the_river_the_route_crossed_beats_the_one_it_did_not():
    """Run length alone cannot separate two tributaries; the route can."""
    crossed = [[float(x), 40.0 + 30.0 * math.sin(x / 260.0)] for x in range(0, 1400, 40)]
    away = [[float(x), 900.0] for x in range(0, 1400, 40)]
    basemap, card, route_px = _labelled_card()
    lines = {
        "roads": [],
        "coast": [],
        "rivers": [
            {"n": "River Heddon", "c": "medium", "d": crossed},
            {"n": "River Medway", "c": "medium", "d": away},
            {"n": "Hebden Beck", "c": "minor", "d": crossed},
        ],
    }
    named = [x.name for x in pick_rivers(basemap, lines, card, route_px)]
    assert named[0] == "Heddon", "the name loses its 'River', the water says it"
    assert "Hebden Beck" not in named, "a beck is noise at this scale"


def test_the_second_river_name_is_earned_by_the_run():
    """A river that clips a corner is read in one piece and named once.

    The second name exists because a river crossing the whole sheet is read in
    pieces. The Severn has 295 px of water on a 900 px card and taking both
    allowances wrote the second name in open paper past the end of the river.
    """

    def rivers(x1):
        lines = {"rivers": [{"n": "Severn", "c": "major", "w": 30.0, "d": [[100, 271], [x1, 271]]}]}
        basemap = label_basemap(wet_px={"major": 11.0})
        return pick_rivers(basemap, lines, wide_card(), [(100.0, 100.0), (800.0, 100.0)])

    short = [label.name for label in rivers(395)]  # 295 px of water
    assert short == ["Severn"], "a corner of river was lettered twice"
    long = [label.name for label in rivers(800)]  # 700 px of water
    assert long == ["Severn", "Severn"], "a river across the sheet lost its second name"
