"""The nib: it runs the hand's marks through the ink engine onto one RGBA plate.

Key types: `NibSurface`, what the nib writes on (the render canvas, the
display-to-render `scale`, the darkness under the plate and the paper's
granulation cell); `nib_plate`, which strokes marks onto it and writes the file;
`nib_brushes`, the brush per role and type size.

The plate is composited normally rather than multiplied, which is the whole
reason it is its own plate: the backing wash is the paper's own colour and
multiply can only darken. Everything on it is stroked through the same ink
engine as the roads and the rivers and gated on the same paper, so the
lettering is made of the painted ink and not printed over it. A broad nib held at
a fixed angle draws its full width across itself and almost nothing along
itself, so a glyph's width follows the angle between the stroke and the nib.

`nib_plate` builds its own `Sheet` from the paper group and the surface, in one
place. It does not decide what is written, where, or in which ink a class of
feature takes (the marks arrive with their ink), and it builds no dark grid:
the caller hands the grid as an array.

Invariants: the same marks, surface and groups write the same pixels; a mark
of fewer than two points is skipped; with nothing to draw no file is written.
"""

import math
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from pyntpot.ink.brush import Brush, brush_from_id
from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.io import save_rgba
from pyntpot.ink.noise import F32, blur, chamfer_distance
from pyntpot.ink.pad import InkPad
from pyntpot.ink.sheet import Canvas, Sheet, rgb
from pyntpot.ink.style import PaperStyle
from pyntpot.ink.wash import WashOptions, wash
from pyntpot.letters.setting import Mark
from pyntpot.letters.style import FaceStyle, NibGroups, NibStyle

#: How wide a mark of each role is drawn, as a multiple of the type size it
#: belongs to. The lettering sets the weight; every other mark is a shade
#: lighter than it, so the line recedes behind the name.
MARK_WEIGHT = {
    "glyph": 1.0,
    "leader": 0.72,
    "span": 0.9,
    "tick": 0.9,
    "underline": 0.66,
    "pin": 1.5,
}

#: A colour a mark may name directly, as opposed to one of the four ink tokens.
_HEX = re.compile(r"#[0-9a-fA-F]{6}")

#: Points a stroke's width profile is sampled at.
_PROFILE_SAMPLES = 24

#: The fewest points a stroke can be run along: it needs two ends.
_STROKE_ENDS = 2

#: A stroke shorter than this, in render pixels, has no direction to take a width from.
_MIN_LENGTH_PX = 1e-6

#: The ink density above which a pixel counts as covered by the nib.
_COVERED = 0.12


@dataclass(frozen=True, eq=False)
class NibSurface:
    """What the nib writes on.

    Attributes:
        canvas: The render grid; only its `w` and `h` are read.
        scale: The display-to-render factor every mark is multiplied by.
        dark: How dark the ground is under each pixel, an `h` by `w` float
            array in [0, 1].
        gran_px: The paper granulation's cell size, in render pixels.
    """

    canvas: Canvas
    scale: float
    dark: np.ndarray
    gran_px: float


def nib_brushes(
    nib: NibStyle, face: FaceStyle, brush: BrushStyle, scale: float
) -> Callable[[str, float], Brush]:
    """A brush per role and type size, made once and kept.

    A nib rather than a brush, and with the route's own set-down turned right
    down: `MAJ6-e` lays a blot at the start of every stroke, which is character
    on a lane and a blob on the crossbar of a `t`.

    Args:
        nib: The nib style, for the brushes and their widths.
        face: The face style; when its `label_route` is `outline` the glyph
            nib is narrowed by `label_outline_width_frac`.
        brush: The brush style the sheet cells are read with.
        scale: Render pixels per display pixel.

    Returns:
        `brush(role, size)`, the brush for one mark.
    """
    made: dict[tuple[str, int], Brush] = {}

    def make(role: str, size: float) -> Brush:
        """The brush for one role at one type size."""
        key = (role, round(size * 4))
        got = made.get(key)
        if got is not None:
            return got
        pen = role == "glyph"
        wid = nib.label_pen_width_px if pen else nib.label_leader_width_px
        if pen and face.label_route == "outline":
            wid *= nib.label_outline_width_frac
        wid = wid * max(size, 1.0) / max(nib.label_size_px, 1e-6)
        made[key], _hex = brush_from_id(
            nib.label_brush if pen else nib.label_leader_brush,
            wid * MARK_WEIGHT.get(role, 1.0),
            scale,
            brush,
            "label",
        )
        b = made[key]
        b.pool *= 0.22
        b.load *= 0.55
        b.wobble *= 0.30
        b.jitter *= 0.55
        b.lift = min(b.lift, b.width * 1.6)
        b.smooth = max(b.smooth, b.width * 0.5)
        return b

    return make


