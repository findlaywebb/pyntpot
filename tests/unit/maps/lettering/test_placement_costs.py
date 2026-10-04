"""What a name costs where it sits: the roads, its own feature and the route."""

from pyntpot.maps.lettering.label import TIER_ROAD, Label
from pyntpot.maps.lettering.picks_lines import road_lines
from pyntpot.maps.lettering.placement_costs import _off_own, _off_own_feature, _on_road

from support.basemaps import hung_card, river_label


def test_a_road_name_stays_near_the_road_it_names():
    """Aviemore Road sat far enough off its tarmac to be a guess."""
    # With no leader drawn, the only thing joining a road name to its road is
    # that they are near each other, so distance from its own centreline is a
    # cost in its own right.
    tarmac = [(float(x), 150.0) for x in range(20, 380, 5)]
    near = Label(
        name="A361", kind="road", px=200.0, py=150.0, tier=TIER_ROAD, size=14.0, baseline=tarmac
    )
    far = Label(
        name="A361", kind="road", px=200.0, py=150.0, tier=TIER_ROAD, size=14.0, baseline=tarmac
    )
    close = (0.0, 0.0, 40.0, 40.0)
    assert _off_own_feature(close, far) > 0.0
    assert _off_own_feature((190.0, 140.0, 230.0, 160.0), near) == 0.0


def test_a_name_is_not_charged_for_crossing_the_thing_it_names():
    """`road_lines` holds the watercourses as well as the tarmac."""
    # For a name set along its own feature that includes the feature itself, so
    # every candidate window scored as "on a road" and the term cancelled out: the
    # Severn could not be moved off a bridge because it was on a road wherever it
    # went.
    water = [(100.0, 400.0), (800.0, 400.0)]
    bridge = [(500.0, 300.0), (500.0, 500.0)]
    name = river_label(40.0)
    kept = _off_own([water, bridge], name)
    assert kept == [bridge]
    # A name beside its feature is filtered the same way; everything else stays.
    assert _off_own([bridge], name) == [bridge]


def test_an_unnamed_lane_and_a_watercourse_both_cost_a_name_that_crosses_them():
    """A mark on the paper is a mark on the paper, named or not."""
    # Only the named roads were charged, so a label could be laid across an
    # unnamed lane for nothing and a settlement could sit on its own river.
    card = hung_card(400, 300, 1.0)

    named = {
        "roads": [{"n": "A361", "c": "major", "d": [[0, -10], [400, -10]]}],
        "rivers": [{"n": "Lyn", "c": "major", "d": [[0, -60], [400, -60]]}],
        "crossings": [[[0, -120], [400, -120]]],
    }
    lines = road_lines(named, card)
    assert len(lines) == 3, "the lanes and the water are not in the crossing cost"
    for y in (10.0, 60.0, 120.0):
        assert _on_road((100.0, y - 4, 200.0, y + 4), lines) == 1.0
