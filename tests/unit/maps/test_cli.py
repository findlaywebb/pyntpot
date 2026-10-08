"""`pyntpot map` runs offline over the fixture cache and composes the golden map.

These tests import `pyntpot.maps.cli`, which needs `letter` from `pyntpot.maps.lettering.pipeline`
and `compose` from `pyntpot.maps.pipeline`; every test here waits on the slice that adds them.
"""

import shutil
from importlib import resources
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


def _run(cache: Path, out: Path) -> int:
    """Run `pyntpot map` over the fixture track and a cache, without attribution."""
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
        """`--style` with a 120-pixel copy of the default theme writes a 240-pixel-wide PNG."""
        theme = resources.files("pyntpot.maps").joinpath("themes/default.toml").read_text("utf-8")
        assert "display_px = 900" in theme
        style = tmp_path / "small.toml"
        style.write_text(theme.replace("display_px = 900", "display_px = 120"), encoding="utf-8")
        cache = tmp_path / "cache"
        shutil.copytree(FIXTURE_DIR, cache)
        out = tmp_path / "out.png"
        argv = ["map", str(FIXTURE_DIR / "track.gpx"), "--cache", str(cache), "--contact", "t"]
        argv += ["--style", str(style), "--no-attribution", "-o", str(out)]
        assert main(argv) == 0
        with Image.open(out) as image:
            assert image.width == 240

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