def _pen_profile(
    pts: np.ndarray, angle: float, thin: float, samples: int = _PROFILE_SAMPLES
) -> np.ndarray:
    """A width along one stroke, from the angle between it and the nib.

    A broad nib held at a fixed angle draws its full width across itself and
    almost nothing along itself. That single fact is most of what separates a
    written letter from a plotted one, and it is why the same skeleton stamped
    at one width reads as a machine.

    Args:
        pts: The stroke in render pixels.
        angle: The nib's angle in radians from the page's horizontal, in
            render pixels with y down.
        thin: How much of the width a stroke drawn straight along the nib loses.
        samples: How many points the profile is sampled at.

    Returns:
        The multiplier at evenly spaced points from the stroke's start to end.
    """
    if len(pts) < _STROKE_ENDS:
        return np.ones(_STROKE_ENDS, F32)
    d = np.diff(pts, axis=0)
    seg = np.hypot(d[:, 0], d[:, 1])
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    if cum[-1] <= _MIN_LENGTH_PX:
        return np.ones(_STROKE_ENDS, F32)
    at = np.linspace(0.0, cum[-1], samples)
    mid = np.clip(np.searchsorted(cum, at) - 1, 0, len(seg) - 1)
    theta = np.arctan2(d[mid, 1], d[mid, 0])
    across = np.abs(np.sin(theta - angle))
    return ((1.0 - thin) + thin * across).astype(F32)


def _sheet(surface: NibSurface, paper: PaperStyle) -> Sheet:
    """The paper the nib's ink is gated on, at the surface's own size."""
    rw, rh = surface.canvas.w, surface.canvas.h
    return Sheet(
        rh,
        rw,
        gran_px=surface.gran_px,
        seed=paper.sheet_seed,
        fibre=paper.paper_fibre_mix if paper.paper_fibre else 0.0,
        fibre_stretch=paper.paper_fibre_stretch,
        fibre_angle=paper.paper_fibre_angle,
        fibre_cell=max(paper.paper_fibre_cell_px * rw / 1800.0, 1.6),
    )


def _backing_wash(
    cover: np.ndarray,
    surface: NibSurface,
    sheet: Sheet,
    groups: NibGroups,
) -> tuple[np.ndarray, np.ndarray]:
    """A faint lift of paper under a word block, through the wash machinery.

    Not a halo: a halo is an outline offset from the glyphs and it reads as a
    sticker cut round the letters. This is one soft blob a word, granulated on
    the paper's own pits with a pooled rim, and it is absent where the ground
    is already pale enough to read on, so it says "the paint was lifted before
    this was written" rather than sitting under every name on the plate.

    Args:
        cover: The ink density of the marks that asked for the wash.
        surface: What the nib writes on; its darkness gates the wash.
        sheet: The paper.
        groups: The style groups the nib reads.

    Returns:
        The wash's colour and its alpha, ready to composite under the ink.
    """
    nib, paper = groups.nib, groups.paper
    reach = max(nib.label_wash_spread * nib.label_size_px * surface.scale, 2.0)
    near = chamfer_distance(cover > _COVERED)
    blob = blur(np.clip(1.0 - near / reach, 0.0, 1.0), reach * 0.35)
    dens = wash(
        np.clip(blob * 1.6, 0.0, 1.0),
        sheet,
        0.85,
        0.3,
        WashOptions(
            rim_px=max(reach * 0.4, 3.0),
            gran=0.3,
            gran_gamma=paper.gran_gamma if paper.paper_fibre else 0.0,
        ),
    )
    floor = nib.label_wash_dark_floor
    gate = np.clip((surface.dark - floor) / max(1.0 - floor, 1e-3), 0.0, 1.0)
    alpha = np.clip(dens * gate * nib.label_wash_alpha, 0.0, 1.0)
    return np.broadcast_to(rgb(paper.paper_hex), (*cover.shape, 3)).copy(), alpha


Item = tuple[Brush, np.ndarray, np.ndarray | None, bool]


