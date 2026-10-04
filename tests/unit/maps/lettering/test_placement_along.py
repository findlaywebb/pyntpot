"""Setting a name along a line of its own."""

from pyntpot.maps.lettering.placement_along import TWO_SIDED_KINDS


def test_a_river_name_may_sit_on_either_side_of_its_own_water():
    """Which side is a question about what is underneath, not about the river."""
    assert "river" in TWO_SIDED_KINDS
    assert "road" in TWO_SIDED_KINDS
    assert "settlement" not in TWO_SIDED_KINDS
