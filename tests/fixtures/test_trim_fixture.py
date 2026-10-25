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
