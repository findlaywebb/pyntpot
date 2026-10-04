"""River width: channels, measured width and the main river."""

from itertools import pairwise

import pytest

from pyntpot.maps.rivers import channel, major_rivers, measured_width_m, painted_width_px


def _channel(x0: float, x1: float, half: float) -> list[tuple[float, float]]:
    """A straight water area running east to west, `half * 2` metres wide."""
    return [(x0, -half), (x1, -half), (x1, half), (x0, half)]


def test_a_river_is_measured_against_the_water_it_runs_in():
    """OSM maps a big river twice: a line for where, a polygon for how wide."""
    line = [[(0.0, 0.0), (2000.0, 0.0)]]
    got = measured_width_m(line, [_channel(-100.0, 2100.0, 120.0)])
    assert got == pytest.approx(240.0, abs=2.0)


def test_a_river_is_re_centred_in_its_own_channel():
    """OSM's line says where a river goes, not that it runs down the middle."""
    off_centre = [(0.0, 60.0), (2000.0, 60.0)]
    pts, widths = channel(off_centre, [_channel(-100.0, 2100.0, 120.0)])
    middle = pts[len(pts) // 2]
    assert middle[1] == pytest.approx(0.0, abs=2.0)
    assert widths[len(widths) // 2] == pytest.approx(240.0, abs=2.0)


def test_the_width_comes_from_both_banks():
    """Twice the nearest bank understates a river its line does not halve."""
    off_centre = [[(0.0, 60.0), (2000.0, 60.0)]]
    got = measured_width_m(off_centre, [_channel(-100.0, 2100.0, 120.0)])
    assert got == pytest.approx(240.0, abs=2.0)


def test_the_correction_is_eased_rather_than_stepped():
    """A river slides into the middle of its channel; it does not jump."""
    line = [(0.0, 0.0), (3000.0, 0.0)]
    # A channel that steps sideways halfway along, so the middle moves with it.
    ring = [
        (-100.0, -120.0),
        (1500.0, -120.0),
        (1500.0, -20.0),
        (3100.0, -20.0),
        (3100.0, 220.0),
        (1500.0, 220.0),
        (1500.0, 120.0),
        (-100.0, 120.0),
    ]
    pts, _widths = channel(line, [ring])
    steps = [abs(b[1] - a[1]) for a, b in pairwise(pts)]
    assert max(steps) < 40.0, "the line steps sideways instead of easing"


def test_a_tributarys_mouth_is_not_its_width():
    """The Swale meets the Wharfe inside the Wharfe's own polygon."""
    mouth = [[(0.0, -400.0), (0.0, -20.0)]]
    assert measured_width_m(mouth, [_channel(-500.0, 500.0, 120.0)]) is None


def test_a_watercourse_outside_every_area_is_not_measured():
    """A culvert has no banks to measure, and says so rather than guessing."""
    assert (
        measured_width_m([[(0.0, 900.0), (2000.0, 900.0)]], [_channel(-100.0, 2100.0, 120.0)])
        is None
    )


def test_thin_water_is_exaggerated_up_to_the_floor():
    """A brook two metres across is not drawn two metres across."""
    assert painted_width_px(4.69, 2.0, 7.533) == 4.69
    assert painted_width_px(4.69, 0.0, 7.533) == 4.69


def test_wide_water_is_drawn_at_its_own_width():
    """The Wharfe is a quarter of a kilometre wide and is drawn as one."""
    assert painted_width_px(10.83, 221.0, 7.533) == pytest.approx(29.34, abs=0.1)


def test_a_measured_river_is_never_exaggerated_further():
    """The floor is a floor, not a multiplier: nothing is added on top of it."""
    wide = painted_width_px(10.83, 221.0, 7.533)
    assert wide == pytest.approx(221.0 / 7.533, abs=0.01)


def test_the_widest_water_is_the_main_river_not_the_longest():
    """A 4.8 km culvert does not outrank the Wharfe clipping a corner."""
    pieces = {
        "Wharfe": [[(0.0, 0.0), (2000.0, 0.0)]],
        "Swale": [[(500.0, 900.0), (500.0, 6000.0)]],
    }
    major, widths = major_rivers(pieces, [_channel(-100.0, 2100.0, 120.0)], 0.65)
    assert major == {"Wharfe"}
    assert "Swale" not in widths


def test_the_longest_run_still_wins_where_nothing_is_mapped_as_an_area():
    """Away from a big river no watercourse has a polygon, and the old rule holds."""
    pieces = {
        "Tay": [[(0.0, 0.0), (6000.0, 0.0)]],
        "Teviot": [[(0.0, 500.0), (900.0, 500.0)]],
    }
    major, widths = major_rivers(pieces, [], 0.65)
    assert major == {"Tay"}
    assert widths == {}
