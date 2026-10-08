"""The brush: the tool a stroke is stamped with, and the brush sheet it is read from.

Key types: `Brush`, one mark-making tool in render pixels; `brush_from_id`, which builds one
from a brush sheet cell and the `BrushStyle`; `scaled_brush`, the same tool on a finer grid;
`ink_aux`, the extra accumulators a brush's flags need. The brush-sheet catalogue is here as
well: `BRUSH_TREATMENTS`, keyed by sheet row `"1"` to `"8"`; `PEN_ROWS`, the rows that are a
nib; and `BRUSH_COLOURS`, keyed by the id's three-letter prefix and then the colour column.

A brush id `<PREFIX><row>-<column>`, such as `MAJ2-a`, is an opaque sheet cell name: this
module never reads the prefix as a feature class. Which class takes which cell is the style's
`brushes` field. It stamps nothing and reads no paper.

Invariants: a brush id naming a row or colour the sheet lacks raises `ValueError`; the
reservoir, directional break and quality flags are inert at their defaults.
"""

from dataclasses import dataclass, replace

import numpy as np

from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.noise import F32

#: The stroke treatment of each sheet row. A brush id is a prefix, a row and a
#: colour column: `MAJ2-a` is treatment 2, colour a. Widths live in `BrushStyle`,
#: because one treatment is drawn at a river's width on one plate, a lane's on another.
BRUSH_TREATMENTS: dict[str, dict[str, float]] = {
    "1": {
        "name_wet": 1.0,
        "darkness": 1.8,
        "bristles": 26,
        "gap": 0.03,
        "dry": 0.15,
        "thr": 0.34,
        "texture": 0.32,
        "press": 0.14,
        "load": 0.6,
        "pool": 0.0,
        "bleed": 1.5,
        "lift": 34,
    },
    "2": {
        "darkness": 2.0,
        "bristles": 22,
        "gap": 0.09,
        "dry": 0.30,
        "thr": 0.38,
        "texture": 0.42,
        "press": 0.20,
        "load": 0.55,
        "pool": 0.0,
        "bleed": 1.1,
        "lift": 30,
    },
    "3": {
        "darkness": 2.4,
        "bristles": 16,
        "gap": 0.14,
        "dry": 0.42,
        "thr": 0.42,
        "texture": 0.55,
        "press": 0.26,
        "load": 0.5,
        "pool": 0.0,
        "bleed": 0.9,
        "lift": 26,
    },
    "4": {
        "darkness": 4.8,
        "bristles": 18,
        "gap": 0.28,
        "dry": 0.72,
        "thr": 0.48,
        "texture": 0.82,
        "press": 0.34,
        "load": 0.7,
        "pool": 0.0,
        "bleed": 0.5,
        "lift": 28,
    },
    "5": {
        "darkness": 7.2,
        "bristles": 5,
        "gap": 0.04,
        "dry": 0.22,
        "thr": 0.40,
        "texture": 0.40,
        "press": 0.18,
        "load": 1.6,
        "pool": 1.4,
        "bleed": 0.3,
        "lift": 12,
    },
    "6": {
        "darkness": 6.0,
        "bristles": 6,
        "gap": 0.0,
        "dry": 0.10,
        "thr": 0.32,
        "texture": 0.16,
        "press": 0.10,
        "load": 0.5,
        "pool": 0.9,
        "bleed": 0.45,
        "lift": 16,
        "solid": 0.75,
    },
    "7": {
        "darkness": 7.4,
        "bristles": 8,
        "gap": 0.44,
        "dry": 0.82,
        "thr": 0.53,
        "texture": 0.86,
        "press": 0.45,
        "load": 0.4,
        "pool": 0.0,
        "bleed": 0.35,
        "lift": 14,
    },
    "8": {
        "darkness": 6.4,
        "bristles": 4,
        "gap": 0.02,
        "dry": 0.20,
        "thr": 0.40,
        "texture": 0.36,
        "press": 0.14,
        "load": 1.2,
        "pool": 0.8,
        "bleed": 0.25,
        "lift": 14,
    },
}
#: The treatment rows that are a nib rather than a brush: a flat core, a
#: touch-down blot, and a line that thins rather than breaking when it runs low.
PEN_ROWS = frozenset({"5", "6", "8"})

#: The colour column of a brush id, per three-letter prefix.
BRUSH_COLOURS: dict[str, dict[str, str]] = {
    "RIV": {"a": "#255d80"},
    "STR": {"a": "#255d80"},
    "MAJ": {"a": "#b5623f", "b": "#8a5a2c", "c": "#6b4423", "d": "#7b7266", "e": "#2b2620"},
    "LAN": {"a": "#6b4423"},
    "TRK": {
        "a": "#6b4423",
        "b": "#b5623f",
        "c": "#7d7468",
        "d": "#6f6636",
        "e": "#95584a",
        "f": "#2b2620",
    },
}


