"""What a name costs where it sits: the roads, its own feature and the route."""

from pyntpot.maps.lettering.label import TIER_ROAD, Label
from pyntpot.maps.lettering.picks_lines import road_lines
from pyntpot.maps.lettering.placement_costs import (
    LEADER_ROUTE_SLACK_PX,
    RouteSegments,
    leader_route_crossings,
    off_own,
    off_own_feature,
    on_road,
)

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
    assert off_own_feature(close, far) > 0.0
    assert off_own_feature((190.0, 140.0, 230.0, 160.0), near) == 0.0


def test_a_name_is_not_charged_for_crossing_the_thing_it_names():
    """`road_lines` holds the watercourses as well as the tarmac."""
    # For a name set along its own feature that includes the feature itself, so
    # every candidate window scored as "on a road" and the term cancelled out: the
    # Severn could not be moved off a bridge because it was on a road wherever it
    # went.
    water = [(100.0, 400.0), (800.0, 400.0)]
    bridge = [(500.0, 300.0), (500.0, 500.0)]
    name = river_label(40.0)
    kept = off_own([water, bridge], name)
    assert kept == [bridge]
    # A name beside its feature is filtered the same way; everything else stays.
    assert off_own([bridge], name) == [bridge]


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
        assert on_road((100.0, y - 4, 200.0, y + 4), lines) == 1.0


class TestLeaderRouteCrossings:
    """A leader is counted for each time it crosses the route past its own pin."""

    #: The track running north to south down x 200, doubling back down x 260.
    ROUTE = ((200.0, 0.0), (200.0, 300.0), (260.0, 300.0), (260.0, 0.0))

    def test_a_leader_kept_to_its_pins_side_crosses_nothing(self):
        """Castell y Fenni's pin west of the track, its name further west."""
        segments = RouteSegments.of(list(self.ROUTE))
        assert leader_route_crossings((195.0, 150.0), (120.0, 120.0), segments) == 0.0

    def test_a_leader_across_the_track_beside_its_pin_is_counted(self):
        """Bean & Bread's pin five pixels west of the track, its name to the east."""
        segments = RouteSegments.of(list(self.ROUTE))
        assert leader_route_crossings((195.0, 150.0), (230.0, 120.0), segments) == 1.0

    def test_a_leader_through_a_route_point_is_counted_once(self):
        """The track as a run of points: a leader through one of them crosses it once."""
        segments = RouteSegments.of([(200.0, float(y)) for y in range(0, 301, 5)])
        assert leader_route_crossings((195.0, 150.0), (230.0, 150.0), segments) == 1.0

    def test_each_strand_crossed_is_counted(self):
        """A leader over both strands of a doubled-back route crosses it twice."""
        segments = RouteSegments.of(list(self.ROUTE))
        assert leader_route_crossings((195.0, 150.0), (300.0, 150.0), segments) == 2.0

    def test_the_track_through_the_pin_is_not_counted(self):
        """Crib Goch's pin sits on the track, so its leader leaves from the line."""
        segments = RouteSegments.of(list(self.ROUTE))
        on_pin = 200.0 - LEADER_ROUTE_SLACK_PX / 2
        assert leader_route_crossings((on_pin, 150.0), (240.0, 150.0), segments) == 0.0

    def test_no_route_prices_nothing(self):
        """A card with fewer than two route points has no segment to cross."""
        empty = RouteSegments.of([(200.0, 150.0)])
        assert leader_route_crossings((150.0, 150.0), (250.0, 150.0), empty) == 0.0
