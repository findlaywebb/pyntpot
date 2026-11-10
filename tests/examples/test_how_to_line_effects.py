"""The line effects how-to paints the Ambleside fixture offline: its theme names presets, and each figure is one image."""

import numpy as np
import pytest
from golden.make_docs_images import fixture_options
from PIL import Image

from pyntpot.maps import Style
from pyntpot.maps.line_effects import BUILT_IN_PRESETS

from support import REPO_ROOT
from support.examples import run_example

FIGURES = ("card", "presets")
THEME = REPO_ROOT / "examples" / "themes" / "ambleside-cased.yaml"


class TestTheCasedTheme:
    """`ambleside-cased.yaml` extends Ambleside and sets two effects by preset name."""

    def test_it_cases_the_main_road_and_lifts_the_route(self) -> None:
        """The main road's stack is the `cased` preset and the route's is `lifted`, and no other class has one."""
        style = Style.from_yaml(THEME)

        assert style.basemap.line_effects == {"road_major": BUILT_IN_PRESETS["cased"]}
        assert style.route_ink.effects == BUILT_IN_PRESETS["lifted"]

    def test_it_moves_the_full_digest_and_not_the_lettering_digest(self) -> None:
        """Against ambleside.yaml the full digest moves and the lettering digest does not."""
        base = Style.from_yaml(THEME.with_name("ambleside.yaml"))
        cased = Style.from_yaml(THEME)

        assert cased.digest() != base.digest()
        assert cased.lettering_digest() == base.lettering_digest()


class TestFigures:
    """Each figure runs from a copy of the fixture's cache with no network and writes one PNG."""

    def test_an_unknown_figure_is_refused(self, tmp_path) -> None:
        """A figure the script does not have is a ValueError before any provider is read."""
        options = fixture_options("ambleside", tmp_path / "cache")
        with pytest.raises(ValueError, match="figure must be one of"):
            run_example("how_to_line_effects", tmp_path / "out", figure="nonesuch", **options)

    @pytest.mark.golden
    @pytest.mark.parametrize("figure", FIGURES, ids=FIGURES)
    def test_a_figure_is_one_image_that_is_not_flat(self, figure, tmp_path) -> None:
        """Each figure writes only its RGB PNG into the output directory, and it is not one flat colour."""
        options = fixture_options("ambleside", tmp_path / "cache")
        path = run_example("how_to_line_effects", tmp_path / "out", figure=figure, **options)

        assert list(path.parent.iterdir()) == [path]
        with Image.open(path) as image:
            assert image.mode == "RGB"
            pixels = np.asarray(image)
        assert (pixels.min(axis=(0, 1)) != pixels.max(axis=(0, 1))).all()
