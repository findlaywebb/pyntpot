"""The brush: the tool a stroke is stamped with, built from a brush sheet cell.

Key types: `Brush`, one mark-making tool in render pixels; `brush_from_id`, which builds one
from a brush sheet cell and the `BrushStyle`; `scaled_brush`, the same tool on a finer grid;
`ink_aux`, the extra accumulators a brush's flags need; `brush_id_known`, whether a brush id
names a sheet cell; `brush_ids`, every id it accepts; `BRUSH_OVERRIDE_KEYS`, the keys a
`brush_overrides` entry may set. The sheet's tables are in `ink.brush_sheet`.

A brush id `<PREFIX><row>-<column>`, such as `MAJ2-a`, is an opaque sheet cell name: this
module never reads the prefix as a feature class. Which class takes which cell is the style's
`brushes` field. It stamps nothing and reads no paper.

Invariants: a brush id naming a row or colour the sheet lacks raises `ValueError`; the
reservoir, directional break and quality flags are inert at their defaults.
"""

from dataclasses import dataclass, replace

import numpy as np

from pyntpot.ink.brush_sheet import BRUSH_COLOURS, BRUSH_TREATMENTS, PEN_ROWS
from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.naming import did_you_mean
from pyntpot.ink.noise import F32

#: The keys a `brush_overrides` entry may set: every key the sheet brush reads from it.
BRUSH_OVERRIDE_KEYS: frozenset[str] = frozenset(
    {
        "jitter_px",
        "press_cell_px",
        "wobble_px",
        "darkness",
        "bristles",
        "gap",
        "dry",
        "thr",
        "texture",
        "press",
        "load",
        "pool",
        "bleed",
        "lift",
        "solid",
    }
)


@dataclass
class Brush:
    """One mark-making tool, in render pixels.

    A stroke is a brush tip stamped along the path. The tip is a row of
    bristles: a one dimensional profile of weights with gaps in it, each
    bristle drifting slowly sideways as the stroke goes on, so the same
    bristles leave the same streaks the whole way down the mark. Pressure varies
    slowly and drives width and darkness together; the paper's own tooth gates
    the ink, so a dry brush breaks where the paper is low.

    Attributes:
        width: Full width of the tip at neutral pressure.
        darkness: Ink laid per stamp.
        bristles: Tines across the tip.
        gap: Share of them missing.
        dry: 0 a loaded wet brush, 1 bone dry.
        thr: Paper height at which a dry mark starts to break.
        jitter: How far a bristle wanders sideways.
        press: Slow pressure variation.
        press_cell: Pixels per pressure cycle.
        wobble: Slow wander of the whole line, for a pen.
        load: Extra ink where the brush is first set down.
        pool: A blot at the start, for a nib.
        bleed: Blur radius of the soft edge.
        lift: Pixels over which the stroke lifts to a point.
        texture: How much the bristles show: 0 a flat band, 1 grain.
        step: Spacing of the stamps along the path.
        profile_px: Spacing the tip's profile is sampled at.
        solid: A flat core under the bristles, for a loaded pen.
        load_px: How fast the set-down ink runs out; 0 derives it.
        pool_radius_frac: Radius of the blot a nib leaves where it touches down, as a share of the
            width.
        pool_gain: Density of that blot, as a multiple of `pool`.
        starve: Spend a per-bristle load along the stroke. The reservoir and the directional break
            fields from here to `pen_thin` are all inert at their defaults, so a brush built without
            the flags is the plain stamped brush.
        run_px: How far one load carries, in render pixels.
        res_floor: What is left in a nominally empty bristle.
        dip_px: Distance between reloads; 0 is never reload.
        knee: Ink kept at empty, before the paper gate.
        dir_dry: Stretch the break texture along the stroke.
        dir_elong: How much longer along the mark than across it one break is.
        dir_cell: Width of one break across the mark, in pixels.
        dir_gain: 1 is the paper's own contrast, more is harsher.
        dir_mix: How far the paper gate moves from the paper's own tooth toward the directional
            break, 0 to 1.
        pen: This treatment is a nib, not a brush.
        pen_starve: The nib thins and lightens as it runs down.
        pen_thin: How much of the width and the ink an empty nib has lost.
        organic: Drift and pressure from a lattice, not a sine. The brush quality fields from here
            to `smooth` are inert at their defaults, so a brush built without the flags is the plain
            stamped brush.
        org_oct: Octaves in each lattice noise.
        org_lac: The ratio between those octaves' cells.
        org_mult: Lattice cell, as a share of the sine's wavelength.
        smooth: Corner radius in render pixels; 0 leaves the path.
        unit: Pixels of the brush's own grid per render pixel. 1 is the plate itself; `scaled_brush`
            sets it when the ink is painted on a finer grid, so the wavelengths written into `stamp`
            stay the same lengths on the plate.
        band_px: How far the tip's own weights are smoothed across the mark, in render pixels. 0
            leaves the tip as it was.
        contrast: A multiplier on the tip's variation about its own mean weight.
        coherence: How much of its sideways drift a bristle shares with its neighbours, as a share
            of the tip. 0 draws every bristle's phase independently.
    """

    width: float
    darkness: float
    bristles: int
    gap: float
    dry: float
    thr: float
    jitter: float
    press: float
    press_cell: float
    wobble: float
    load: float
    pool: float
    bleed: float
    lift: float
    texture: float = 0.7
    step: float = 0.40
    profile_px: float = 0.55
    solid: float = 0.0
    load_px: float = 0.0
    pool_radius_frac: float = 0.5
    pool_gain: float = 1.9
    starve: bool = False
    run_px: float = 0.0
    res_floor: float = 0.38
    dip_px: float = 0.0
    knee: float = 0.62
    dir_dry: bool = False
    dir_elong: float = 5.0
    dir_cell: float = 7.0
    dir_gain: float = 1.0
    dir_mix: float = 0.8
    pen: bool = False
    pen_starve: bool = False
    pen_thin: float = 0.26
    organic: bool = False
    org_oct: int = 4
    org_lac: float = 2.17
    org_mult: float = 0.5
    smooth: float = 0.0
    unit: float = 1.0
    band_px: float = 0.0
    contrast: float = 1.0
    coherence: float = 0.0


def brush_id_known(brush_id: str) -> bool:
    """Whether `brush_id` names a row the sheet has and a colour its class has.

    Args:
        brush_id: A cell on the brush sheet, such as `RIV1-a`.

    Returns:
        True when `brush_from_id` would build a brush from it.
    """
    cls, rest = brush_id[:3], brush_id[3:]
    row, _, col = rest.partition("-")
    return row in BRUSH_TREATMENTS and col in BRUSH_COLOURS.get(cls, {})


def brush_ids() -> tuple[str, ...]:
    """Every brush id the sheet carries, the ones `brush_id_known` accepts.

    Returns:
        The ids in sheet order: by prefix, then row, then colour column.
    """
    return tuple(
        f"{cls}{row}-{col}"
        for cls, cols in BRUSH_COLOURS.items()
        for row in BRUSH_TREATMENTS
        for col in cols
    )


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
        ValueError: When the id names a row or a colour that does not exist; the message names
            the nearest id when one is close.
    """
    if not brush_id_known(brush_id):
        raise ValueError(f"no such brush {brush_id!r}{did_you_mean(brush_id, brush_ids())}")
    cls, rest = brush_id[:3], brush_id[3:]
    row, _, col = rest.partition("-")
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
