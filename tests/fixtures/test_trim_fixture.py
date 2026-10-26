"""Tests for `trim_fixture`: the fixture trim keeps what the code reads and nothing else."""

import json
from pathlib import Path
from typing import Any

from fixtures.trim_fixture import main, trim_payload


def _payload() -> dict[str, Any]:
    """A three-element payload: a node, a way with a collinear midpoint, a relation."""
    line = [
        {"lat": 51.2300, "lon": -3.8300},
        {"lat": 51.2301, "lon": -3.8299},
        {"lat": 51.2302, "lon": -3.8298},
    ]
    return {
        "version": 0.6,
        "generator": "Overpass API test",
        "osm3s": {"copyright": "ODbL"},
        "elements": [
            {
                "type": "node",
                "id": 1,
                "lat": 51.23,
                "lon": -3.83,
                "tags": {
                    "name": "Lynmouth",
                    "name:cy": "Aber Llyn",
                    "wikidata": "Q1",
                    "source": "survey",
                },
            },
            {
                "type": "way",
                "id": 2,
                "bounds": {"minlat": 51.23, "minlon": -3.83, "maxlat": 51.2302, "maxlon": -3.8298},
                "nodes": [10, 11, 12],
                "geometry": line,
                "tags": {"highway": "path", "created_by": "editor"},
            },
            {
                "type": "relation",
                "id": 3,
                "bounds": {"minlat": 51.23, "minlon": -3.83, "maxlat": 51.2302, "maxlon": -3.8298},
                "members": [{"type": "way", "ref": 2, "role": "outer", "geometry": line}],
                "tags": {"natural": "water", "type": "multipolygon"},
            },
        ],
    }


def _write(tmp_path: Path) -> Path:
    """Write the hand-built payload, pretty-printed as Overpass sends it."""
    path = tmp_path / "overpass-x.json"
    path.write_text(json.dumps(_payload(), indent=2), encoding="utf-8")
    return path


class TestTrim:
    """What a trimmed payload keeps and drops."""

    def test_output_is_minified_with_one_trailing_newline(self, tmp_path: Path) -> None:
        """The file has no spaces after separators and ends in exactly one newline."""
        path = _write(tmp_path)
        assert main([str(path)]) == 0
        text = path.read_text(encoding="utf-8")
        assert text.endswith("}\n")
        assert not text.endswith("\n\n")
        assert '": ' not in text
        assert ", " not in text

    def test_nodes_and_bounds_are_gone_and_the_header_stays(self) -> None:
        """Elements lose `nodes` and `bounds`; `version`, `generator` and `osm3s` stay."""
        out = trim_payload(_payload())
        assert {"version", "generator", "osm3s"} <= set(out)
        for element in out["elements"]:
            assert "nodes" not in element
            assert "bounds" not in element
        assert out["elements"][2]["members"][0]["geometry"]

    def test_unread_tags_go_and_name_and_wikidata_stay(self) -> None:
        """`source` and `created_by` are dropped; `name:cy` and `wikidata` are kept."""
        out = trim_payload(_payload())
        assert out["elements"][0]["tags"] == {
            "name": "Lynmouth",
            "name:cy": "Aber Llyn",
            "wikidata": "Q1",
        }
        assert out["elements"][1]["tags"] == {"highway": "path"}

    def test_a_second_run_is_byte_identical(self, tmp_path: Path) -> None:
        """Trimming a trimmed file changes nothing."""
        path = _write(tmp_path)
        main([str(path)])
        first = path.read_bytes()
        main([str(path)])
        assert path.read_bytes() == first


class TestSimplify:
    """`--simplify-m` thins geometry and keeps the ends."""

    def test_collinear_midpoint_is_dropped_and_ends_are_kept(self, tmp_path: Path) -> None:
        """The straight three-point way becomes its two end points, exactly."""
        path = _write(tmp_path)
        assert main(["--simplify-m", "5", str(path)]) == 0
        elements = json.loads(path.read_text(encoding="utf-8"))["elements"]
        assert elements[1]["geometry"] == [
            {"lat": 51.2300, "lon": -3.8300},
            {"lat": 51.2302, "lon": -3.8298},
        ]
        assert len(elements[2]["members"][0]["geometry"]) == 2


