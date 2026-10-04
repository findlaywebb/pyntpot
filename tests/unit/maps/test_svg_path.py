"""SVG path data: the vector map output format."""

from pyntpot.maps.svg_path import stroke_d


def test_a_stroke_path_is_written_as_deltas():
    """Hachures ship as relative steps, which is what keeps the layer small."""
    d = stroke_d([(100.0, 200.0), (110.0, 205.0), (118.0, 212.0)])
    assert d == "M100,200l10,5l8,7"
