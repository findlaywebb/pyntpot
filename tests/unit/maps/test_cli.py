"""`pyntpot map` runs offline over the fixture cache and composes the golden map.

These tests import `pyntpot.maps.cli`, which needs `letter` from `pyntpot.maps.lettering.pipeline`
and `compose` from `pyntpot.maps.pipeline`; every test here waits on the slice that adds them.
"""

import shutil
from pathlib import Path

import pytest
from PIL import Image

from pyntpot.maps.cli import main

from support.golden import differing_fraction
from support.paths import FIXTURE_DIR, GOLDEN_DIR

MAX_DIFFERING_FRACTION = 0.005
MAX_CHANNEL_DELTA = 2


def _snapshot(directory: Path) -> dict[str, int]:
    """Return each payload file's name and `st_mtime_ns` in a directory."""
    return {path.name: path.stat().st_mtime_ns for path in sorted(directory.glob("*.json"))}


def _run(cache: Path, out: Path, *options: str) -> int:
    """Run `pyntpot map` over the fixture track and a cache, without attribution, with `options`."""
    argv = [
        "map",
        str(FIXTURE_DIR / "track.gpx"),
        "--cache",
        str(cache),
        "--contact",
        "test",
        "--no-attribution",
        "-o",
        str(out),
        *options,
    ]
    return main(argv)


class TestMap:
    """The `map` subcommand over a copy of the fixture cache."""

    @pytest.mark.golden
    def test_a_full_cache_makes_no_request(self, tmp_path: Path) -> None:
        """The command succeeds and leaves every cached payload untouched."""
        cache = tmp_path / "cache"
        shutil.copytree(FIXTURE_DIR, cache)
        before = _snapshot(cache)
        assert _run(cache, tmp_path / "out.png") == 0
        assert _snapshot(cache) == before
        assert sorted(path.name for path in cache.glob("*.json")) == sorted(before)
        assert (tmp_path / "out.png").is_file()

    def test_a_small_display_style_paints_a_map_quickly(self, tmp_path: Path) -> None:
        """`--style` with a theme naming only a 120-pixel display writes a 240-pixel-wide PNG."""
        style = tmp_path / "small.yaml"
        style.write_text("card:\n  display_px: 120\n", encoding="utf-8")
        cache = tmp_path / "cache"
        shutil.copytree(FIXTURE_DIR, cache)
        out = tmp_path / "out.png"
        argv = ["map", str(FIXTURE_DIR / "track.gpx"), "--cache", str(cache), "--contact", "t"]
        argv += ["--style", str(style), "--no-attribution", "-o", str(out)]
        assert main(argv) == 0
        with Image.open(out) as image:
            assert image.width == 240

    @pytest.mark.golden
    def test_a_named_style_paints_a_map(self, tmp_path: Path) -> None:
        """`--style sepia` paints the map in the packaged sepia theme and writes the PNG."""
        cache = tmp_path / "cache"
        shutil.copytree(FIXTURE_DIR, cache)
        out = tmp_path / "out.png"
        assert _run(cache, out, "--style", "sepia") == 0
        assert out.is_file()

    def test_a_small_theme_extending_a_name_paints_quickly(self, tmp_path: Path) -> None:
        """`--style` with a theme extending `sepia` at a 120-pixel display writes a 240-pixel PNG."""
        style = tmp_path / "small.yaml"
        style.write_text("extends: sepia\ncard:\n  display_px: 120\n", encoding="utf-8")
        cache = tmp_path / "cache"
        shutil.copytree(FIXTURE_DIR, cache)
        out = tmp_path / "out.png"
        assert _run(cache, out, "--style", str(style)) == 0
        with Image.open(out) as image:
            assert image.width == 240

    def test_an_unknown_style_name_exits_2_with_the_names(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """`--style missing` exits with status 2 and logs the available theme names."""
        assert _run(tmp_path / "cache", tmp_path / "out.png", "--style", "missing") == 2
        assert "pyntpot map: " in caplog.text
        assert "available: bold, default, pen-and-ink, sepia, winter" in caplog.text
        assert not (tmp_path / "out.png").exists()

    def test_a_toml_style_exits_2_with_the_adr_pointer(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """`--style old.toml` exits with status 2 and logs the pointer to ADR 0069."""
        assert _run(tmp_path / "cache", tmp_path / "out.png", "--style", "old.toml") == 2
        assert "themes are YAML since ADR 0069" in caplog.text

    @pytest.mark.golden
    def test_the_png_matches_the_golden_map(self, tmp_path: Path) -> None:
        """The composed PNG is within the pixel bound of the golden map."""
        cache = tmp_path / "cache"
        shutil.copytree(FIXTURE_DIR, cache)
        _run(cache, tmp_path / "out.png")
        fraction = differing_fraction(
            tmp_path / "out.png", GOLDEN_DIR / "map.png", MAX_CHANNEL_DELTA
        )
        assert fraction <= MAX_DIFFERING_FRACTION

    @pytest.mark.parametrize(
        "missing", ["--contact", "--cache", "-o"], ids=["contact", "cache", "output"]
    )
    def test_a_missing_required_option_exits_2(self, tmp_path: Path, missing: str) -> None:
        """Leaving out a required option exits with status 2."""
        argv = ["map", str(FIXTURE_DIR / "track.gpx"), "--cache", str(tmp_path), "--contact", "t"]
        argv += ["-o", str(tmp_path / "o.png")]
        index = argv.index(missing)
        del argv[index : index + 2]
        with pytest.raises(SystemExit) as raised:
            main(argv)
        assert raised.value.code == 2
