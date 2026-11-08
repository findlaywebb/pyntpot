"""The pen route draws a retraced leg as one line, the line the strands draw."""

import dataclasses

import numpy as np
from PIL import Image

from pyntpot.maps import paint
from pyntpot.maps.painter.job import PlateStack
from pyntpot.maps.painter.pen import paint_route_pen
from pyntpot.maps.strands import STRAND_MERGE_WIDTHS, strand_merge_px
from pyntpot.maps.style import Style

from .jobs import tiny_job

#: An out-and-back along one street, 300 m each way: 150 render pixels a leg.
OUT = [(float(x), 120.0) for x in range(10, 310, 4)]
OUT_AND_BACK = tuple(OUT + OUT[::-1])
#: The column of the card, in render pixels, well clear of both ends of the legs.
MID_COLUMN = 60


def _inked_as(style: Style, drawn_as: str) -> Style:
    """The style with its route ink drawn in this treatment."""
    ink = dataclasses.replace(style.route_ink, drawn_as=drawn_as)
    return style.model_copy(update={"route_ink": ink})


def _runs(alpha: np.ndarray) -> list[float]:
    """The centre row of each inked run in one column of alpha."""
    inked = alpha > alpha.max() / 2
    runs: list[float] = []
    start = None
    for row, on in enumerate([*inked, False]):
        if on and start is None:
            start = row
        elif not on and start is not None:
            runs.append((start + row - 1) / 2)
            start = None
    return runs


def _pen_column(directory, column: int = MID_COLUMN) -> list[float]:
    """The inked runs down one column of the painted pen plate."""
    alpha = np.asarray(Image.open(directory / "pen.webp").convert("RGBA"))[..., 3]
    return _runs(alpha[:, column].astype(float))


def test_an_out_and_back_gives_a_pen_plate_with_one_line(tmp_path):
    """A column across both legs of an out-and-back crosses one inked run, not two."""
    job = tiny_job(tmp_path, route=OUT_AND_BACK)
    paint_route_pen(job, PlateStack.blank(job.shape))
    assert len(_pen_column(tmp_path)) == 1


def test_a_pen_route_ink_draws_strands_on_the_pens_line(tmp_path):
    """With a pen route ink, both passes run within a pixel of the one inked run's centre."""
    style = _inked_as(Style.default(), "pen")
    job = tiny_job(tmp_path / "job", style, route=OUT_AND_BACK)
    plates = paint(job.basemap, style, tmp_path / "plates")
    k = job.scale
    rows = sorted(y * k for x, y in plates.strands if abs(x * k - MID_COLUMN) <= 1.0)
    runs = _pen_column(tmp_path / "plates")
    assert len(runs) == 1
    for row in (rows[0], rows[-1]):
        assert min(abs(row - r) for r in runs) <= 1.0


def test_the_pen_reach_is_the_pens_and_the_solid_reach_is_the_inks():
    """The merge reach follows the pen's width for a pen route ink and the ink's for any other."""
    style = Style.default()
    assert strand_merge_px(style) == style.route_ink.px * STRAND_MERGE_WIDTHS
    pen = _inked_as(style, "pen")
    assert strand_merge_px(pen) == style.route.route_pen_width_px * STRAND_MERGE_WIDTHS
    no_pen = pen.model_copy(update={"route": dataclasses.replace(pen.route, route_pen=False)})
    assert strand_merge_px(no_pen) == style.route_ink.px * STRAND_MERGE_WIDTHS


def test_solid_and_pen_route_inks_paint_the_same_pen_plate(tmp_path):
    """The route ink is not a base field: two styles with the same base groups paint one pen plate."""
    solid = tiny_job(tmp_path / "solid", _inked_as(Style.default(), "solid"), route=OUT_AND_BACK)
    pen = tiny_job(tmp_path / "pen", _inked_as(Style.default(), "pen"), route=OUT_AND_BACK)
    for job in (solid, pen):
        paint_route_pen(job, PlateStack.blank(job.shape))
    assert (tmp_path / "solid" / "pen.webp").read_bytes() == (
        tmp_path / "pen" / "pen.webp"
    ).read_bytes()
