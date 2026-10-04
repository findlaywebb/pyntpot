"""The ink pad: one class's strokes laid, saturated, gated on the paper and read back.

Key names: `InkPad`, one class's accumulator on the plate's grid or a finer one, with `lay` to
stamp strokes into it and `read` to get density back; `ink_density`, which turns an
accumulator into ink by saturating, gating on the paper and bleeding the edge; `_bleed`, the
mark's soft edge; `_grow` and `_reduce`, carrying a field up to a finer grid and a plane
back down.

It builds no brush and draws no bristle: strokes go through `pyntpot.ink.stamp`. It reads the
`BrushStyle` for the grid and the joining only.

Invariants: at a supersample of 1 the pad is the plate's own accumulator and every call is
the call it was; the density is clipped to 0 to 1.
"""

import numpy as np
from PIL import Image

from pyntpot.ink.brush import Brush, ink_aux, scaled_brush
from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.chains import chain_lines
from pyntpot.ink.noise import F32, blur
from pyntpot.ink.sheet import Sheet
from pyntpot.ink.stamp import stamp

#: Blur radius, in render pixels, at or under which a mark has no soft edge to wick.
_MIN_BLEED_PX = 0.4


def ink_density(
    acc: np.ndarray,
    b: Brush,
    sheet: Sheet,
    aux: dict[str, np.ndarray] | None = None,
    paper: np.ndarray | None = None,
    *,
    bleed: bool = True,
) -> np.ndarray:
    """Turn an accumulator into ink: saturate, gate on the paper, then bleed.

    Saturating with 1 - exp(-acc) is what stops a crossing from doubling: two
    strokes over each other reach the same black as one heavy one.

    The gate is where the reservoir and the directional break land, rather than
    inside `stamp`: a per-sample gate is diluted by the splat and then by the
    saturation, and what comes out is a mark that is evenly thinner instead of
    one that breaks.

    Args:
        acc: The ink accumulator.
        b: The brush.
        sheet: The paper's noise fields.
        aux: The accumulators `stamp` filled alongside the ink, when the brush
            asked for them.
        paper: The paper's own height on the accumulator's grid, when the ink
            is painted on a finer grid than the sheet. `sheet.paper` when it is
            not given, which is every caller that paints on the plate itself.
        bleed: Whether to wick the mark's edge out here. Off when the ink is
            painted on a finer grid: the bleed is a blur, a blur costs the same
            whatever its radius, and doing it after the reduce is cheaper by
            the square of the grid and no different to look at.

    Returns:
        Density in 0 to 1.
    """
    if not acc.any():
        return np.zeros_like(acc)
    pap = sheet.paper if paper is None else paper
    dens = 1.0 - np.exp(-acc)
    if aux is None:
        gate = 1.0 - b.dry * (1.0 - np.clip((pap - b.thr) * 5.5 + 0.5, 0, 1))
    else:
        safe = np.maximum(acc, F32(1e-6))
        tooth = pap
        if "tooth" in aux:
            # Matched to the paper's own mean and spread under the mark, so the
            # flag swaps the direction of the break and nothing else: a texture
            # with more contrast than the paper would gate less often and come
            # out darker, which is not what the flag is for. `dir_gain` above 1
            # is then an honest ask for a harsher tooth than the paper's.
            here = acc > 0
            r = aux["tooth"] / safe
            src, dst = r[here], pap[here]
            k = b.dir_gain * float(dst.std()) / max(float(src.std()), 1e-4)
            streak = np.clip((r - float(src.mean())) * k + float(dst.mean()), 0.0, 1.0)
            tooth = pap * (1.0 - b.dir_mix) + streak * b.dir_mix
        thr, dry, slope = b.thr, b.dry, 5.5
        if "res" in aux:
            # A harder gate, so an empty brush skips rather than fades. It comes
            # with the reservoir, which is what raises the threshold under it.
            slope = 8.0
            # How wet the brush was where each pixel was laid down. An empty
            # brush needs higher paper to make a mark, so the gate tightens
            # along the stroke rather than breaking the whole mark at once.
            spent = 1.0 - np.clip(aux["res"] / safe, 0.0, 1.0)
            thr = np.minimum(b.thr + 0.20 * spent, 0.72)
            dry = np.minimum(b.dry * (0.85 + 0.5 * spent), 1.0)
        gate = 1.0 - dry * (1.0 - np.clip((tooth - thr) * slope + 0.5, 0, 1))
    dens = dens * gate
    if bleed:
        dens = _bleed(dens, b)
    return np.clip(dens, 0.0, 1.0)


def _bleed(dens: np.ndarray, b: Brush) -> np.ndarray:
    """The mark's soft edge: what the paper wicks out past the bristles."""
    if b.bleed <= _MIN_BLEED_PX:
        return dens
    return np.clip(np.maximum(dens, blur(dens, b.bleed) * 1.35), 0, 1)


