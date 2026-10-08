"""The plates phase: every phase run in order, the plates and the manifest written."""

import json

from pyntpot.maps.painter.plates import paint_plates

from .jobs import tiny_job


def test_a_tiny_card_writes_three_plates_and_a_manifest_that_names_them(tmp_path):
    """Card, wash and route pen land on disk, and the manifest on disk matches the result."""
    job = tiny_job(tmp_path / "plates")
    plates = paint_plates(job.basemap, job.style, tmp_path / "plates")
    written = json.loads((tmp_path / "plates" / "plates.json").read_text())
    assert set(plates.manifest.files) == {"paper", "wash", "pen"}
    assert set(written["files"]) == {"paper", "wash", "pen"}
    assert plates.manifest.bytes == sum(plates.manifest.sizes.values())


def test_the_dark_grid_has_the_cells_the_style_asks_for(tmp_path):
    """The manifest's dark grid is `dark_grid` cells wide and high, each in 0 to 1."""
    job = tiny_job(tmp_path / "plates")
    manifest = paint_plates(job.basemap, job.style, tmp_path / "plates").manifest
    gw, gh = job.style.card.dark_grid
    assert (manifest.dark.w, manifest.dark.h) == (gw, gh)
    assert len(manifest.dark.values) == gh
    assert all(0.0 <= v <= 1.0 for row in manifest.dark.values for v in row)