def _ring(lat: float, lon: float, size: float) -> list[dict[str, float]]:
    """A closed square ring of `size` degrees whose south-west corner is (lat, lon)."""
    corners = [(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)]
    return [{"lat": lat + size * a, "lon": lon + size * b} for a, b in corners]


def _scale_payload() -> dict[str, Any]:
    """Roads of several classes and closed ways and relations of several sizes."""
    small, big = 0.0001, 0.01
    road = [{"lat": 51.23, "lon": -3.83}, {"lat": 51.24, "lon": -3.82}]
    elements: list[dict[str, Any]] = [
        {"type": "way", "id": i, "geometry": road, "tags": {"highway": highway}}
        for i, highway in enumerate(("trunk", "tertiary", "path", "steps", "service"), 1)
    ]
    elements += [
        {"type": "way", "id": 10, "geometry": _ring(51.23, -3.83, small), "tags": {"landuse": "x"}},
        {"type": "way", "id": 11, "geometry": _ring(51.23, -3.83, big), "tags": {"landuse": "x"}},
        {
            "type": "way",
            "id": 12,
            "geometry": _ring(51.23, -3.83, small),
            "tags": {"natural": "water"},
        },
        {
            "type": "way",
            "id": 13,
            "geometry": _ring(51.23, -3.83, small),
            "tags": {"landuse": "x", "name:gd": "Loch"},
        },
        {
            "type": "relation",
            "id": 14,
            "members": [{"type": "way", "role": "outer", "geometry": _ring(51.23, -3.83, small)}],
            "tags": {"type": "multipolygon", "landuse": "x"},
        },
        {
            "type": "relation",
            "id": 15,
            "members": [{"type": "way", "role": "outer", "geometry": _ring(51.23, -3.83, big)}],
            "tags": {"type": "multipolygon", "landuse": "x"},
        },
    ]
    return {"version": 0.6, "elements": elements}


class TestScaleDrops:
    """`--drop-minor-roads` and `--min-area-m2` drop what a coarse card cannot paint."""

    def test_minor_roads_and_paths_go_and_a_trunk_road_stays(self, tmp_path: Path) -> None:
        """Tertiary, path, steps and service ways are dropped; the trunk road stays."""
        path = tmp_path / "overpass-x.json"
        path.write_text(json.dumps(_scale_payload()), encoding="utf-8")
        assert main(["--drop-minor-roads", str(path)]) == 0
        ids = [e["id"] for e in json.loads(path.read_text(encoding="utf-8"))["elements"]]
        assert ids[0] == 1
        assert not {2, 3, 4, 5} & set(ids)
        assert {10, 11, 12, 13, 14, 15} <= set(ids)

    def test_small_areas_go_unless_water_or_named(self) -> None:
        """Below the area limit a plain closed way and relation go; water and named ones stay."""
        out = trim_payload(_scale_payload(), min_area_m2=1000.0)
        ids = {e["id"] for e in out["elements"]}
        assert not {10, 14} & ids
        assert {1, 2, 11, 12, 13, 15} <= ids

    def test_no_option_keeps_everything(self) -> None:
        """Without the options the element count is unchanged."""
        assert len(trim_payload(_scale_payload())["elements"]) == 11

    def test_a_second_run_is_byte_identical(self, tmp_path: Path) -> None:
        """Trimming a dropped file again with the same options changes nothing."""
        path = tmp_path / "overpass-x.json"
        path.write_text(json.dumps(_scale_payload()), encoding="utf-8")
        args = ["--drop-minor-roads", "--min-area-m2", "1000", str(path)]
        main(args)
        first = path.read_bytes()
        main(args)
        assert path.read_bytes() == first