def _grow(a: np.ndarray, h: int, w: int) -> np.ndarray:
    """One smooth field carried up to a finer grid, bilinear."""
    img = Image.fromarray(np.asarray(a, F32), "F").resize((w, h), Image.Resampling.BILINEAR)
    return np.asarray(img, F32)


def _reduce(a: np.ndarray, h: int, w: int) -> np.ndarray:
    """One plane Lanczos-reduced to the plate's own grid.

    Lanczos rather than an area mean because the mark's edge is what is being
    saved: an area mean is a box filter and leaves the stair it was asked to
    remove. It overshoots a hard edge slightly, which is why the result is
    clipped back into range.
    """
    if a.shape == (h, w):
        return np.asarray(a, F32)
    img = Image.fromarray(np.asarray(a, F32), "F").resize((w, h), Image.Resampling.LANCZOS)
    return np.clip(np.asarray(img, F32), 0.0, 1.0)


class InkPad:
    """One class's ink, painted on the plate's grid or on a finer one.

    The plate is written at `supersample` times the display size and shown at
    up to one render pixel per device pixel, so the ink's own grid is what the
    eye reads as pixelation: a lane is under four render pixels wide and its
    splat lands on a visible stair. `ink_ss` paints the whole ink pipeline, the
    saturation and the paper gate included, on a grid that many times finer and
    Lanczos-reduces the density back. Doing it after the gate rather than
    before is the point: the reduce then averages ink, which is what the eye
    does, instead of averaging deposits and gating the average.

    At `ink_ss` of 1 the pad is the plate's own accumulator and every call is
    the call it was.
    """

    def __init__(self, shape: tuple[int, int], b: Brush, style: BrushStyle) -> None:
        """Open an accumulator for one class.

        Args:
            shape: The plate's pixel shape.
            b: The brush the class is read back with, for the accumulators its
                flags need.
            style: The brush style, for the grid and the joining.
        """
        self.h, self.w = shape
        self.ss = max(int(style.ink_ss), 1)
        self.tol = style.ink_join_tol_px if style.ink_joins else 0.0
        self.acc = np.zeros((self.h * self.ss, self.w * self.ss), F32)
        self.aux = ink_aux(self.acc.shape, b)
        self._brushes: dict[int, Brush] = {}

    def _at(self, b: Brush) -> Brush:
        """This brush on the pad's own grid, made once per brush."""
        got = self._brushes.get(id(b))
        if got is None:
            got = self._brushes[id(b)] = scaled_brush(b, self.ss)
        return got

    def lay(
        self,
        items: list[tuple[Brush, np.ndarray]],
        rng: np.random.Generator,
        profiles: list[np.ndarray | None] | None = None,
    ) -> None:
        """Stamp a class's strokes.

        With joining off the strokes are stamped in the order they arrive, one
        polyline at a time, which is what the painter always did. With it on
        they are grouped by brush, in first-seen order, and the ways in each
        group are chained end to end first.

        Args:
            items: Brush and polyline per stroke, in render pixels.
            rng: The generator the bristle patterns are drawn from.
            profiles: A width profile per stroke, or None per stroke that wants
                none. Chaining is skipped when they are given: two strokes
                joined end to end are one stroke and their two profiles are
                not, and lettering does not want its glyphs chained anyway.
        """
        if profiles is not None:
            for (b, line), prof in zip(items, profiles, strict=True):
                stamp(
                    self.acc,
                    line * self.ss if self.ss > 1 else line,
                    self._at(b),
                    rng,
                    aux=self.aux,
                    wprof=prof,
                )
            return
        if self.tol <= 0:
            for b, line in items:
                stamp(
                    self.acc,
                    line * self.ss if self.ss > 1 else line,
                    self._at(b),
                    rng,
                    aux=self.aux,
                )
            return
        groups: dict[int, tuple[Brush, list[np.ndarray]]] = {}
        for b, line in items:
            groups.setdefault(id(b), (b, []))[1].append(line)
        for b, lines in groups.values():
            for line in chain_lines(lines, self.tol):
                stamp(
                    self.acc,
                    line * self.ss if self.ss > 1 else line,
                    self._at(b),
                    rng,
                    aux=self.aux,
                )

    def any(self) -> bool:
        """Whether anything was laid down."""
        return bool(self.acc.any())

    def read(self, b: Brush, sheet: Sheet) -> np.ndarray:
        """The class's density on the plate's own grid.

        Args:
            b: The brush the class is read back with.
            sheet: The paper's noise fields, on the plate's grid.

        Returns:
            Density in 0 to 1, `(plate h, plate w)`.
        """
        if self.ss == 1:
            return ink_density(self.acc, b, sheet, self.aux)
        paper = _grow(sheet.paper, *self.acc.shape)
        dens = ink_density(self.acc, self._at(b), sheet, self.aux, paper, bleed=False)
        return _bleed(_reduce(dens, self.h, self.w), b)


# --------------------------------------------------------------------------- ribbon