@dataclass
class Brush:
    """One mark-making tool, in render pixels.

    A stroke is a brush tip stamped along the path. The tip is a row of
    bristles: a one dimensional profile of weights with gaps in it, each
    bristle drifting slowly sideways as the stroke goes on, so the same
    bristles leave the same streaks the whole way down the mark. Pressure varies
    slowly and drives width and darkness together; the paper's own tooth gates
    the ink, so a dry brush breaks where the paper is low.
    """

    width: float  # full width of the tip at neutral pressure
    darkness: float  # ink laid per stamp
    bristles: int  # tines across the tip
    gap: float  # share of them missing
    dry: float  # 0 a loaded wet brush, 1 bone dry
    thr: float  # paper height at which a dry mark starts to break
    jitter: float  # how far a bristle wanders sideways
    press: float  # slow pressure variation
    press_cell: float  # pixels per pressure cycle
    wobble: float  # slow wander of the whole line, for a pen
    load: float  # extra ink where the brush is first set down
    pool: float  # a blot at the start, for a nib
    bleed: float  # blur radius of the soft edge
    lift: float  # pixels over which the stroke lifts to a point
    texture: float = 0.7  # how much the bristles show: 0 a flat band, 1 grain
    step: float = 0.40  # spacing of the stamps along the path
    profile_px: float = 0.55  # spacing the tip's profile is sampled at
    solid: float = 0.0  # a flat core under the bristles, for a loaded pen
    load_px: float = 0.0  # how fast the set-down ink runs out; 0 derives it
    pool_radius_frac: float = 0.5
    pool_gain: float = 1.9
    # --- the reservoir and the directional break. All inert at these defaults,
    # so a brush built without the flags is the plain stamped brush.
    starve: bool = False  # spend a per-bristle load along the stroke
    run_px: float = 0.0  # how far one load carries, in render pixels
    res_floor: float = 0.38  # what is left in a nominally empty bristle
    dip_px: float = 0.0  # distance between reloads; 0 is never reload
    knee: float = 0.62  # ink kept at empty, before the paper gate
    dir_dry: bool = False  # stretch the break texture along the stroke
    dir_elong: float = 5.0
    dir_cell: float = 7.0  # width of one break across the mark, in pixels
    dir_gain: float = 1.0  # 1 is the paper's own contrast, more is harsher
    dir_mix: float = 0.8
    pen: bool = False  # this treatment is a nib, not a brush
    pen_starve: bool = False  # the nib thins and lightens as it runs down
    pen_thin: float = 0.26
    # --- brush quality. Inert at these defaults, so a brush built without the
    # flags is the plain stamped brush.
    organic: bool = False  # drift and pressure from a lattice, not a sine
    org_oct: int = 4
    org_lac: float = 2.17
    org_mult: float = 0.5  # lattice cell, as a share of the sine's wavelength
    smooth: float = 0.0  # corner radius in render pixels; 0 leaves the path
    #: Pixels of the brush's own grid per render pixel. 1 is the plate itself;
    #: `scaled_brush` sets it when the ink is painted on a finer grid, so the
    #: wavelengths written into `stamp` stay the same lengths on the plate.
    unit: float = 1.0
    #: How far the tip's own weights are smoothed across the mark, in render
    #: pixels. 0 leaves the tip as it was.
    band_px: float = 0.0
    #: A multiplier on the tip's variation about its own mean weight.
    contrast: float = 1.0
    #: How much of its sideways drift a bristle shares with its neighbours, as
    #: a share of the tip. 0 draws every bristle's phase independently.
    coherence: float = 0.0


def brush_from_id(
    brush_id: str,
    width_display_px: float,
    scale: float,
    style: BrushStyle,
    override: str | None = None,
) -> tuple[Brush, str]:
    """One class's brush and ink colour, from a brush sheet id.

    Args:
        brush_id: A cell on the brush sheet, `RIV1-a` or `TRK4-d`.
        width_display_px: The width this class is painted at on screen.
        scale: Render pixels per display pixel.
        style: The brush style, for the shared geometry and the overrides.
        override: Key into `style.brush_overrides`; None reads the id's prefix, lower case.

    Returns:
        The brush in render pixels, and its ink colour as hex.

    Raises:
        ValueError: When the id names a row or a colour that does not exist.
    """
    cls, rest = brush_id[:3], brush_id[3:]
    row, _, col = rest.partition("-")
    if row not in BRUSH_TREATMENTS or col not in BRUSH_COLOURS.get(cls, {}):
        raise ValueError(f"no such brush {brush_id!r}")
    over = style.brush_overrides.get(override or cls.lower(), {})
    brush = _sheet_brush(row, over, width_display_px, scale, style)
    _load_reservoir(brush, style)
    _load_quality(brush, style, scale)
    return brush, BRUSH_COLOURS[cls][col]


