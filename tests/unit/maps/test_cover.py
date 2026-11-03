"""Land cover rings read from the cached land cover payload."""

import json
from pathlib import Path

import pytest

from pyntpot.maps.cache import Cache
from pyntpot.maps.cover import coastline_chains, cover_rings
from pyntpot.maps.projection import track_projection
from pyntpot.maps.rings import point_in_ring
from pyntpot.maps.sea import sea_from_coast

#: A short synthetic track inside the Lynmouth box.
LATS = [51.2250 + 2e-5 * i for i in range(60)]
LNGS = [-3.8400 + 0.00040 * i for i in range(60)]


def test_the_tag_lookup_takes_the_last_class_that_matches(tmp_path: Path) -> None:
    """A way tagged both ways is the one further down the table, which is the wood."""
    way = {
        "type": "way",
        "tags": {"landuse": "meadow", "natural": "wood"},
        "geometry": [
            {"lat": 51.2250, "lon": -3.8400},
            {"lat": 51.2250, "lon": -3.8380},
            {"lat": 51.2270, "lon": -3.8380},
            {"lat": 51.2270, "lon": -3.8400},
            {"lat": 51.2250, "lon": -3.8400},
        ],
    }
    (tmp_path / "landcover-iTAGS.json").write_text(json.dumps({"elements": [way]}))
    proj, _ = track_projection(LATS, LNGS)
    clip = (-9000.0, -9000.0, 9000.0, 9000.0)
    assert list(cover_rings("iTAGS", proj, clip, 2.0, Cache(tmp_path))) == ["wood"]


def test_a_box_with_no_land_cover_cached_is_bare_paper(tmp_path: Path) -> None:
    """Where nobody has drawn a field the ground stays paper, and that is honest."""
    proj, _ = track_projection(LATS, LNGS)
    clip = (-100.0, -100.0, 100.0, 100.0)
    assert cover_rings("iNONE", proj, clip, 2.0, Cache(tmp_path)) == {}


def test_the_coast_is_cut_at_the_card_edge_and_its_land_is_not_sea(tmp_path: Path) -> None:
    """A coast surveyed a kilometre between vertices still ends on the card edge, land and all."""
    way = {
        "type": "way",
        "tags": {"natural": "coastline"},
        "geometry": [{"lat": 51.2256, "lon": -3.801 - 0.0145 * k} for k in range(6)],
    }
    (tmp_path / "overpass-iCOAST.json").write_text(json.dumps({"elements": [way]}))
    proj, _ = track_projection(LATS, LNGS)
    clip = (-2000.0, -3000.0, 2000.0, 3000.0)
    chains = coastline_chains("iCOAST", proj, clip, Cache(tmp_path))
    assert len(chains) == 1
    assert chains[0][0][0] == pytest.approx(clip[2])
    assert chains[0][-1][0] == pytest.approx(clip[0])
    sea = sea_from_coast(chains, clip)
    _, y_coast = proj(51.2256, -3.83)
    assert any(point_in_ring(0.0, y_coast + 1500.0, ring) for ring in sea)
    assert not any(point_in_ring(0.0, y_coast - 1500.0, ring) for ring in sea)
