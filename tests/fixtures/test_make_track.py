"""Tests for `make_track`: `ref=` items chain a road's ways, and `--step-m` sets the spacing."""

from typing import Any

import pytest
from fixtures.make_track import (
    TrackError,
    assemble,
    chain,
    chain_ref,
    length_km,
    parse_items,
    resample,
)

_LAT = 51.23
_LON0 = -3.84
_STEP = 0.0010


def _way(way_id: int, first: int, last: int, *, ref: str = "A1") -> dict[str, Any]:
    """A way along one parallel, its nodes numbered first..last, one 0.001 degree apart."""
    nodes = list(range(first, last + 1))
    geometry = [{"lat": _LAT, "lon": _LON0 + n * _STEP} for n in nodes]
    return {
        "type": "way",
        "id": way_id,
        "version": 1,
        "nodes": nodes,
        "geometry": geometry,
        "tags": {"highway": "primary", "ref": ref},
    }


def _line(ways: list[dict[str, Any]]) -> list[int]:
    """The node ids a chained way runs through."""
    return [int(n) for n in chain_ref(ways, "A1")["nodes"]]


class TestParseItems:
    """`--ways` items are ids, cut ids, refs and cut refs, in one ordered list."""

    def test_the_four_forms_parse_in_order(self) -> None:
        """An id, a cut id, a ref and a cut ref parse to triples in the order given."""
        items = parse_items("7,8:1:2,ref=A87,ref=B8009:3:4")
        assert items == [(7, None, None), (8, 1, 2), ("A87", None, None), ("B8009", 3, 4)]

    def test_a_single_cut_node_is_refused(self) -> None:
        """An item with one node after the id is a usage error."""
        with pytest.raises(TrackError):
            parse_items("ref=A87:3")


class TestChainRef:
    """The ways of one ref join end to end into one ordered line."""

    def test_three_shuffled_ways_chain_into_one_line(self) -> None:
        """Ways given out of order come back as one run of nodes with the joints once."""
        ways = [_way(2, 3, 5), _way(3, 5, 7), _way(1, 1, 3)]
        nodes = _line(ways)
        assert nodes in ([1, 2, 3, 4, 5, 6, 7], [7, 6, 5, 4, 3, 2, 1])

    def test_a_reversed_way_is_flipped(self) -> None:
        """A way digitised against the others runs the same way in the chained line."""
        reversed_way = _way(2, 3, 5)
        reversed_way["nodes"] = reversed_way["nodes"][::-1]
        reversed_way["geometry"] = reversed_way["geometry"][::-1]
        nodes = _line([_way(1, 1, 3), reversed_way])
        assert nodes in ([1, 2, 3, 4, 5], [5, 4, 3, 2, 1])

    def test_a_six_metre_gap_fails_naming_ids(self) -> None:
        """Two ways 6 m apart, with no shared node, are refused and named by id."""
        gapped = _way(2, 13, 15)
        gapped["geometry"][0]["lon"] = _LON0 + 3 * _STEP + 0.00009
        with pytest.raises(TrackError, match=r"gap.*\b1\b.*\b2\b"):
            _line([_way(1, 1, 3), gapped])

    def test_a_four_metre_gap_joins(self) -> None:
        """Two ways 4 m apart with different end nodes join."""
        near = _way(2, 13, 15)
        near["geometry"][0]["lon"] = _LON0 + 3 * _STEP + 0.00006
        assert _line([_way(1, 1, 3), near]) in ([1, 2, 3, 13, 14, 15], [15, 14, 13, 3, 2, 1])

    def test_a_fork_fails_naming_its_ids(self) -> None:
        """Three ways meeting at one node are refused, and the message names them."""
        ways = [_way(1, 1, 3), _way(2, 3, 5), _way(3, 3, 6)]
        with pytest.raises(TrackError, match=r"fork.*\b1\b.*\b2\b.*\b3\b"):
            _line(ways)

    def test_a_closed_way_fails(self) -> None:
        """A way that starts and ends on one node is refused."""
        ring = _way(4, 1, 4)
        ring["nodes"][-1] = 1
        with pytest.raises(TrackError, match="closed"):
            _line([ring])

    def test_a_single_way_is_its_own_line(self) -> None:
        """One way chains to itself."""
        assert _line([_way(1, 1, 3)]) == [1, 2, 3]


class TestAssemble:
    """Ref items and id items resolve to ways in the order given, cut where asked."""

    def test_a_ref_item_and_an_id_item_keep_their_order(self) -> None:
        """A ref, an id, then the ref again give three ways in that order."""
        found = {9: _way(9, 5, 7, ref="B2")}
        refs = {"A1": [_way(1, 1, 3), _way(2, 3, 5)]}
        items: list[Any] = [("A1", 1, 5), (9, None, None), ("A1", 5, 1)]
        built = assemble(items, found, refs)
        assert [w["nodes"][0] for w in built] == [1, 5, 5]
        assert built[0]["nodes"] == [1, 2, 3, 4, 5]
        assert built[2]["nodes"] == [5, 4, 3, 2, 1]

    def test_from_to_cuts_the_chain_at_those_nodes(self) -> None:
        """FROM:TO keeps only the chained stretch between the two nodes."""
        refs = {"A1": [_way(2, 3, 5), _way(1, 1, 3)]}
        built = assemble([("A1", 2, 4)], {}, refs)
        assert built[0]["nodes"] == [2, 3, 4]

    def test_a_ref_without_ways_fails(self) -> None:
        """A ref the box did not return is a failure naming the ref."""
        with pytest.raises(TrackError, match="A9"):
            assemble([("A9", None, None)], {}, {"A9": []})

    def test_assembled_ways_chain_into_a_track(self) -> None:
        """An out-and-back leg from a ref chains back onto itself."""
        refs = {"A1": [_way(1, 1, 3), _way(2, 3, 5)]}
        built = assemble([("A1", 1, 5), ("A1", 5, 3)], {}, refs)
        assert len(chain(built)) == 5 + 2


class TestStep:
    """`resample` spaces points by the step it is given."""

    def test_a_wider_step_gives_fewer_points(self) -> None:
        """A 100 m step on a 1 km line gives about a tenth the points of a 10 m step."""
        line = [(_LAT, _LON0 + n * _STEP) for n in range(15)]
        fine, coarse = resample(line, 10.0), resample(line, 100.0)
        assert len(coarse) * 5 < len(fine)
        assert length_km(coarse) == pytest.approx(length_km(fine), rel=0.01)