def _sheet_brush(
    row: str, over: dict[str, float], width_display_px: float, scale: float, style: BrushStyle
) -> Brush:
    """The brush a sheet row's treatment makes, with the overrides laid over it."""
    t = dict(BRUSH_TREATMENTS[row])
    t.pop("name_wet", None)
    jitter = over.get("jitter_px", style.brush_jitter_px)
    press_cell = over.get("press_cell_px", style.brush_press_cell_px)
    wobble = over.get("wobble_px", style.brush_wobble_px)
    brush = Brush(
        width=max(width_display_px, 0.4) * scale,
        darkness=over.get("darkness", t["darkness"]),
        bristles=int(over.get("bristles", t["bristles"])),
        gap=over.get("gap", t["gap"]),
        dry=over.get("dry", t["dry"]),
        thr=over.get("thr", t["thr"]),
        texture=over.get("texture", t["texture"]),
        jitter=jitter * scale,
        press=over.get("press", t["press"]),
        press_cell=press_cell * scale,
        wobble=wobble * scale,
        load=over.get("load", t["load"]),
        pool=over.get("pool", t["pool"]),
        bleed=over.get("bleed", t["bleed"]) * scale,
        lift=over.get("lift", t["lift"]) * scale,
        solid=over.get("solid", t.get("solid", 0.0)),
        step=style.brush_step,
        profile_px=style.brush_profile_px,
        pool_radius_frac=style.pen_pool_radius_frac,
        pool_gain=style.pen_pool_gain,
    )
    brush.load_px = max(brush.width * style.pen_load_px_frac, 2.0)
    brush.pen = row in PEN_ROWS
    return brush


def _load_reservoir(brush: Brush, style: BrushStyle) -> None:
    """Set the reservoir flags.

    A brush breaks when it runs down and a nib thins, so the two flags are
    separate and a brush never takes the nib's treatment.
    """
    if style.ink_starve and not brush.pen:
        brush.starve = True
        brush.run_px = max(brush.width * style.ink_reservoir, 1.0)
        brush.res_floor = style.ink_res_floor
        brush.dip_px = max(brush.run_px * style.ink_dip_mult, 1.0)
        brush.knee = style.ink_knee
    if style.pen_starve and brush.pen:
        brush.pen_starve = True
        brush.run_px = max(brush.width * style.pen_reservoir, 1.0)
        brush.dip_px = max(brush.run_px * style.ink_dip_mult, 1.0)
        brush.pen_thin = style.pen_thin


def _load_quality(brush: Brush, style: BrushStyle, scale: float) -> None:
    """Set the directional break and the brush-quality flags."""
    if style.dry_directional and brush.dry > 0.0:
        brush.dir_dry = True
        brush.dir_elong = style.dry_dir_elong
        brush.dir_cell = max(style.dry_dir_cell_px * scale, 1.0)
        brush.dir_gain = style.dry_dir_gain
        brush.dir_mix = style.dry_dir_mix
    if style.brush_organic:
        brush.organic = True
        brush.org_oct = max(int(style.organic_octaves), 1)
        brush.org_lac = max(style.organic_lacunarity, 1.1)
        brush.org_mult = max(style.organic_cell_mult, 0.05)
    if style.stroke_smooth:
        brush.smooth = max(brush.width * style.stroke_smooth_mult, 0.0)
    brush.band_px = max(style.bristle_bandlimit_px, 0.0)
    brush.contrast = max(style.bristle_contrast, 0.0)
    brush.coherence = max(style.bristle_drift_coherence, 0.0)


def ink_aux(shape: tuple[int, int], b: Brush) -> dict[str, np.ndarray] | None:
    """The extra accumulators a brush's reservoir and break flags need, or None.

    Both are weighted sums over the same deposits as the ink itself, so
    dividing one by the ink gives a per-pixel weighted mean of whatever it
    carries. That is why they exist: the reservoir and the break texture have
    to be read off the final density, because the splat and the `1 - exp(-acc)`
    saturation dilute a per-sample gate to nothing.

    Args:
        shape: The plate's pixel shape.
        b: The brush whose flags decide what is needed.

    Returns:
        Accumulators by name, or None when the brush asks for neither.
    """
    aux: dict[str, np.ndarray] = {}
    if b.starve:
        aux["res"] = np.zeros(shape, F32)
    if b.dir_dry:
        aux["tooth"] = np.zeros(shape, F32)
    return aux or None


def scaled_brush(b: Brush, k: int) -> Brush:
    """The same brush on a grid `k` times finer than the plate's own.

    Everything the brush measures in pixels moves with the grid. `unit` carries
    the factor, so the wavelengths written into `stamp` stay the lengths they
    were rather than shrinking with the grid they are sampled on. The stamp
    spacing and the tip's own sampling are scaled but capped (0.9 and 0.7): a
    finer grid is asked for precisely so those two land under a pixel.

    Args:
        b: The brush on the plate's grid.
        k: Pixels of the finer grid per plate pixel.

    Returns:
        The brush on that grid, or `b` itself at `k` of 1 or less.
    """
    if k <= 1:
        return b
    return replace(
        b,
        width=b.width * k,
        jitter=b.jitter * k,
        press_cell=b.press_cell * k,
        wobble=b.wobble * k,
        bleed=b.bleed * k,
        lift=b.lift * k,
        load_px=b.load_px * k,
        run_px=b.run_px * k,
        dip_px=b.dip_px * k,
        dir_cell=b.dir_cell * k,
        smooth=b.smooth * k,
        unit=b.unit * k,
        step=min(b.step * k, 0.9),
        profile_px=min(b.profile_px * k, 0.7),
    )