def _items(marks: Sequence[Mark], groups: NibGroups, scale: float) -> dict[str, list[Item]]:
    """The marks as render-pixel strokes with their brush and profile, grouped by ink."""
    nib = groups.nib
    brush = nib_brushes(nib, groups.face, groups.brush, scale)
    angle = math.radians(nib.label_pen_angle_deg)
    inks = {"map", "route", "water", "in_water"}
    found: dict[str, list[Item]] = {}
    for mark in marks:
        pts = np.asarray(mark.pts, np.float64) * scale
        if len(pts) < _STROKE_ENDS:
            continue
        prof = (
            _pen_profile(pts, angle + mark.pen, nib.label_pen_thin)
            if mark.role == "glyph"
            else None
        )
        # Four of the inks are the style's own and are named; a span carries a
        # fifth, resolved from its intent, and it arrives as the colour itself.
        # Anything else falls back to the label ink rather than writing a name
        # in a colour nobody chose.
        key = str(mark.ink)
        if key not in inks:
            key = key if _HEX.fullmatch(key) else "map"
        found.setdefault(key, []).append((brush(mark.role, mark.size), pts, prof, bool(mark.wash)))
    return found


def _ink_colour(key: str, nib: NibStyle) -> str:
    """The colour an ink token names, or the colour itself."""
    named = {
        "map": nib.label_ink,
        "route": nib.label_route_ink,
        "water": nib.label_water_ink,
        "in_water": nib.label_in_water_ink,
    }
    return named.get(key, key)


def nib_plate(
    marks: Sequence[Mark], surface: NibSurface, groups: NibGroups, path: Path
) -> Path | None:
    """Write the marks as one RGBA plate.

    Source: `nib` in docs/explanation/references.md.

    Args:
        marks: What to draw. Each carries `pts` in display pixels, a `role`
            naming its weight, an `ink` naming its colour, the type `size` it
            belongs to and the `pen` angle it was written with.
        surface: What the nib writes on.
        groups: The style groups the nib reads.
        path: Where to write.

    Returns:
        The file written, or None when there was nothing to draw.
    """
    if not marks:
        return None
    rw, rh = surface.canvas.w, surface.canvas.h
    sheet = _sheet(surface, groups.paper)
    found = _items(marks, groups, surface.scale)
    if not found:
        return None

    nib, paper, pad_style = groups.nib, groups.paper, groups.brush
    rng = np.random.default_rng(groups.hand.label_seed)
    layers: list[tuple[np.ndarray, np.ndarray]] = []
    cover = np.zeros((rh, rw), F32)
    dark = surface.dark
    # A name is written a shade darker where the paper is bare and a shade
    # lighter over a wood, which is the difference between printed on and
    # written on.
    tint = (1.0 + 0.20 * (dark - 0.35))[..., None]
    for ink, items in found.items():
        base = items[0][0]
        pad = InkPad((rh, rw), base, pad_style)
        pad.lay(
            [(b, line) for b, line, _p, _w in items],
            rng,
            profiles=[prof for _b, _l, prof, _w in items],
        )
        dens = pad.read(base, sheet)
        # Only the marks that asked for one are under the backing wash. A name
        # written on its own water is not: the wash exists to make a name
        # readable on ground it was not meant to be on.
        if any(w for _b, _l, _p, w in items):
            if all(w for _b, _l, _p, w in items):
                cover = np.maximum(cover, dens)
            else:
                keep = InkPad((rh, rw), base, pad_style)
                keep.lay(
                    [(b, line) for b, line, _p, w in items if w],
                    rng,
                    profiles=[prof for _b, _l, prof, w in items if w],
                )
                cover = np.maximum(cover, keep.read(base, sheet))
        colour = rgb(_ink_colour(ink, nib))[None, None, :] * tint
        layers.append((np.clip(colour, 0.0, 1.0), np.clip(dens, 0.0, 1.0)))

    out_rgb = np.zeros((rh, rw, 3), F32)
    out_a = np.zeros((rh, rw), F32)
    if nib.label_wash:
        layers.insert(0, _backing_wash(cover, surface, sheet, groups))
    for src_rgb, src_a in layers:
        a = np.clip(src_a, 0.0, 1.0)[..., None]
        keep = out_a[..., None] * (1.0 - a)
        total = np.maximum(a + keep, 1e-6)
        out_rgb = (src_rgb * a + out_rgb * keep) / total
        out_a = np.clip(a[..., 0] + out_a * (1.0 - a[..., 0]), 0.0, 1.0)

    save_rgba(out_rgb, out_a, path, paper.paper_quality, lossless=paper.plate_lossless)
    return path
