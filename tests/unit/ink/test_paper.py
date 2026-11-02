"""Tests for the paper plate: the cream paper painted from the sheet alone."""

import dataclasses
import hashlib

import numpy as np

from pyntpot.ink import Canvas, Sheet
from pyntpot.ink.paper import paper_plate
from pyntpot.ink.style import PaperStyle


def _paper(style: PaperStyle, display_px: int = 90) -> np.ndarray:
    """The paper plate of a 90 by 60 canvas, painted on a fresh sheet."""
    return paper_plate(Sheet(60, 90, 4.0, 11), Canvas(0, 0, 90, 60, 90, 60), style, display_px)


class TestPaperPlate:
    """The paper plate."""

    def test_the_paper_is_the_canvas_size_and_inside_the_unit_range(self):
        """The paper is an RGB array of the canvas's shape, within 0 to 1."""
        paper = _paper(PaperStyle())
        assert paper.shape == (60, 90, 3)
        assert paper.min() >= 0.0 and paper.max() <= 1.0

    def test_the_border_is_worn_darker_than_the_middle(self):
        """The edge of the paper carries more wear than its centre."""
        paper = _paper(PaperStyle())
        assert paper[0, :, :].mean() < paper[25:35, 40:50].mean()

    def test_a_grid_darkens_the_paper_along_its_lines(self):
        """Turning the grid on makes the paper darker overall."""
        plain = _paper(dataclasses.replace(PaperStyle(), grid=False), 80)
        ruled = _paper(dataclasses.replace(PaperStyle(), grid=True), 80)
        assert ruled.mean() < plain.mean()


#: The sha-256 (first 16 hex digits) of the classic plate's float32 bytes on `_paper`'s sheet,
#: read from the code before the warm edge existed.
CLASSIC_PLATE_SHA = "ae150866b4642275"


def _classic() -> PaperStyle:
    """The classic paper: the grey vignette and the smudged foxing."""
    return PaperStyle(paper_edge="classic")


def _big(style: PaperStyle, gran_px: float = 3.0) -> np.ndarray:
    """The paper plate of a 360 by 240 canvas on a fresh sheet."""
    sheet = Sheet(240, 360, gran_px, 11)
    return paper_plate(sheet, Canvas(0, 0, 360, 240, 360, 240), style, 360)


def _speck_extents(mask: np.ndarray) -> list[int]:
    """The longer side of each 4-connected component's bounding box in `mask`."""
    seen = np.zeros_like(mask)
    extents = []
    for y, x in zip(*np.nonzero(mask), strict=True):
        if seen[y, x]:
            continue
        seen[y, x] = True
        stack, ys, xs = [(y, x)], [y], [x]
        while stack:
            cy, cx = stack.pop()
            for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                inside = 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1]
                if inside and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
                    ys.append(ny)
                    xs.append(nx)
        extents.append(int(max(max(ys) - min(ys), max(xs) - min(xs))) + 1)
    return extents


class TestClassicEdge:
    """`paper_edge="classic"` is the paper as it was."""

    def test_the_classic_plate_is_the_pinned_one(self):
        """The classic plate on a small seeded sheet hashes to the literal read before the edit."""
        plate = _paper(_classic())
        assert hashlib.sha256(np.ascontiguousarray(plate).tobytes()).hexdigest()[:16] == (
            CLASSIC_PLATE_SHA
        )

    def test_both_edges_leave_the_generator_in_the_same_state(self):
        """After either edge the sheet's next noise draw is the same field."""
        after = []
        for edge in ("classic", "warm"):
            sheet = Sheet(60, 90, 4.0, 11)
            paper_plate(sheet, Canvas(0, 0, 90, 60, 90, 60), PaperStyle(paper_edge=edge), 90)
            after.append(sheet.noise(26.0, 2))
        assert np.array_equal(after[0], after[1])


class TestWarmEdge:
    """`paper_edge="warm"`: a narrow brown edge and rust specks."""

    def test_warm_is_the_default(self):
        """A paper style that names no edge is the warm one."""
        assert PaperStyle().paper_edge == "warm"

    def test_with_no_wear_no_vignette_and_no_foxing_the_edges_agree(self):
        """Without the three things that differ, the draws and the tooth are the same."""
        bare = PaperStyle(paper_worn=0.0, paper_vignette=0.0, paper_foxing=0.0)
        warm = _big(dataclasses.replace(bare, paper_edge="warm"))
        classic = _big(dataclasses.replace(bare, paper_edge="classic"))
        assert np.abs(warm - classic).max() < 1e-6

    def test_the_edge_browns_rather_than_greys(self):
        """Red over blue is greater at the edge than at the centre."""
        plate = _big(PaperStyle(paper_tooth=0.0, paper_foxing=0.0))
        edge, centre = plate[120, 0:2].mean(0), plate[120, 180]
        assert edge[0] / edge[2] > centre[0] / centre[2]

    def test_the_edge_is_narrow(self):
        """A tenth of the width in, the darkening is within 2% of the centre's value."""
        plate = _big(PaperStyle(paper_tooth=0.0, paper_foxing=0.0))
        assert np.abs(plate[120, 36] / plate[120, 180] - 1.0).max() < 0.02

    def test_a_speck_is_rustier_than_the_paper_beside_it(self):
        """Red over blue at a foxed pixel exceeds the paper's."""
        clean = _big(PaperStyle(paper_tooth=0.0, paper_foxing=0.0))
        foxed = _big(PaperStyle(paper_tooth=0.0))
        hit = np.abs(foxed - clean).max(axis=2) > 0
        assert hit.any()
        assert (foxed[hit, 0] / foxed[hit, 2] > clean[hit, 0] / clean[hit, 2]).all()

    def test_the_specks_are_few_and_no_wider_than_twice_the_grain(self):
        """On a 360 by 240 sheet at grain 3 the foxed pixels are under 1% and each speck is 6 or less."""
        clean = _big(PaperStyle(paper_foxing=0.0))
        hit = np.abs(_big(PaperStyle()) - clean).max(axis=2) > 0
        assert 0.0 < hit.mean() < 0.01
        assert max(_speck_extents(hit)) <= 2 * 3.0

    def test_the_share_of_foxed_paper_does_not_follow_the_grain(self):
        """A coarser grain touches the same share of the sheet."""
        shares = []
        for gran_px in (3.0, 8.0):
            clean = _big(PaperStyle(paper_foxing=0.0), gran_px)
            shares.append((np.abs(_big(PaperStyle(), gran_px) - clean).max(axis=2) > 0).mean())
        assert abs(shares[0] - shares[1]) < 0.001
