"""The journal map's raster painter: washes, brushes and the notebook card.

The route chart draws a session on a painted sheet rather than over a set of
vector washes. Everything with a soft edge is painted here, at twice the size it
is shown at, and written out as WebP plates the page stacks with
`mix-blend-mode: multiply`: the card, and one plate carrying every pigment. The
route, the lettering and the marks stay vector on top, in `charts.route_track`,
because those are the things that have to stay crisp.

Two rules run through all of it. Every size is stated in metres and converted at
the plate's own metres per pixel, with a floor in on-screen pixels, so a 13 km
ride and a 3 km run carry lines of the same weight rather than the same number
of metres. And every number is a `PaintStyle` field, so a theme's `style.json`
can move any of them without a change here.

Nothing in this module reaches the network or any activity service. It paints
the `Basemap` that `geo.journal_layers` has already assembled from the cache.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field, fields, replace
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
from PIL import Image

from pyntpot._port.style import coerce_like
from pyntpot.ink.chains import chain_lines
from pyntpot.ink.polyline import simplify

if TYPE_CHECKING:
    from pyntpot.maps.basemap import Basemap, ElevationPatch, Line
    from pyntpot.maps.plates import Plates
    from pyntpot.maps.style import Style

F32 = np.float32
Pt = tuple[float, float]
#: One layer of the pigment stack: its density, its pigment over white, and,
#: where the caller knows it, what that pigment shows over black as a share of
#: that. Only Kubelka-Munk glazing reads the third; multiply ignores it.
Layer = tuple[np.ndarray | None, np.ndarray] | tuple[np.ndarray | None, np.ndarray, float]

#: Painted plates live inside the geo cache, one directory per activity, so a
#: caller that redirects the cache redirects the plates with it.
PLATES_SUBDIR = "plates"

#: The card's own cream, before anything is laid on it.
PAPER = "#f3ead6"

#: Multiply colours: what a full-strength wash of each pigment transmits. The
#: inks are darker than the washes, because a mark is not a wash.
PIGMENTS = {
    "farmland": "#dfe0b0",
    "meadow": "#cfdfae",
    "orchard": "#d5dda2",
    "scrub": "#c9d5a4",
    "heath": "#e0cda2",
    "sand": "#ecdfbe",
    "rock": "#dcd6c6",
    "wetland": "#bfd2cd",
    "built": "#ddd3c3",
    "works": "#d2cbc0",
    "wood": "#a8c286",
    "pale": "#d5e0b4",
    "water": "#9ec4de",
    "relief": "#c9bda4",
    "rim": "#c2ad91",
}

#: What each pigment shows over black, as a share of what it shows over white.
#: This is the one number Kubelka-Munk glazing needs beyond the hex, and it is
#: the honest place to record which pigments stain: near 0 is a transparent
#: glaze that lets the layer under it through, near 1 is a covering body colour.
#: The wood green and the water blue stain; the relief grey and the built greys
#: sit on the surface. Anything not named here takes `km_transparency`.
TRANSPARENCY = {
    "farmland": 0.10,
    "meadow": 0.09,
    "orchard": 0.09,
    "scrub": 0.08,
    "heath": 0.14,
    "sand": 0.16,
    "rock": 0.22,
    "wetland": 0.08,
    "built": 0.26,
    "works": 0.28,
    "wood": 0.05,
    "pale": 0.12,
    "water": 0.04,
    "relief": 0.30,
    "rim": 0.18,
}

#: How dark a wash of each class goes, and how hard its edge pools.
COVER_CFG = {
    "farmland": (0.52, 0.20),
    "meadow": (0.55, 0.22),
    "orchard": (0.55, 0.24),
    "scrub": (0.58, 0.26),
    "heath": (0.60, 0.26),
    "sand": (0.50, 0.22),
    "rock": (0.52, 0.26),
    "wetland": (0.60, 0.28),
    "built": (0.55, 0.20),
    "works": (0.58, 0.22),
    "wood": (0.72, 0.30),
}

#: The eight stroke treatments of the brush sheet, by row. A brush id is a
#: class, a row and a colour: `MAJ2-a` is the A and B road width, treatment 2,
#: colour a. Widths live in `PaintStyle`, because the same treatment is drawn at
#: a river's width on one plate and a lane's on another.
BRUSH_TREATMENTS: dict[str, dict[str, float]] = {
    "1": dict(
        name_wet=1.0,
        darkness=1.8,
        bristles=26,
        gap=0.03,
        dry=0.15,
        thr=0.34,
        texture=0.32,
        press=0.14,
        load=0.6,
        pool=0.0,
        bleed=1.5,
        lift=34,
    ),
    "2": dict(
        darkness=2.0,
        bristles=22,
        gap=0.09,
        dry=0.30,
        thr=0.38,
        texture=0.42,
        press=0.20,
        load=0.55,
        pool=0.0,
        bleed=1.1,
        lift=30,
    ),
    "3": dict(
        darkness=2.4,
        bristles=16,
        gap=0.14,
        dry=0.42,
        thr=0.42,
        texture=0.55,
        press=0.26,
        load=0.5,
        pool=0.0,
        bleed=0.9,
        lift=26,
    ),
    "4": dict(
        darkness=4.8,
        bristles=18,
        gap=0.28,
        dry=0.72,
        thr=0.48,
        texture=0.82,
        press=0.34,
        load=0.7,
        pool=0.0,
        bleed=0.5,
        lift=28,
    ),
    "5": dict(
        darkness=7.2,
        bristles=5,
        gap=0.04,
        dry=0.22,
        thr=0.40,
        texture=0.40,
        press=0.18,
        load=1.6,
        pool=1.4,
        bleed=0.3,
        lift=12,
    ),
    "6": dict(
        darkness=6.0,
        bristles=6,
        gap=0.0,
        dry=0.10,
        thr=0.32,
        texture=0.16,
        press=0.10,
        load=0.5,
        pool=0.9,
        bleed=0.45,
        lift=16,
        solid=0.75,
    ),
    "7": dict(
        darkness=7.4,
        bristles=8,
        gap=0.44,
        dry=0.82,
        thr=0.53,
        texture=0.86,
        press=0.45,
        load=0.4,
        pool=0.0,
        bleed=0.35,
        lift=14,
    ),
    "8": dict(
        darkness=6.4,
        bristles=4,
        gap=0.02,
        dry=0.20,
        thr=0.40,
        texture=0.36,
        press=0.14,
        load=1.2,
        pool=0.8,
        bleed=0.25,
        lift=14,
    ),
}
#: The treatment rows that are a nib rather than a brush: a flat core, a
#: touch-down blot, and a line that thins rather than breaking when it runs low.
PEN_ROWS = frozenset({"5", "6", "8"})

#: The colour column of a brush id, per class.
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
class PaintStyle:
    """Every number the painter uses, so a theme can move any of them.

    The defaults are the settings the reference sheets are painted with: the
    fitted ribbon at its own radius, land cover on, wood texture at 75 and dab
    density at 78, the coast a hard mask with the sea run to the card edge, the
    river importance curve at 1.0, and the five brushes RIV1-a, STR3-a, MAJ2-a,
    LAN5-a and TRK4-d.

    A `style.json` reaches all of it through a `paint` block, which
    `from_style` merges field by field, so a theme states only what it changes.
    """

    # --- the card, in pixels
    #: Display width of the card in CSS pixels; the height follows its aspect.
    #: 900 is the width the plates were set at, and it is what decides
    #: whether the lanes and the tracks are drawn: below it, a display pixel is
    #: more than eight metres of ground and a lane is not a mark.
    display_px: int = 900
    #: Painted at this multiple of the display size, so the grain survives a
    #: retina screen. 2 is what the plates were set at.
    supersample: int = 2
    #: Write the plates as lossless WebP. On, because lossy WebP is what put
    #: the two-plateau step in a stroke: it transforms in 4 by 4 blocks and
    #: subsamples the chroma to half resolution, so a mark three or four render
    #: pixels wide has its edge-to-centre ramp flattened into a light plateau
    #: and a dark one with a jump between them, and its paper grain removed.
    #: Measured on a woodland plate, wash layer, against the float the
    #: painter composed: mean error over the ink 0.023 at quality 74 and still
    #: 0.008 at quality 100, blocking ratio 1.15 against 1.01, and on the paper
    #: plate a blocking ratio of 2.56 and 63% of the grain gone. No quality
    #: setting fixes it, because the chroma subsampling is not a quality
    #: setting. Off is the old encoder, and the two quality numbers below are
    #: what it uses; the plates are then about eighteen times smaller.
    plate_lossless: bool = True
    webp_quality: int = 74
    paper_quality: int = 80
    #: The notebook grid. Off by default.
    grid: bool = False
    grid_spacing_px: float = 26.0
    grid_opacity: float = 0.34
    paper_hex: str = PAPER
    #: Paper texture, the worn border, the vignette and the foxing.
    paper_tooth: float = 0.085
    paper_worn: float = 0.20
    paper_vignette: float = 0.05
    paper_foxing: float = 0.09
    #: Seeds, so the same box paints the same sheet every time.
    sheet_seed: int = 11
    ink_seed: int = 91
    dither_seed: int = 23

    # --- the ribbon: the trimmed extent of the painted ground
    #: Radius in metres is `ribbon_k * sqrt(box) + ribbon_c`, then the slider.
    ribbon_k: float = 7.15
    ribbon_c: float = 158.0
    #: The slider, as a multiplier on that. 1.0 leaves the fitted radius unchanged.
    ribbon_mult: float = 1.0
    ribbon_min_m: float = 420.0
    ribbon_max_m: float = 1250.0
    #: The card is framed as though the widest ribbon were on, so the same box
    #: is composed whatever the slider is set to.
    card_grow_mult: float = 1.55
    card_pad_frac: float = 0.09
    card_pad_ribbon_frac: float = 0.55
    card_aspect_min: float = 1.12
    card_aspect_max: float = 1.62
    #: Fill what the outside cannot reach, so the inside of a loop is painted.
    ribbon_fill: bool = True
    #: Torn edge, as a fraction of the render width, with a floor in pixels.
    ribbon_tear_frac: float = 0.004
    ribbon_tear_floor_px: float = 5.0
    #: The pooled edge just inside the tear.
    rim_strength: float = 0.40
    #: The coast is a hard edge: nothing the ribbon carries crosses it.
    coast_hard_mask: bool = True
    #: The sea is painted to the edge of the card and never trimmed.
    sea_to_edge: bool = True

    # --- land cover
    land_cover: bool = True
    relief: bool = True
    #: Painting order, low to high. A wood over farmland replaces it, so the
    #: plate carries one class per pixel and no two land pigments can stack.
    cover_order: tuple[str, ...] = (
        "farmland",
        "meadow",
        "orchard",
        "scrub",
        "heath",
        "sand",
        "rock",
        "wetland",
        "built",
        "works",
        "wood",
    )
    cover_cfg: dict[str, tuple[float, float]] = field(default_factory=lambda: dict(COVER_CFG))
    pigments: dict[str, str] = field(default_factory=lambda: dict(PIGMENTS))
    #: The pale single wash drawn instead of the classes when cover is off.
    pale_base: float = 0.50
    pale_pool: float = 0.16

    # --- the wood, as a texture and a scatter of dabs
    #: Both are a cross fade over three printed scales, because a texture's
    #: scale cannot be changed after it is printed. 0.75 and 0.78 are the
    #: defaults for the two sliders.
    wood_texture: float = 0.75
    wood_dabs: float = 0.78
    wood_tex_scales: tuple[float, ...] = (2.1, 1.0, 0.45)
    wood_tex_strengths: tuple[float, ...] = (0.30, 0.40, 0.48)
    dab_spacings: tuple[float, ...] = (1.7, 1.0, 0.6)
    dab_strengths: tuple[float, ...] = (0.34, 0.36, 0.38)

    # --- the ink
    #: Watercourse width in display pixels: coefficient and exponent on the box
    #: in kilometres, then a floor and a ceiling. The exponents are negative, so
    #: a line grows in metres as the box grows but shrinks on screen, which is
    #: what keeps a river prominent on a ride and a brook modest on it.
    river_curve: dict[str, tuple[float, float, float, float]] = field(
        default_factory=lambda: {
            "major": (14.2, -0.20, 4.0, 12.0),
            "medium": (10.5, -0.42, 2.2, 7.0),
            "minor": (13.5, -0.78, 1.3, 8.0),
        }
    )
    #: Share of the box's longest named river a river's own run has to reach
    #: to also count as major. A box-spanning river and a short tributary
    #: fully inside the box can otherwise look comparably long against the
    #: box's span alone, which can name the short tributary "major"
    #: alongside the box-spanning river.
    major_river_rel_frac: float = 0.65
    #: Metres per display pixel above which the lanes and tracks are dropped.
    minor_roads_mppd: float = 8.0
    #: The wood's blotch, the dab spacing and the granulation, in metres: a
    #: floor, and a multiple of the plate's own metres per display pixel.
    blotch_m: tuple[float, float] = (190.0, 26.0)
    dab_spacing_m: tuple[float, float] = (620.0, 95.0)
    gran_m: tuple[float, float] = (70.0, 9.0)
    #: The importance curve slider, as a multiplier on every painted width.
    river_mult: float = 1.0
    #: Class to brush id. Water is classed by importance, roads by what the
    #: session used: a lane is a pen, a track is the dry broken brush.
    brushes: dict[str, str] = field(
        default_factory=lambda: {
            "major": "RIV1-a",
            "medium": "STR2-a",
            "minor": "STR3-a",
            "coast": "STR2-a",
            "road_major": "MAJ2-a",
            "lane": "LAN5-a",
            "track": "TRK4-d",
        }
    )
    #: Painted width in display pixels for the classes whose width is not on
    #: the river curve.
    brush_width_px: dict[str, float] = field(
        default_factory=lambda: {
            "road_major": 3.6,
            "lane": 1.8,
            "track": 2.4,
        }
    )
    #: The coast is drawn at this share of a medium watercourse.
    coast_width_frac: float = 0.8
    #: Shared stroke geometry, in display pixels, and the per-class overrides.
    #: The lane's pool is the pen touch-down as it was last tuned: a nib meeting
    #: the paper, not a line that starts fat.
    brush_jitter_px: float = 0.55
    brush_press_cell_px: float = 110.0
    brush_wobble_px: float = 0.32
    brush_step: float = 0.40
    brush_profile_px: float = 0.55
    #: How fast the set-down ink runs out, as a multiple of the brush width.
    pen_load_px_frac: float = 0.85
    #: Radius and density of the blot a nib leaves where it touches down.
    pen_pool_radius_frac: float = 0.5
    pen_pool_gain: float = 1.9
    brush_overrides: dict[str, dict[str, float]] = field(
        default_factory=lambda: {
            "major": {"press_cell_px": 170.0, "jitter_px": 0.55, "wobble_px": 0.25},
            "medium": {"press_cell_px": 130.0, "jitter_px": 0.50, "wobble_px": 0.30},
            "minor": {"press_cell_px": 95.0, "jitter_px": 0.55, "wobble_px": 0.35},
            "coast": {"press_cell_px": 120.0, "jitter_px": 0.40, "wobble_px": 0.20},
            "lane": {"press_cell_px": 70.0, "jitter_px": 0.30, "wobble_px": 0.55, "pool": 1.4},
            "track": {"press_cell_px": 60.0, "jitter_px": 0.65, "wobble_px": 0.40},
        }
    )

    # --- the route's own painted plate, for the one route style that is not
    # vector. It is an alpha plate, tinted at render time by the route colour,
    # so a theme can change the ink without repainting.
    route_pen: bool = True
    route_pen_brush: str = "MAJ6-e"
    route_pen_width_px: float = 3.0

    # --- the crisp layer, read by `charts.route_track` rather than here
    #: The hand. A stack ending in cursive, never a webfont the page depends on.
    label_font: str = '"Patrick Hand",cursive'
    label_size_px: float = 20.0
    #: The landmark cap. Five was the count before the ground was lettered:
    #: with no settlements, watercourses or road numbers on the sheet, five
    #: landmarks were what filled it. Now that the ground carries its own names
    #: the landmarks compete with them, and three leaves room for both. Spans have
    #: their own cap in `labels.SPAN_MAX`.
    label_max: int = 3
    label_pin_colour: str = "#b4682c"
    label_ink: str = "#241c14"
    label_glow_colour: str = "#f7f0dd"
    #: Draw the label layer at all. Nothing reads this yet: it is the switch the
    #: label plate is turned off with once there is one, so a theme that wants
    #: the painting bare has somewhere to say so.
    labels: bool = True
    #: Letter the settlements, the watercourses and the roads the box holds,
    #: which are in the data and were never drawn. This was off until a label
    #: engine could set them as the hierarchy asks: a settlement beside its dot
    #: with no leader, a river along its own water in spaced italic, a road
    #: number along its own tarmac. There is one now.
    label_ground: bool = True
    #: Every random draw a label makes comes from this plus the label's own
    #: name, so an unchanged map letters identically on every render and a
    #: deliberate reshuffle is one number.
    label_seed: int = 17
    #: How far a named road or watercourse is simplified before it is kept in
    #: the manifest for a label to be set along, in display pixels.
    label_geom_tol_px: float = 8.0
    #: How a glyph is turned into something the pen follows. `centreline` thins
    #: the face's own outline to a written skeleton; `outline` draws round the
    #: contour itself. They are two different letters, not a choice and a
    #: fallback, and the second is what the first falls back to.
    label_route: str = "centreline"
    #: The face, under `analysis/report/fonts/`. Empty is the vendored one.
    label_face: str = ""
    #: The nib the lettering is written with, and its width in display pixels.
    #: A nib, not a brush: a letter at fourteen pixels breaks up if the mark can
    #: break, and a broken letter is a wrong letter rather than a textured one.
    label_brush: str = "MAJ6-e"
    label_pen_width_px: float = 1.05
    #: The outline route draws two strokes where the centreline draws one, a
    #: stroke's width apart, so the same nib fills the counters and the letter
    #: comes out a bolder thing than the face is. It writes with a finer one.
    label_outline_width_frac: float = 0.62
    #: The leader and the span line, one step lighter, so the line recedes
    #: behind the name it points at.
    label_leader_brush: str = "MAJ6-e"
    label_leader_width_px: float = 0.85
    #: The pen's angle, anticlockwise from the writing line, and how much of the
    #: width it takes off a stroke drawn along it. Without this the letters come
    #: out one thickness the whole way round, which is a plotter and not a pen.
    label_pen_angle_deg: float = -38.0
    label_pen_thin: float = 0.52
    #: The backing wash: paper-coloured, laid through the wash machinery, and
    #: absent where the ground is already pale enough to read on.
    label_wash: bool = True
    label_wash_alpha: float = 0.5
    label_wash_dark_floor: float = 0.22
    label_wash_spread: float = 0.75
    #: The ink a name in the route's own colour is written in. The caller fills
    #: it from the sport's route ink; the default is what the route was.
    label_route_ink: str = "#c22050"
    label_water_ink: str = "#4a7691"
    #: The ink a name written *on* the water is set in. Reversed out of the
    #: river in the paper's own cream rather than written into it in a dark ink:
    #: the water is a mid-tone, so a dark ink is fighting it from the wrong side.
    #: Measured on a painted river, black holds 3.9:1 and this holds 4.7:1,
    #: and the difference on the sheet is larger than the ratio suggests because
    #: the letters no longer share a value with the bridges crossing them.
    label_in_water_ink: str = "#f8f4e9"
    home_glyph: bool = True
    #: The coarse darkness grid the label placer scores against.
    dark_grid: tuple[int, int] = (80, 60)

    # --- phase 1: brush ---
    # Every field here is off or inert by default, so the default
    # plates paint byte for byte the same until a theme turns one on.
    #: Ink starvation with reload. Each bristle sets off with its own load,
    #: spends it in proportion to what it lays down, and the paper gate tightens
    #: as the load falls, so a long lane starts loaded and breaks into skips
    #: that run along the mark rather than everywhere at once.
    ink_starve: bool = False
    #: How far a full load carries, as a multiple of the brush's own width. A
    #: track at 4.8 render pixels wide runs about 700 px on one load.
    ink_reservoir: float = 150.0
    #: What is left in a bristle when it is nominally empty: a brush never goes
    #: to nothing, it goes to a scratch.
    ink_res_floor: float = 0.38
    #: The dip. A painter reloads, and the seam that leaves is what makes a long
    #: line look drawn rather than extruded. In reservoir lengths.
    ink_dip_mult: float = 3.2
    #: How much of the ink survives an empty brush before the paper gate is
    #: asked: 1.0 is no darkening at all from the reservoir itself.
    ink_knee: float = 0.62
    #: Directional dry brush: the break texture stretched along the stroke, so a
    #: dry mark reads as scratches running with the line rather than blotches.
    dry_directional: bool = False
    #: How much longer than it is wide a break is, and the width of one across
    #: the mark, in display pixels. Under the paper's own grain on purpose: a
    #: break that is coarser than the tooth it replaces does not break the mark
    #: more often, it breaks it in fewer, longer places, and a track stops
    #: reading as a track.
    dry_dir_elong: float = 4.5
    dry_dir_cell_px: float = 0.9
    #: How hard the directional tooth is, against the paper's own contrast
    #: under the same mark. 1.0 swaps the direction of the break and nothing
    #: else; above 1 asks for a tooth harsher than the paper.
    dry_dir_gain: float = 1.0
    #: How far the gate moves from the paper's own tooth toward that texture.
    dry_dir_mix: float = 0.8
    #: A nib runs down too. Its line does not break, it thins and lightens over
    #: a long run and comes back at the reload.
    pen_starve: bool = False
    #: The nib's run, as a multiple of its width: much longer than a brush's.
    pen_reservoir: float = 420.0
    #: How much of the width and the ink an empty nib has lost.
    pen_thin: float = 0.26

    # --- phase 1: compositing and paper ---
    # Off or inert by default, on the same rule: the default plates paint byte
    # for byte the same until a theme turns one on.
    #: Kubelka-Munk glazing in place of multiply for the pigment stack. Multiply
    #: is transmission with no scattering, so two washes crossing lose chroma
    #: and go grey; Kubelka-Munk gives each pigment absorption and scattering
    #: derived from what it shows over white and over black, and composites the
    #: layers optically, so the greens and blues keep their hue where they meet.
    km_glazing: bool = False
    #: Per-pigment transparency, as `TRANSPARENCY`. Ink and anything unnamed
    #: takes the default below.
    pigment_transparency: dict[str, float] = field(default_factory=lambda: dict(TRANSPARENCY))
    km_transparency: float = 0.06
    #: One cold-press paper field: a second fibre noise stretched along a
    #: sheet-wide axis, mixed into the tooth, with granulation then taken from
    #: the paper's own height rather than an unrelated field. Heavy pigment
    #: settles in the pits the dry brush also breaks on.
    paper_fibre: bool = False
    paper_fibre_mix: float = 0.35
    #: How much longer than it is wide a fibre is, the angle of the grain in
    #: radians, and the fibre's own cell in render pixels.
    paper_fibre_stretch: float = 3.0
    paper_fibre_angle: float = 0.42
    paper_fibre_cell_px: float = 4.2
    #: How sharply granulation follows the pits. Above 1 the pigment has to
    #: reach a real hollow before it settles.
    gran_gamma: float = 1.7
    #: One wet-area map shared across the land classes, so a wash knows another
    #: is beside it: inside the union of the cover, neighbours bleed into each
    #: other and no class boundary carries its own rim. The outer silhouette of
    #: the land keeps its edge, which is the one that should have it.
    wet_bleed: bool = False
    wet_bleed_px: float = 5.0
    #: How far the bleed goes inside the wet area, and how much of the rim it
    #: takes away there.
    wet_bleed_mix: float = 0.55
    wet_rim_drop: float = 0.7
    #: How far back from the land's outer edge the wet area starts, as a
    #: multiple of the cover's own rim width. The silhouette of the whole land
    #: mass is the one edge that should stay hard, so the wet map has to end
    #: before it does.
    wet_bleed_edge_mult: float = 2.2
    #: Edge darkening from an outward flow term rather than mask minus blur.
    #: Real edge darkening is pigment carried out by evaporation at a pinned
    #: contact line: it sits inside the wet boundary, decays inward, and is
    #: wider on a large wash instead of one width everywhere.
    flow_rim: bool = False
    #: How fast the rim widens with the wash's area. The width is `rim_px` at
    #: the reference area below and grows as area to this power.
    flow_rim_exp: float = 0.125
    flow_rim_ref_frac: float = 0.02
    #: The distance the rim decays over, as a share of `rim_px`, at that
    #: reference area. Well under 1, because an exponential has a tail and the
    #: mask-minus-blur rim it replaces does not.
    flow_rim_frac: float = 0.38
    #: Blooms: a re-wet event with no solver. A second front of liquid pushes
    #: deposited pigment out into a crenellated ridge, leaving a lighter centre.
    blooms: bool = False
    #: Blooms per wash, against the square root of its area. 0 turns them off
    #: without turning the flag off.
    bloom_density: float = 1.0
    bloom_max: int = 5
    #: The bloom's radius as a share of the root of the wash's area, how much
    #: pigment the front lifts out of the centre, and how far the fbm warps the
    #: front off a circle.
    bloom_radius_frac: float = 0.17
    bloom_lift: float = 0.45
    bloom_warp: float = 0.45
    bloom_seed: int = 57

    # --- phase 2: tuning and sea ---
    # Inert by default on the same rule as phase 1: 1.0 is the bloom the phase 1
    # numbers already lay, and the sea variation is off until a theme asks.
    #: How hard a bloom works, as a multiple of `bloom_lift`. A backrun at full
    #: strength is a demonstration of a backrun; the effect should be
    #: present and not the first thing the eye lands on.
    bloom_strength: float = 1.0
    #: Large-scale variation in the sea's pigment strength. A flat sea wash is
    #: the one place the plate reads as a fill rather than as paint: a real
    #: wash over that much paper dries in broad paler and deeper patches, with
    #: the pigment worked along the shore rather than across it.
    sea_variation: bool = False
    #: The size of a patch on the ground, in metres, so the same sea reads the
    #: same on a 3 km run and a 40 km ride. Converted at the plate's own mpp.
    sea_variation_cell_m: float = 600.0
    #: How far the density swings across those patches, 0 to 1, where 1 is plus
    #: or minus the wash's own density.
    sea_variation_amount: float = 0.5
    #: The streaking that runs along the coast: its share of the swing, how
    #: much longer than wide a streak is, and how far out from the shore it
    #: still shows, in metres. Its direction is taken from the coast itself.
    sea_variation_streak: float = 0.45
    sea_variation_elong: float = 6.0
    sea_variation_band_m: float = 420.0
    sea_variation_seed: int = 73
    #: How wide a gap in the land cover the wet map closes over, in render
    #: pixels, before it backs off from the land's edge. Measured, not guessed:
    #: on a woodland plate the classes meet along hairlines of unmapped ground,
    #: the median class seam sits 2 px from one, and a wet map taken from the
    #: raw union is therefore punched full of holes exactly where two washes
    #: meet. At 5 px the share of seam that is wet goes from 0.00 to 0.58 while
    #: the dry share of the card moves 0.148 to 0.140, so the land's outer
    #: silhouette is where it was. 0 is the union as it stands.
    wet_close_px: float = 0.0

    # --- phase 2: wash ---
    # Off or inert by default, on phase 1's rule: the default plates paint byte
    # for byte the same until a theme turns one on.
    #: Recursive midpoint deformation of the land cover's own outlines before
    #: they are rasterised. The wash edge is a blurred mask thresholded against
    #: two noise scales, so every edge wobbles at the same two frequencies and
    #: none of them stays sharp. Displacing the polygon instead, with a
    #: variance carried per segment and randomised into each child, gives an
    #: outline that is loose in one place and tight in the next. It costs
    #: polygon work rather than pixel work. The surveyed coast and the lakes
    #: are not deformed: that edge is a fact, not a brush stroke.
    silhouette_deform: bool = False
    #: One displacement as a share of the segment it sits on, at the first
    #: round, and how much of that each round hands its children.
    silhouette_deform_amount: float = 0.26
    silhouette_deform_decay: float = 0.55
    #: How many rounds of midpoint displacement. Each doubles the ring's point
    #: count, so this is also the cost.
    silhouette_deform_depth: int = 4
    #: A ceiling on one displacement, in metres: a floor, and a multiple of the
    #: plate's own metres per render pixel, so a long straight field boundary
    #: is not thrown across the sheet on a wide box.
    silhouette_deform_max_m: tuple[float, float] = (16.0, 3.0)
    #: Where the recursion stops, in render pixels: a segment shorter than this
    #: is already below the wash's own edge noise.
    silhouette_deform_min_px: float = 1.6
    silhouette_deform_seed: int = 73
    #: Two-pigment washes. A real wood green is not one pigment: it is a
    #: staining green with a heavier blue-black in it, and the two separate as
    #: the wash dries, the heavy one settling into the paper's tooth while the
    #: light one floats on the surface. Curtis' pigment separation, as one
    #: extra layer per class rather than a second solver. It is meant to be
    #: read through `km_glazing`, which is what keeps the two hues apart where
    #: they lie over each other.
    pigment_separation: bool = False
    #: The second pigment per class, over white. Only the classes named here
    #: separate; anything else stays the one wash it was.
    separation_pigments: dict[str, str] = field(default_factory=lambda: {"wood": "#6e7f8b"})
    #: How much of the wash's density the heavy pigment carries, and how
    #: sharply it follows the pits. The gamma is above the granulation's,
    #: because a pigment that settles out has to reach a real hollow.
    separation_share: float = 0.22
    separation_gamma: float = 2.2
    #: What the heavy pigment shows over black, as a share of over white. A
    #: blue-black stains, so it is low.
    separation_transparency: float = 0.07
    #: One bounded shallow-water pass over the whole sheet, on a coarse grid:
    #: velocities from the pressure gradient, a fixed number of relaxation
    #: iterations rather than a convergence test, the outward flow at the wet
    #: boundary, then pigment advected and deposited. It buys directional
    #: drying and edge darkening that varies around a shape, in one pass shared
    #: by every class. It modulates the densities the painter already has and
    #: never becomes them, so a failure degrades to the plate without it.
    fluid_pass: bool = False
    #: How much smaller than the plate the grid is. Quarter resolution is what
    #: the cost allows; full resolution is several seconds.
    fluid_grid: int = 4
    #: Steps, and relaxation iterations inside a step. Both are counts and
    #: neither is a tolerance: that is what keeps the pass deterministic.
    fluid_steps: int = 40
    fluid_relax: int = 4
    #: How far the deposit moves a density, either way.
    fluid_amount: float = 0.30
    #: How much the settling follows the paper's own height.
    fluid_gran: float = 0.6
    fluid_seed: int = 41

    # --- phase 2: brush quality ---
    # The rest of this block is off or inert by default, on phase 1's rule: the
    # smoke box paints the same bytes until a theme turns one on. `ink_ss` is
    # the exception and is on, because a mark under four render pixels wide is
    # not a stroke the plate's own grid can hold.
    #: Paint the ink at this multiple of the plate's own grid and Lanczos-reduce
    #: it back. The plate is written at `supersample` times the display size and
    #: shown at up to one render pixel per device pixel, so the ink's own grid is
    #: what the eye reads as pixelation: a 1.8 display pixel lane is under four
    #: render pixels wide and its bilinear splat lands on a visible stair. 1 is
    #: the plate's grid. Measured on that lane, stamped along a shallow diagonal
    #: so it crosses the pixel grid: the mark's weight beats by 1.03% of itself
    #: at 1, 0.70% at 2 and 0.73% at 3, and its cross-section carries 0.81
    #: distinct 8-bit levels per pixel at 1, 0.85 at 2, 0.86 at 3 and 0.88 at 4.
    #: 3 is where it stops paying: 4 and above buy a hundredth of a level each
    #: and cost the square of the grid in memory.
    ink_ss: int = 3
    #: Non-repeating drift. Every wander in a stroke was a sine, so a long mark
    #: repeated itself: the bristle drift at 390 render pixels and shared by
    #: every bristle, the line's wobble at 210 and 69, the pressure at 2 pi times
    #: its own cell, and each bristle's break at 116 to 215 with a beat near 500
    #: where two of them differ a little. On the flag each of the four becomes a
    #: one dimensional fractal noise sampled along the stroke from the stroke's
    #: own lattice, which has no period for the eye to find.
    brush_organic: bool = False
    #: Octaves in each of those and the ratio between them. The lacunarity is
    #: deliberately not 2: octaves an octave apart line up with each other.
    organic_octaves: int = 4
    organic_lacunarity: float = 2.17
    #: The coarsest feature, as a share of the wavelength the sine had. At 0.5 a
    #: lattice cell is half a wavelength, which is the same feature size, so the
    #: flag changes what repeats rather than how the mark looks.
    organic_cell_mult: float = 0.5
    #: Join polylines that meet end to end before stamping. OSM splits one road
    #: into many ways: a woodland plate's A road arrives as 43 separate strokes, 25
    #: of them under 60 render pixels, and each took a fresh tip pattern, a fresh
    #: set-down blob and a fresh lift taper at both ends. That chain of tapered
    #: lozenges with a bead at every join is the sectioning the eye catches.
    ink_joins: bool = False
    #: How close two ends have to be to count as the same mark, in render pixels.
    ink_join_tol_px: float = 2.5
    #: Round a corner to the brush's own width before stamping. A generalised
    #: track turns 82 degrees at the 95th percentile of its vertices, and a tip
    #: stamped straight through that folds over itself and leaves a bead; no
    #: brush draws a corner tighter than it is wide.
    stroke_smooth: bool = False
    #: The corner radius, as a multiple of the brush's own width.
    stroke_smooth_mult: float = 0.7
    #: Bandlimit the tip's own lanes to what a mark this wide can show, with
    #: this sigma in render pixels. A treatment names a fixed number of logical
    #: bristles whatever it is painted at, so `road_major` at 7.2 render pixels
    #: carries 22 of them. One bristle is then 0.33 px; a dropped one, which
    #: `gap` 0.09 gives about two of per stroke, goes from full weight to
    #: nothing and back inside two thirds of a pixel; and the clumping sine
    #: lands between 1.3 and 3.1 px, which is the plate's own Nyquist. None of
    #: that can be drawn, so what reaches the plate is an alias of it. This
    #: smooths the bristle weights and the break texture across the tip, and
    #: only those: the deposit positions are untouched, so the mark keeps its
    #: width and its edge. Measured on one `road_major` stroke's accumulator,
    #: the cross-tip spread against the mark's own envelope, with the drift
    #: already shared: 0.191 at 0 and 0.042 at 0.9, where a tip with no drift
    #: at all sits at 0.037. It is the second half of the fix and it only
    #: shows once the first is in: with the tip still folding it moves that
    #: same number from 0.447 to 0.414, which is nothing. 0 is the tip as it
    #: was. The lanes a mark is genuinely wide enough to show survive it: the
    #: major river at 16.8 px keeps its own.
    bristle_bandlimit_px: float = 0.9
    #: How hard the tip's lanes are, as a multiplier on the variation about the
    #: tip's own mean. It scales what the bristles weigh and where the brush is
    #: breaking, and leaves the tip's profile and its pressure alone, so the
    #: knob moves the streaking and not the mark. 1.0 is where this is left:
    #: with the fold gone and the weights bandlimited, what remains is
    #: variation the plate can actually draw, so it is texture rather than an
    #: artefact. This is the knob to soften it further, or to
    #: ask for more: the same spread is 0.037 at 0.5 and 0.067 at 2.0.
    bristle_contrast: float = 1.0
    #: How much of its sideways drift a bristle shares with its neighbours, as
    #: a share of the tip's own width. This is the fault the shared drift fixes.
    #: The regular parallel rails along a road, with a hard step from one to
    #: the next, are the tip folded over itself: every bristle's drift phase
    #: was drawn independently of the one beside it, so two neighbours could be
    #: driven a full amplitude apart. On `road_major` the drift is 1.1 render
    #: pixels either way against a bristle spacing of 0.34, so the tip does not
    #: lay a band, it collapses into four or five coincident filaments with
    #: nearly bare paper between them, and because the phases do not change
    #: along the stroke those gaps run its entire length. Measured on one
    #: stroke's accumulator, the deepest hole across the tip against the mark's
    #: own envelope: 0.24 at coherence 0, which is a bristle's worth of almost
    #: nothing in the middle of a road, against 0.61 at 0.25 and 0.92 once the
    #: weights are bandlimited too, where a tip with no drift at all sits at
    #: 0.94. It is why `ink_ss` 3 made the streaking worse rather than better:
    #: the finer grid resolves the folded tip instead of averaging it away.
    #: Above 0.25 nothing more is bought, because the drift that is left is
    #: then smooth enough that the tip no longer crosses itself. On, it also
    #: turns on two things a drifting tip needs and cannot do without: the
    #: sampling widens to cover the room the drift asks for, and each sample
    #: carries the strip of tip it actually stands on rather than an equal
    #: share, so a bunch is no longer a dark filament. 0 draws the phases
    #: independently again, which is the old behaviour but not the old bytes:
    #: they now come off a normal draw rather than a uniform one, so the tip is
    #: a different pattern of the same kind.
    bristle_drift_coherence: float = 0.25

    @classmethod
    def from_style(cls, style: Any) -> PaintStyle:
        """Build a paint style from a `ChartStyle`'s `paint` block.

        A key the block does not carry keeps the default here, so adding a
        field does not oblige every theme to restate it.

        Args:
            style: The chart style, whose `paint` mapping holds the overrides.

        Returns:
            The paint style this theme asks for.

        Raises:
            ValueError: When the block names a field that does not exist.
        """
        out = cls()
        known = {spec.name for spec in fields(cls)}
        for key, value in (getattr(style, "paint", None) or {}).items():
            if key not in known:
                raise ValueError(f"paint block has unknown key {key!r}")
            current = getattr(out, key)
            if isinstance(current, tuple) and isinstance(value, list):
                value = tuple(value)
            elif isinstance(current, dict) and isinstance(value, dict):
                value = {**current, **value}
            setattr(out, key, value)
        return out

    @classmethod
    def from_resolved(cls, resolved: dict[str, Any]) -> PaintStyle:
        """Build a paint style from a resolved, JSON-loaded field mapping.

        Each value takes the type of the same field on a default instance, so a
        JSON list becomes a tuple wherever the field is one.

        Args:
            resolved: Field name to value, as `dataclasses.asdict` writes it.

        Returns:
            The paint style the mapping describes.

        Raises:
            ValueError: When the mapping names a field that does not exist.
        """
        out = cls()
        known = {spec.name for spec in fields(cls)}
        for name, value in resolved.items():
            if name not in known:
                raise ValueError(f"resolved paint style has unknown key {name!r}")
            setattr(out, name, coerce_like(getattr(out, name), value))
        return out

    def digest(self) -> str:
        """A short hash of every field, so a changed style repaints."""
        blob = json.dumps(asdict(self), sort_keys=True, default=str)
        return hashlib.sha256(blob.encode()).hexdigest()[:16]


# --------------------------------------------------------------------------- colour


def rgb(hex_s: str) -> np.ndarray:
    """One hex colour as three floats in 0 to 1."""
    h = hex_s.lstrip("#")
    return np.array([int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)], F32)


# --------------------------------------------------------------------------- noise


def value_noise(h: int, w: int, cell: float, rng: np.random.Generator) -> np.ndarray:
    """Smooth value noise on a grid of `cell` pixels."""
    cell = max(cell, 1.0)
    gh, gw = int(h / cell) + 3, int(w / cell) + 3
    g = rng.random((gh, gw)).astype(F32)
    ys = np.arange(h, dtype=F32) / cell
    xs = np.arange(w, dtype=F32) / cell
    y0 = np.floor(ys).astype(np.int32)
    x0 = np.floor(xs).astype(np.int32)
    fy = ys - y0
    fx = xs - x0
    fy = (fy * fy * (3 - 2 * fy))[:, None]
    fx = fx * fx * (3 - 2 * fx)
    a = g[y0][:, x0]
    b = g[y0][:, x0 + 1]
    c = g[y0 + 1][:, x0]
    d = g[y0 + 1][:, x0 + 1]
    top = a + (b - a) * fx
    bot = c + (d - c) * fx
    return top + (bot - top) * fy


def fbm(h: int, w: int, cell: float, octaves: int, rng: np.random.Generator) -> np.ndarray:
    """Fractal noise, normalised to 0 to 1."""
    out = np.zeros((h, w), F32)
    amp, total = 1.0, 0.0
    for i in range(octaves):
        out += amp * value_noise(h, w, cell / (2**i), rng)
        total += amp
        amp *= 0.5
    out /= total
    lo, hi = float(out.min()), float(out.max())
    return (out - lo) / max(hi - lo, 1e-6)


def _value_noise_at(
    u: np.ndarray, v: np.ndarray, cell: float, rng: np.random.Generator
) -> np.ndarray:
    """Smooth value noise sampled at arbitrary coordinates rather than a grid.

    `value_noise` walks the pixel grid, so it can only make an isotropic field.
    This takes the coordinates it is given, which is what lets a caller squash
    or rotate them first.

    Args:
        u: Column coordinate per pixel, in the same units as `cell`.
        v: Row coordinate per pixel.
        cell: The lattice spacing.
        rng: The generator the lattice is drawn from.

    Returns:
        The field, in 0 to 1, with the shape of `u`.
    """
    cell = max(cell, 1.0)
    us, vs = u / cell, v / cell
    u0f, v0f = np.floor(us), np.floor(vs)
    umin, vmin = float(u0f.min()), float(v0f.min())
    gw = int(u0f.max() - umin) + 3
    gh = int(v0f.max() - vmin) + 3
    g = rng.random((gh, gw)).astype(F32)
    ix = (u0f - umin).astype(np.int32)
    iy = (v0f - vmin).astype(np.int32)
    fx = (us - u0f).astype(F32)
    fy = (vs - v0f).astype(F32)
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    a = g[iy, ix]
    b = g[iy, ix + 1]
    c = g[iy + 1, ix]
    d = g[iy + 1, ix + 1]
    top = a + (b - a) * fx
    bot = c + (d - c) * fx
    return top + (bot - top) * fy


def fbm_aniso(
    h: int,
    w: int,
    cell: float,
    octaves: int,
    rng: np.random.Generator,
    stretch: float,
    angle: float,
) -> np.ndarray:
    """Fractal noise stretched along one axis: a laid fibre, not concrete.

    Cold-press paper has a direction. Squashing one axis of the sampling
    coordinates by `stretch` before the lattice is read gives a field whose
    features are that many times longer than they are wide, all lying at the
    same sheet-wide angle.

    Args:
        h: Rows.
        w: Columns.
        cell: The coarsest lattice spacing, across the fibre.
        octaves: How many halvings to sum.
        rng: The generator the lattice is drawn from.
        stretch: How much longer than wide a fibre is.
        angle: The grain's angle in radians.

    Returns:
        The field, normalised to 0 to 1.
    """
    yy = np.arange(h, dtype=F32)[:, None]
    xx = np.arange(w, dtype=F32)[None, :]
    ca, sa = math.cos(angle), math.sin(angle)
    u = (xx * ca + yy * sa) / max(stretch, 1e-3)
    v = yy * ca - xx * sa
    out = np.zeros((h, w), F32)
    amp, total = 1.0, 0.0
    for i in range(octaves):
        out += amp * _value_noise_at(u, v, cell / (2**i), rng)
        total += amp
        amp *= 0.5
    out /= total
    lo, hi = float(out.min()), float(out.max())
    return (out - lo) / max(hi - lo, 1e-6)


def _box1(a: np.ndarray, r: int, axis: int) -> np.ndarray:
    """One box blur pass along one axis."""
    if r < 1:
        return a
    a = np.moveaxis(a, axis, -1)
    n = a.shape[-1]
    pad = np.pad(a, [(0, 0)] * (a.ndim - 1) + [(r + 1, r)], mode="edge")
    cs = np.cumsum(pad, axis=-1, dtype=F32)
    out = (cs[..., 2 * r + 1 :] - cs[..., :n]) / F32(2 * r + 1)
    return np.moveaxis(out, -1, axis)


def blur(a: np.ndarray, sigma: float) -> np.ndarray:
    """Three box passes, which is a Gaussian to the eye and much cheaper."""
    if sigma <= 0.4:
        return a.astype(F32, copy=False)
    r = max(1, int(round(sigma * 0.95)))
    out = a.astype(F32, copy=True)
    for _ in range(3):
        out = _box1(out, r, 1)
        out = _box1(out, r, 0)
    return out


def edt(mask: np.ndarray) -> np.ndarray:
    """Chamfer distance in pixels to the nearest True cell."""
    inf = F32(1e6)
    d = np.where(mask, F32(0), inf).astype(F32)
    if not mask.any():
        return d
    h, w = d.shape
    idx = np.arange(w, dtype=F32)
    dd, one = F32(1.41421356), F32(1.0)
    for r in range(h):
        row = d[r].copy()
        if r:
            p = d[r - 1]
            np.minimum(row, p + one, out=row)
            np.minimum(row[:-1], p[1:] + dd, out=row[:-1])
            np.minimum(row[1:], p[:-1] + dd, out=row[1:])
        np.minimum(row, np.minimum.accumulate(row - idx) + idx, out=row)
        d[r] = row
    for r in range(h - 1, -1, -1):
        row = d[r].copy()
        if r < h - 1:
            p = d[r + 1]
            np.minimum(row, p + one, out=row)
            np.minimum(row[:-1], p[1:] + dd, out=row[:-1])
            np.minimum(row[1:], p[:-1] + dd, out=row[1:])
        rev = row[::-1].copy()
        np.minimum(rev, np.minimum.accumulate(rev - idx) + idx, out=rev)
        d[r] = rev[::-1]
    return d


def smoothstep(x: np.ndarray, w: float) -> np.ndarray:
    """A soft step of width `w` about zero."""
    t = np.clip(x / w + 0.5, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def fill_holes(mask: np.ndarray, step: int = 6) -> np.ndarray:
    """Fill anything the outside cannot reach: the inside of a loop is land.

    Done on a coarse copy, because the flood is a propagation and the answer is
    a shape, not a pixel.

    Args:
        mask: The dilated track.
        step: Coarsening factor for the flood.

    Returns:
        The mask with its enclosed holes filled.
    """
    small = mask[::step, ::step]
    free = ~small
    reach = np.zeros_like(free)
    reach[0, :] |= free[0, :]
    reach[-1, :] |= free[-1, :]
    reach[:, 0] |= free[:, 0]
    reach[:, -1] |= free[:, -1]
    for i in range(4000):
        grown = reach.copy()
        grown[1:, :] |= reach[:-1, :]
        grown[:-1, :] |= reach[1:, :]
        grown[:, 1:] |= reach[:, :-1]
        grown[:, :-1] |= reach[:, 1:]
        grown &= free
        if i % 20 == 0 and np.array_equal(grown, reach):
            break
        if not grown.sum() > reach.sum():
            reach = grown
            break
        reach = grown
    holes = free & ~reach
    if not holes.any():
        return mask
    big = np.repeat(np.repeat(holes, step, 0), step, 1)[: mask.shape[0], : mask.shape[1]]
    if big.shape != mask.shape:
        pad = np.zeros_like(mask)
        pad[: big.shape[0], : big.shape[1]] = big
        big = pad
    return mask | big


# --------------------------------------------------------------------------- the plate


@dataclass
class Plate:
    """The card's metre box and the pixel grid it is painted on."""

    x0: float
    y0: float
    x1: float
    y1: float
    w: int
    h: int

    @property
    def scale(self) -> float:
        """Render pixels per metre."""
        return self.w / (self.x1 - self.x0)

    def px(self, pts: Any) -> np.ndarray:
        """Project metre points into render pixels, north up."""
        a = np.asarray(pts, dtype=np.float64)
        s = self.scale
        out = np.empty_like(a)
        out[:, 0] = (a[:, 0] - self.x0) * s
        out[:, 1] = (self.y1 - a[:, 1]) * s
        return out


@dataclass
class Sheet:
    """The paper's own noise fields, shared by every wash and every mark."""

    h: int
    w: int
    gran_px: float
    seed: int = 11
    #: Cold press. Above 0 a second noise field, stretched along one sheet-wide
    #: axis, is mixed into the tooth at this weight, so the paper reads as a
    #: laid fibre rather than as concrete. 0 is the isotropic sheet.
    fibre: float = 0.0
    fibre_stretch: float = 3.0
    fibre_angle: float = 0.42
    fibre_cell: float = 4.2
    paper: np.ndarray = field(init=False)
    coarse: np.ndarray = field(init=False)
    fine: np.ndarray = field(init=False)
    wet: np.ndarray = field(init=False)
    gran: np.ndarray = field(init=False)

    def __post_init__(self) -> None:
        """Build the five fields from one seeded generator."""
        rng = np.random.default_rng(self.seed)
        self.paper = np.clip(
            0.5 * fbm(self.h, self.w, 3.6, 3, rng) + 0.5 * fbm(self.h, self.w, 92.0, 3, rng), 0, 1
        )
        self.coarse = fbm(self.h, self.w, 74.0, 3, rng)
        self.fine = fbm(self.h, self.w, 5.0, 2, rng)
        self.wet = fbm(self.h, self.w, 130.0, 2, rng)
        self.gran = fbm(self.h, self.w, self.gran_px, 2, rng)
        if self.fibre > 0:
            # Drawn last, so a sheet with no fibre is the sheet it always was:
            # the five fields above have already taken their draws.
            grain = fbm_aniso(
                self.h, self.w, self.fibre_cell, 3, rng, self.fibre_stretch, self.fibre_angle
            )
            self.paper = np.clip((1.0 - self.fibre) * self.paper + self.fibre * grain, 0, 1)
        self._rng = rng

    def pits(self, gamma: float) -> np.ndarray:
        """How readily pigment settles, from the paper's own height.

        Granulation on real paper is deposition following the tooth: the
        hollows take the heavy pigment, and they are the same hollows a dry
        brush skips over. Taking it from `paper` rather than from an unrelated
        field is what ties the two together.

        Args:
            gamma: How sharply it follows. Above 1 a pigment has to reach a
                real hollow before it settles.

        Returns:
            A field about 0 to 1, high in the pits.
        """
        return np.clip(1.0 - self.paper, 0.0, 1.0) ** F32(max(gamma, 0.05))

    def noise(self, cell: float, octaves: int = 2) -> np.ndarray:
        """One more noise field at this scale."""
        return fbm(self.h, self.w, cell, octaves, self._rng)


def parse_d(d: str) -> list[list[Pt]]:
    """The point lists inside one `M x,y L x,y` path."""
    rings = []
    for chunk in d.split("M"):
        chunk = chunk.strip().rstrip("Z").strip()
        if not chunk:
            continue
        pts = []
        for tok in chunk.replace("L", " ").split():
            if "," in tok:
                a, b = tok.split(",")
                pts.append((float(a), float(b)))
        if len(pts) > 1:
            rings.append(pts)
    return rings


def _edge(acc: np.ndarray, x0: float, y0: float, x1: float, y1: float, hs: int, ws: int) -> None:
    """Add one polygon edge's winding contribution to a scanline accumulator."""
    if y0 == y1:
        return
    d = 1
    if y1 < y0:
        x0, y0, x1, y1 = x1, y1, x0, y0
        d = -1
    r0 = max(int(math.ceil(y0 - 0.5)), 0)
    r1 = min(int(math.ceil(y1 - 0.5)), hs)
    if r1 <= r0:
        return
    rr = np.arange(r0, r1)
    xx = x0 + (rr + 0.5 - y0) * (x1 - x0) / (y1 - y0)
    cc = np.clip(np.ceil(xx - 0.5).astype(np.int32), 0, ws + 1)
    np.add.at(acc, (rr, cc), d)


#: What one class's outlines are deformed by: the generator, the first round's
#: variance as a share of a segment, the rounds, what each round hands its
#: children, the ceiling on one displacement and the segment length to stop at,
#: both in the rings' own metres.
Deform = tuple[np.random.Generator, float, int, float, float, float]


def deform_ring(
    ring: Any,
    rng: np.random.Generator,
    amount: float,
    depth: int,
    decay: float,
    cap: float,
    min_seg: float,
) -> np.ndarray:
    """Recursive midpoint displacement of one closed outline.

    Hobbs' construction: each segment carries its own variance, is split at a
    midpoint pushed off the line by that variance times its own length, and
    hands each half a decayed and separately randomised share of it. Carrying
    the variance per segment rather than per round is the whole point. A single
    global amplitude gives an outline that wobbles at one frequency everywhere,
    which is what the blurred-mask edge already does; per-segment variance is
    what makes one stretch of a wood loose and the next stretch tight.

    Args:
        ring: The outline, in the rings' own metre coordinates.
        rng: The generator the displacements are drawn from.
        amount: The first round's variance, as a share of a segment's length.
        depth: How many rounds. Each doubles the point count.
        decay: What each round hands its children, before the randomisation.
        cap: The largest one displacement may be, in metres.
        min_seg: Stop once the typical segment is shorter than this.

    Returns:
        The deformed ring, `(n, 2)`.
    """
    p = np.asarray(ring, dtype=np.float64)
    if p.ndim != 2 or len(p) < 3:
        return p
    var = np.full(len(p), max(amount, 0.0))
    for _ in range(max(int(depth), 0)):
        n = len(p)
        if n > 24000:
            break
        q = np.roll(p, -1, axis=0)
        d = q - p
        seg = np.hypot(d[:, 0], d[:, 1])
        if float(np.median(seg)) < min_seg:
            break
        ln = np.maximum(seg, 1e-9)
        off = np.clip(rng.normal(0.0, 1.0, n) * var * seg, -cap, cap)
        mid = 0.5 * (p + q)
        mid[:, 0] -= d[:, 1] / ln * off
        mid[:, 1] += d[:, 0] / ln * off
        out = np.empty((2 * n, 2))
        out[0::2] = p
        out[1::2] = mid
        p = out
        var = np.repeat(var, 2) * decay * rng.uniform(0.75, 1.25, 2 * n)
    return p


def deform_rings(rings: list[list[Pt]], deform: Deform | None) -> list[Any]:
    """Every outline of one class deformed, or the outlines unchanged.

    Args:
        rings: The class's outlines, in metres.
        deform: The settings, or None to leave them exactly as they are.

    Returns:
        The rings, deformed or the same objects.
    """
    if deform is None:
        return rings
    return [deform_ring(r, *deform) for r in rings]


def fill_cov(rings: list[list[Pt]], plate: Plate, ss: int = 2) -> np.ndarray:
    """Coverage of a set of rings, supersampled and averaged down."""
    hs, ws = plate.h * ss, plate.w * ss
    acc = np.zeros((hs, ws + 2), np.int16)
    for ring in rings:
        if len(ring) < 3:
            continue
        p = plate.px(ring) * ss
        xs, ys = p[:, 0], p[:, 1]
        for a, b, c, d in zip(xs, ys, np.roll(xs, -1), np.roll(ys, -1), strict=True):
            _edge(acc, a, b, c, d, hs, ws)
    inside = np.cumsum(acc, axis=1, dtype=np.int32)[:, :ws] != 0
    return inside.reshape(plate.h, ss, plate.w, ss).mean(axis=(1, 3), dtype=F32)


def stroke_mask(lines: list[list[Pt]], plate: Plate, width_px: float) -> np.ndarray:
    """A binary mask of polylines stroked at a fixed width."""
    hits = np.zeros((plate.h, plate.w), bool)
    for pts in lines:
        p = plate.px(pts)
        seg = np.hypot(np.diff(p[:, 0]), np.diff(p[:, 1]))
        total = float(seg.sum())
        if total < 1:
            continue
        cum = np.concatenate([[0.0], np.cumsum(seg)])
        t = np.linspace(0, total, max(int(total / 0.6), 2))
        ix = np.clip(np.round(np.interp(t, cum, p[:, 0])).astype(np.int32), 0, plate.w - 1)
        iy = np.clip(np.round(np.interp(t, cum, p[:, 1])).astype(np.int32), 0, plate.h - 1)
        hits[iy, ix] = True
    if width_px <= 1:
        return hits
    return edt(hits) < width_px * 0.5


# --------------------------------------------------------------------------- washes


def flow_edge(
    a: np.ndarray, sheet: Sheet, rim_px: float, exp: float, ref_frac: float, frac: float = 0.38
) -> np.ndarray:
    """Edge darkening as an outward flow term, decaying inward from the edge.

    Mask minus blur is symmetric about the geometric edge and one width
    everywhere. Real edge darkening is pigment carried out by evaporation at a
    pinned contact line, so it sits inside the wet boundary and is wider on a
    large wash than on a small one. Coarse noise then breaks it up, because a
    contact line does not pin evenly.

    Args:
        a: The wash's own alpha, in 0 to 1.
        sheet: The paper's noise fields.
        rim_px: The rim's width at the reference area.
        exp: How fast the width grows with area.
        ref_frac: The reference area, as a share of the sheet.
        frac: The decay length as a share of `rim_px`.

    Returns:
        The rim, in 0 to 1.
    """
    inside = a > 0.5
    area = float(inside.sum())
    if area < 4:
        return np.zeros_like(a)
    ref = max(a.size * ref_frac, 1.0)
    width = max(rim_px * frac * (area / ref) ** exp, 0.8)
    d = edt(~inside)
    rim = np.exp(-d / F32(width)) * a * (0.6 + 0.8 * sheet.coarse)
    return np.clip(rim, 0.0, 1.0)


def bloom(
    dens: np.ndarray,
    a: np.ndarray,
    sheet: Sheet,
    rng: np.random.Generator,
    count: int,
    radius_frac: float,
    lift: float,
    warp: float,
) -> None:
    """Backruns, as a re-wet event with no solver. Modifies `dens` in place.

    A backrun is a second front of liquid pushing already-deposited pigment out
    ahead of it: the centre goes lighter than the wash around it and the front
    dries as a dark crenellated ridge. Seeded where the wash is thick, grown
    outward, and warped off a circle by fractal noise, which is what makes the
    ridge read as a cauliflower rather than a halo. Cropped to the bloom's own
    box, so the cost does not scale with the plate.

    Args:
        dens: The wash's density, changed in place.
        a: The wash's alpha, so a bloom stops at the wash's edge.
        sheet: The paper's noise fields.
        rng: The generator the seeds and the warp are drawn from.
        count: How many blooms to lay.
        radius_frac: Radius as a share of the root of the wash's area.
        lift: How much pigment the front takes out of the centre.
        warp: How far the fbm pushes the front off a circle.
    """
    inside = np.flatnonzero((a > 0.6).ravel())
    if count < 1 or inside.size < 64:
        return
    h, w = dens.shape
    radius = float(np.clip(radius_frac * math.sqrt(inside.size), 5.0, 0.22 * min(h, w)))
    flat = dens.ravel()
    for _ in range(count):
        # Seeded toward the thick: a handful of candidates, the wettest wins.
        cand = rng.choice(inside, size=min(24, inside.size), replace=False)
        cy, cx = divmod(int(cand[int(np.argmax(flat[cand]))]), w)
        r = radius * float(rng.uniform(0.7, 1.3))
        span = int(r * 1.9) + 3
        y0, y1 = max(cy - span, 0), min(cy + span + 1, h)
        x0, x1 = max(cx - span, 0), min(cx + span + 1, w)
        if y1 - y0 < 5 or x1 - x0 < 5:
            continue
        bh, bw = y1 - y0, x1 - x0
        yy = (np.arange(y0, y1, dtype=F32) - cy)[:, None]
        xx = (np.arange(x0, x1, dtype=F32) - cx)[None, :]
        d = np.hypot(yy, xx) + warp * (fbm(bh, bw, r * 0.55, 3, rng) - 0.5) * r
        front = np.exp(-(((d - r) / F32(max(r * 0.09, 1.6))) ** 2))
        box_a = a[y0:y1, x0:x1]
        box = dens[y0:y1, x0:x1]
        core = (d < r) * box_a
        held = float(box[core > 0.5].mean()) if (core > 0.5).any() else 0.0
        box *= 1.0 - lift * core
        box += held * lift * 1.5 * front * box_a
        np.clip(box, 0.0, 1.0, out=box)


def wash(
    cover: np.ndarray,
    sheet: Sheet,
    base: float,
    pool: float,
    wobble: float = 3.6,
    dry: float = 1.8,
    rim_px: float = 7.0,
    gran: float = 0.26,
    uneven: float = 0.22,
    tooth: float = 0.34,
    wet: np.ndarray | None = None,
    bleed_px: float = 5.0,
    bleed_mix: float = 0.55,
    rim_drop: float = 0.7,
    gran_gamma: float = 0.0,
    flow: tuple[float, float, float] | None = None,
    blooms: tuple[np.random.Generator, int, float, float, float] | None = None,
) -> np.ndarray:
    """One pigment's density from a coverage mask.

    The edge is the blurred mask thresholded against two noise scales, which is
    cheaper than a signed distance field and, at this resolution, the same
    picture. Pooling is the mask minus its own blur, so pigment sits just inside
    the edge instead of fading out of it.

    Everything from `wet` on is a phase 1 option and is inert when it is not
    given, so a caller that passes none of it paints the wash it always did.

    Args:
        cover: Coverage in 0 to 1.
        sheet: The paper's noise fields.
        base: Density of the flat body of the wash.
        pool: Extra density where the pigment pools at the edge.
        wobble: Coarse noise on the edge, in mask units.
        dry: Fine noise on the edge.
        rim_px: Width of the pooled edge, in render pixels.
        gran: Granulation, as a share of the body density.
        uneven: Slow variation across the wash.
        tooth: How much the paper's tooth lightens it.
        wet: The shared wet-area map, when there is one. Inside it this wash
            bleeds into whatever is beside it and gives up most of its rim,
            because a class boundary under water is not an edge.
        bleed_px: How far the bleed carries, in render pixels.
        bleed_mix: How much of the bleed is taken, at the centre of a wet area.
        rim_drop: How much of the rim the wet area removes.
        gran_gamma: Above 0, granulation follows the paper's own pits at this
            gamma rather than the unrelated `sheet.gran` field.
        flow: `(exp, ref_frac, frac)` to take the rim from `flow_edge` instead.
        blooms: `(rng, count, radius_frac, lift, warp)` to lay backruns.

    Returns:
        Density in 0 to 1.
    """
    if not cover.any():
        return np.zeros_like(cover)
    soft = blur(cover, 2.4)
    edge = (wobble * (sheet.coarse - 0.5) + dry * (sheet.fine - 0.5)) * 0.06
    a = np.clip((soft - 0.5 + edge) * 3.2 + 0.5, 0.0, 1.0)
    if flow is not None:
        rim = flow_edge(a, sheet, rim_px, flow[0], flow[1], flow[2])
    else:
        rim = np.clip(a - blur(a, rim_px), 0.0, 1.0)
    peak = float(rim.max())
    if peak > 1e-5:
        rim = rim / peak
    if wet is not None:
        rim = rim * (1.0 - wet * rim_drop)
    dens = a * base + rim * pool
    dens *= 1.0 + uneven * (sheet.wet - 0.5) * 2.0
    if gran_gamma > 0:
        pits = sheet.pits(gran_gamma)
        dens *= 1.0 + gran * (pits - float(pits.mean())) * 2.4
    else:
        dens *= 1.0 + gran * np.clip((sheet.gran - 0.5) * 2.4, -0.7, 1.0)
    dens *= 1.0 - tooth * (sheet.paper - 0.5)
    if wet is not None and bleed_px > 0.4:
        m_wet = wet * bleed_mix
        dens = dens * (1.0 - m_wet) + blur(dens, bleed_px) * m_wet
    if blooms is not None:
        bloom(dens, a, sheet, blooms[0], int(blooms[1]), blooms[2], blooms[3], blooms[4])
    b1 = blur(dens, 1.6)
    b2 = blur(dens, 4.4)
    m = sheet.wet
    lo = np.clip(m * 2.0, 0, 1)
    hi = np.clip(m * 2.0 - 1.0, 0, 1)
    return np.clip(dens * (1 - lo) + b1 * (lo - hi) + b2 * hi, 0.0, 1.0)


def separated(
    dens: np.ndarray,
    key: str,
    pig: np.ndarray,
    transparency: float,
    sheet: Sheet,
    style: PaintStyle,
) -> list[Layer]:
    """One wash as one pigment, or as the two it is really mixed from.

    A tube green is a staining green with a heavier blue-black in it, and the
    two come apart as the wash dries: the heavy one drops into the paper's
    hollows and the light one floats over the tooth. Curtis' pigment
    separation, taken as one extra layer rather than a second solver. The total
    density is what it was, because the heavy field is normalised to a mean of
    one before its share is taken out of the light one: the flag redistributes
    a wash, it does not add to it.

    The pair only reads as two pigments through `km_glazing`. Under multiply
    the layers still stack, but the two hues average where they overlap, which
    is exactly what glazing was brought in to stop.

    Args:
        dens: The wash's density.
        key: The land class, which is what decides whether it separates.
        pig: The pigment over white.
        transparency: What that pigment shows over black, as a share.
        sheet: The paper's noise fields, for the pits the heavy one settles in.
        style: The paint style.

    Returns:
        One layer, or the light one and then the heavy one over it.
    """
    hex2 = style.separation_pigments.get(key) if style.pigment_separation else None
    if not hex2:
        return [(dens, pig, transparency)]
    share = float(np.clip(style.separation_share, 0.0, 0.9))
    heavy = dens * sheet.pits(style.separation_gamma)
    # Scaled against this wash's own pigment rather than against the sheet's
    # mean tooth, so the heavy pigment is exactly the share of the wash it is
    # said to be wherever the wash happens to lie. The pits say where it goes,
    # not how much of it there is.
    total = float(heavy.sum())
    if total < 1e-9:
        return [(dens, pig, transparency)]
    heavy = heavy * F32(share * float(dens.sum()) / total)
    return [
        (dens * F32(1.0 - share), pig, transparency),
        (np.clip(heavy, 0.0, 1.0), rgb(hex2), float(style.separation_transparency)),
    ]


def shallow_water(
    wet: np.ndarray,
    pig: np.ndarray,
    paper: np.ndarray,
    steps: int,
    relax: int,
    seed: int,
    gran: float,
) -> np.ndarray:
    """Curtis' shallow water layer, cut down to a bounded number of steps.

    Velocities come from the pressure gradient, `RelaxDivergence` hands each
    cell's divergence to its two neighbours a fixed number of times, the
    outward flow lifts the pressure at the wet boundary, and what settles
    follows the paper's own height. Pigment moves as a flux between cells
    rather than by sampling, which is what lets it pile up against a contact
    line the water cannot cross: that pile is the edge darkening.

    Every count here is a count and not a tolerance. A convergence test would
    make the number of iterations depend on the arithmetic, and the plate would
    stop being reproducible from its seed.

    Args:
        wet: The wet area on this grid, in 0 to 1.
        pig: Pigment in suspension at the start, in 0 to 1.
        paper: The paper's height on this grid, in 0 to 1.
        steps: How many steps to run.
        relax: Relaxation iterations inside one step.
        seed: The generator's seed, for the water's own unevenness.
        gran: How much the settling follows the paper's height.

    Returns:
        What has been deposited, normalised to 0 to 1.
    """
    h, w = wet.shape
    rng = np.random.default_rng(seed)
    hgt = (wet * (0.85 + 0.30 * rng.random((h, w)))).astype(F32)
    u = np.zeros((h, w), F32)
    v = np.zeros((h, w), F32)
    g = (pig * wet).astype(F32)
    dep = np.zeros((h, w), F32)
    tooth = (paper - float(paper.mean())).astype(F32)
    mask = (wet > 0.05).astype(F32)
    edge = np.clip(mask - blur(mask, 3.0), 0.0, 1.0)
    hold = (F32(0.05) * (1.0 + gran * (0.5 - paper) * 2.0)).astype(F32)
    #: Where pigment may pass: nothing crosses the edge of the wet area.
    wall_x = (mask * np.roll(mask, -1, 1)).astype(F32)
    wall_y = (mask * np.roll(mask, -1, 0)).astype(F32)

    def dx(a: np.ndarray) -> np.ndarray:
        return np.roll(a, -1, 1) - a

    def dy(a: np.ndarray) -> np.ndarray:
        return np.roll(a, -1, 0) - a

    for _ in range(max(int(steps), 0)):
        p = hgt + F32(0.40) * tooth
        u = (u - F32(0.35) * dx(p)) * F32(0.94) * mask
        v = (v - F32(0.35) * dy(p)) * F32(0.94) * mask
        for _ in range(max(int(relax), 0)):
            d = (F32(0.1) * (dx(u) + dy(v))).astype(F32)
            hgt += d
            u += d - np.roll(d, 1, 1)
            v += d - np.roll(d, 1, 0)
            u *= mask
            v *= mask
        np.clip(u, -0.45, 0.45, out=u)
        np.clip(v, -0.45, 0.45, out=v)
        hgt = np.maximum(hgt - F32(0.03) * edge, 0.0) * mask
        # Pigment moves as a flux between cells, upwind, and no flux crosses
        # the wet boundary. Advecting it by sampling instead would carry it
        # about without ever piling it up, and piling it up against a contact
        # line the water cannot cross is exactly what edge darkening is.
        fx = np.where(u > 0, g, np.roll(g, -1, 1)) * u * wall_x
        g = g - fx + np.roll(fx, 1, 1)
        fy = np.where(v > 0, g, np.roll(g, -1, 0)) * v * wall_y
        g = g - fy + np.roll(fy, 1, 0)
        settle = g * hold
        dep += settle
        g -= settle
    top = float(dep.max())
    return (dep / top).astype(F32) if top > 1e-6 else dep


def fluid_modulate(
    layers: list[Layer], wet: np.ndarray, sheet: Sheet, style: PaintStyle
) -> list[Layer]:
    """Modulate a stack of washes by one coarse shallow-water pass.

    The rule this holds to is that the pass modulates the painter and never
    becomes it: the water is run on a grid a quarter of the plate's size,
    against the densities the painter has already laid, and what comes back
    multiplies them. A pass that produced nothing leaves the plate it was given.

    The densities are modulated in place, because they were built for this
    stack a few lines earlier and nothing else holds them: a plate carrying
    fourteen layers cannot afford a second copy of every one.

    Args:
        layers: The washes to modulate. Their densities are changed in place.
        wet: The wet area at plate resolution, in 0 to 1.
        sheet: The paper's noise fields.
        style: The paint style.

    Returns:
        The same layers, for a caller that would rather read it that way.
    """
    q = max(int(style.fluid_grid), 1)
    h, w = wet.shape
    qh, qw = max(h // q, 8), max(w // q, 8)

    def down(a: np.ndarray) -> np.ndarray:
        return a[: qh * q, : qw * q].reshape(qh, q, qw, q).mean(axis=(1, 3), dtype=F32)

    wet_q = down(wet)
    if not (wet_q > 0.05).any():
        return layers
    total = np.zeros((h, w), F32)
    for layer in layers:
        if layer[0] is not None:
            total += layer[0]
    dep = shallow_water(
        wet_q,
        np.clip(down(total), 0.0, 1.0),
        down(sheet.paper),
        style.fluid_steps,
        style.fluid_relax,
        style.fluid_seed,
        style.fluid_gran,
    )
    # Read against its own middle and its own spread inside the wash, not
    # against its maximum: a deposit field piles up hard in a few cells, and
    # scaling by the largest of them would leave every other cell untouched.
    seen = dep[wet_q > 0.05]
    lo, mid, hi = (float(v) for v in np.percentile(seen, [10, 50, 90]))
    gain_q = 1.0 + style.fluid_amount * np.clip((dep - mid) / max(hi - lo, 1e-6), -1.5, 1.5)
    # The whole gain is built on the coarse grid, the fade out to dry paper
    # included, and brought back up bilinearly in one step. Anything done at
    # plate resolution here costs more than the pass that earned it: a single
    # blur over 1800 by 1529 is a fifth of the solver.
    gain_q = gain_q * wet_q + (1.0 - wet_q)
    gain = np.asarray(Image.fromarray(gain_q.astype(F32), "F").resize((w, h), Image.BILINEAR), F32)
    for layer in layers:
        if layer[0] is not None:
            np.multiply(layer[0], gain, out=layer[0])
            np.clip(layer[0], 0.0, 1.0, out=layer[0])
    return layers


def multiply_plate(layers: list[Layer], h: int, w: int) -> np.ndarray:
    """Stack densities into one white-backed multiply plate."""
    out = np.ones((h, w, 3), F32)
    for layer in layers:
        dens, pig = layer[0], layer[1]
        if dens is None or not dens.any():
            continue
        out *= 1.0 - dens[..., None] * (1.0 - pig)
    return np.clip(out, 0.0, 1.0)


def km_rt(dens: np.ndarray, pig: np.ndarray, transparency: float) -> tuple[np.ndarray, np.ndarray]:
    """One wash's reflectance and transmittance, per Kubelka-Munk.

    The pigment hex the painter already carries is Rw, what a unit wash of it
    shows over white. The one number this needs beyond that is Rb, what the
    same wash shows over black, which is what says whether the pigment stains
    or covers. K and S follow from the pair, and the painter's own density is
    the layer's thickness.

    The step that is easy to miss is deriving S from Rw and Rb rather than
    picking it: without it the round trip does not return Rw and every wash
    goes black.

    Args:
        dens: Layer thickness, the wash's density in 0 to 1.
        pig: The pigment over white, three channels in 0 to 1.
        transparency: Rb over Rw. Near 0 the pigment is a transparent glaze
            that lets the layer under it through; near 1 it covers.

    Returns:
        Reflectance and transmittance, each `dens.shape + (3,)`.
    """
    rw = np.clip(pig, 1e-3, 0.999).astype(np.float64)
    rb = np.clip(rw * float(np.clip(transparency, 1e-3, 0.95)), 1e-4, rw - 1e-4)
    a = 0.5 * (rw + (rb - rw + 1.0) / rb)
    b = np.sqrt(np.maximum(a * a - 1.0, 1e-9))
    z = (b * b - (a - rw) * (a - 1.0)) / (b * (1.0 - rw))
    s = (1.0 / b) * 0.5 * np.log((z + 1.0) / (z - 1.0))
    # a, b and S are three numbers a channel; only the thickness is a plate, so
    # the hyperbolics run in float32 and the plate stays half the size.
    x = np.clip(dens, 0.0, 1.0).astype(F32)[..., None]
    bsx = np.clip((b * s).astype(F32)[None, None, :] * x, 0.0, 40.0)
    sh, ch = np.sinh(bsx), np.cosh(bsx)
    af = a.astype(F32)[None, None, :]
    bf = b.astype(F32)[None, None, :]
    c = np.maximum(af * sh + bf * ch, F32(1e-9))
    return sh / c, bf / c


def km_plate(layers: list[Layer], base: np.ndarray, transparency: float = 0.06) -> np.ndarray:
    """Glaze the layers optically over a backing, bottom layer first.

    Multiply is transmission with no scattering, so two washes crossing lose
    their chroma and go grey. Kubelka-Munk keeps the scattering, so a green
    over a blue is still green over blue where they meet.

    Args:
        layers: Density, pigment, and optionally the pigment's transparency.
        base: What the stack is laid over, `(h, w, 3)`.
        transparency: The default, for a layer that does not name one.

    Returns:
        The glazed plate, in 0 to 1.
    """
    out = base.astype(F32, copy=True)
    for layer in layers:
        dens, pig = layer[0], layer[1]
        if dens is None or not dens.any():
            continue
        t = float(layer[2]) if len(layer) > 2 else transparency
        r, tr = km_rt(dens, pig, t)
        out = r + tr * tr * out / np.maximum(1.0 - r * out, 1e-6)
    return np.clip(out, 0.0, 1.0)


def composite(layers: list[Layer], base: np.ndarray, style: PaintStyle) -> np.ndarray:
    """Stack one set of layers over a backing, the way the style asks.

    Args:
        layers: Density, pigment, and optionally a transparency.
        base: What the stack is laid over, `(h, w, 3)`.
        style: The paint style, for `km_glazing`.

    Returns:
        The composited plate.
    """
    if style.km_glazing:
        return km_plate(layers, base, style.km_transparency)
    h, w = base.shape[:2]
    return np.clip(base * multiply_plate(layers, h, w), 0.0, 1.0)


def relief_density(grid: ElevationPatch, plate: Plate, sheet: Sheet) -> np.ndarray:
    """A quiet shaded relief from the SRTM grid, in pigment density."""
    n = grid.n
    v = np.asarray(grid.values, F32).reshape(n, n)
    gx = (
        (np.arange(plate.w, dtype=F32) / plate.scale + plate.x0 - grid.x0)
        / (grid.x1 - grid.x0)
        * (n - 1)
    )
    gy = (
        (plate.y1 - np.arange(plate.h, dtype=F32) / plate.scale - grid.y0)
        / (grid.y1 - grid.y0)
        * (n - 1)
    )
    gx = np.clip(gx, 0, n - 1.001)
    gy = np.clip(gy, 0, n - 1.001)
    x0 = gx.astype(np.int32)
    y0 = gy.astype(np.int32)
    fx = (gx - x0)[None, :]
    fy = (gy - y0)[:, None]
    a, b = v[y0][:, x0], v[y0][:, x0 + 1]
    c, d = v[y0 + 1][:, x0], v[y0 + 1][:, x0 + 1]
    z = (a + (b - a) * fx) * (1 - fy) + (c + (d - c) * fx) * fy
    z = blur(z, 3.0)
    mpp = 1.0 / plate.scale
    gyd, gxd = np.gradient(z, mpp)
    shade = np.clip((-0.6 * gxd + 0.6 * gyd + 0.55) / 1.2, 0.0, 1.0)
    dens = np.clip(0.30 * (1.0 - shade), 0.0, 0.40)
    dens *= 1.0 + 0.24 * np.clip((sheet.gran - 0.5) * 2.2, -0.7, 1.0)
    dens *= 1.0 - 0.30 * (sheet.paper - 0.5)
    return np.clip(blur(dens, 2.0), 0.0, 1.0)


# --------------------------------------------------------------------------- brushes


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
    # --- phase 1: the reservoir and the directional break. All inert at these
    # defaults, so a brush built without the flags is the brush that was there.
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
    # --- phase 2: brush quality. Inert at these defaults, so a brush built
    # without the flags is the brush that was there.
    organic: bool = False  # drift and pressure from a lattice, not a sine
    org_oct: int = 4
    org_lac: float = 2.17
    org_mult: float = 0.5  # lattice cell, as a share of the sine's wavelength
    smooth: float = 0.0  # corner radius in render pixels; 0 leaves the path
    #: Pixels of the brush's own grid per render pixel. 1 is the plate itself;
    #: `scaled_brush` sets it when the ink is painted on a finer grid, so the
    #: wavelengths written into the code below stay the lengths they were.
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
    brush_id: str, width_display_px: float, scale: float, style: PaintStyle, override: str = ""
) -> tuple[Brush, str]:
    """One class's brush and ink colour, from a brush sheet id.

    Args:
        brush_id: A cell on the brush sheet, `RIV1-a` or `TRK4-d`.
        width_display_px: The width this class is painted at on screen.
        scale: Render pixels per display pixel.
        style: The paint style, for the shared geometry and the overrides.
        override: Key into `style.brush_overrides`, when the class has one.

    Returns:
        The brush in render pixels, and its ink colour as hex.

    Raises:
        ValueError: When the id names a row or a colour that does not exist.
    """
    cls, rest = brush_id[:3], brush_id[3:]
    row, _, col = rest.partition("-")
    if row not in BRUSH_TREATMENTS or col not in BRUSH_COLOURS.get(cls, {}):
        raise ValueError(f"no such brush {brush_id!r}")
    t = dict(BRUSH_TREATMENTS[row])
    t.pop("name_wet", None)
    over = style.brush_overrides.get(override or cls.lower(), {})
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
    # The reservoir. A brush breaks when it runs down and a nib thins, so the
    # two flags are separate and a brush never takes the nib's treatment.
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
    return brush, BRUSH_COLOURS[cls][col]


def plate_brushes(
    style: PaintStyle, scale: float, wet_px: dict[str, float]
) -> dict[str, tuple[Brush, str]]:
    """Every class's brush for one plate, sized against its own display pixel.

    Args:
        style: The paint style.
        scale: Render pixels per display pixel.
        wet_px: Painted width in display pixels per watercourse class, from the
            river importance curve.

    Returns:
        Brush and ink colour by class key.
    """
    mult = style.river_mult
    widths = {
        "major": wet_px.get("major", 8.4) * mult,
        "medium": wet_px.get("medium", 5.5) * mult,
        "minor": wet_px.get("minor", 2.2) * mult,
        "coast": wet_px.get("medium", 5.5) * mult * style.coast_width_frac,
        "road_major": style.brush_width_px["road_major"],
        "lane": style.brush_width_px["lane"],
        "track": style.brush_width_px["track"],
    }
    return {
        key: brush_from_id(style.brushes[key], widths[key], scale, style, key) for key in widths
    }


def ink_aux(shape: tuple[int, int], b: Brush) -> dict[str, np.ndarray] | None:
    """The extra accumulators a brush's phase 1 flags need, or None.

    Both are weighted sums over the same deposits as the ink itself, so
    dividing one by the ink gives a per-pixel weighted mean of whatever it
    carries. That is the whole trick: the reservoir and the break texture have
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


def _tip_band(w: np.ndarray, sigma: float) -> np.ndarray:
    """Bandlimit one stamp's weights across the tip.

    A treatment names its bristle count once, so a tip is the same number of
    logical bristles whether the mark is 3 render pixels wide or 17. On a
    narrow mark that puts most of the tip's structure past what the plate can
    carry, and what lands is an alias of it: hard-edged rails at about the
    plate's Nyquist, running the whole length of the stroke because the tip's
    weights do not change along it. Smoothing across the tip is the honest fix
    and not a blur of the mark: the deposit positions are untouched, so the
    mark keeps its width and its edge, and only the detail no pixel could have
    shown is graded away.

    Three box passes, which is a Gaussian to the eye, with the ends held by
    edge padding so the outermost bristles are not pulled inward.

    Args:
        w: The weights, `(samples along the stroke, samples across the tip)`.
        sigma: The smoothing, in samples across the tip.

    Returns:
        The smoothed weights, or `w` itself when the tip is already narrower
        than the smoothing would be.
    """
    r = int(round(sigma * 0.95))
    if r < 1 or w.shape[1] < 3:
        return w
    r = min(r, (w.shape[1] - 1) // 2)
    if r < 1:
        return w
    out = w
    for _ in range(3):
        pad = np.pad(out, ((0, 0), (r, r)), mode="edge")
        cs = np.cumsum(pad, axis=1, dtype=F32)
        cs = np.concatenate([np.zeros((len(out), 1), F32), cs], axis=1)
        out = (cs[:, 2 * r + 1 :] - cs[:, : out.shape[1]]) / F32(2 * r + 1)
    return out.astype(F32)


def _tip_drift(m: int, b: Brush, rng: np.random.Generator) -> np.ndarray:
    """Each bristle's sideways drift, as a quadrature pair per bristle.

    A bristle wanders sideways as the stroke goes on, and every bristle used to
    be given its own phase, drawn independently of the one beside it. On a
    narrow mark that is not a brush: the drift is wider than the gap between
    two bristles, so neighbours cross each other, the tip collapses into a few
    coincident filaments with bare paper between them, and the gaps run the
    whole length of the stroke because the phases do not change along it.

    Smoothing the drift across the tip is what makes it a tip again. The pair
    is renormalised afterwards, so each bristle still drifts by exactly the
    brush's own amplitude and only the phase is shared.

    Args:
        m: Logical bristles across the tip.
        b: The brush, for how much of the tip a drift is shared over.
        rng: The generator the phases are drawn from.

    Returns:
        `(2, m)`, the cosine and sine of each bristle's drift phase.
    """
    q = rng.normal(size=(2, m)).astype(F32)
    q = _tip_band(q, b.coherence * m)
    return q / np.maximum(np.hypot(q[0], q[1]), F32(1e-6))


def _unfold(
    off: np.ndarray, base: np.ndarray, jitter: np.ndarray, keep: float = 0.25
) -> np.ndarray:
    """Scale a drift back until the tip stops crossing itself.

    Even a shared drift can close the gap between two bristles where the tip
    is at its narrowest, and a closed gap is a filament with a hole beside it.
    The whole stroke's drift is scaled by one number rather than clipped per
    sample, so the mark keeps its wander and only loses the amplitude that
    would have folded it.

    Args:
        off: The offsets across the tip, `(samples, tip)`.
        base: The same without the drift.
        jitter: The drift alone.
        keep: The share of the nominal bristle spacing that has to survive.

    Returns:
        The offsets, with the drift scaled back if it had to be.
    """
    if off.shape[1] < 2:
        return off
    dbase = np.diff(base, axis=1)
    djit = np.diff(jitter, axis=1)
    close = djit < 0
    if not close.any():
        return off
    room = (dbase * F32(1.0 - keep))[close] / -djit[close]
    k = float(room.min())
    if k >= 1.0:
        return off
    return base + jitter * F32(k)


def _fbm1(
    t: np.ndarray, cell: float, b: Brush, rng: np.random.Generator, rows: int = 1
) -> np.ndarray:
    """Fractal noise along a stroke, with no period in it, in about -1 to 1.

    The wanders in a stroke were sines, so a long mark repeated itself at 2 pi
    times whatever cell each one was given. This is the same feature size drawn
    from a lattice instead: the values are random, the interpolation is smooth,
    and there is nothing for the eye to lock onto. `rows` independent copies
    come out of one call, which is how each bristle gets its own drift without
    a Python loop over the tip.

    The output is normalised to a sine's own spread, so swapping one for the
    other changes what repeats and not how hard the brush is worked.

    Args:
        t: Arc length along the stroke, in render pixels.
        cell: The coarsest lattice spacing, in the same units.
        b: The brush, for the octave count and the lacunarity.
        rng: The generator the lattice is drawn from.
        rows: How many independent fields to draw.

    Returns:
        The field, `(len(t), rows)`.
    """
    out = np.zeros((len(t), rows), F32)
    span = max(float(t[-1] - t[0]), 1.0)
    amp, total = 1.0, 0.0
    for i in range(b.org_oct):
        c = max(cell / (b.org_lac**i), 1.5)
        n = int(span / c) + 3
        g = rng.random((n, rows)).astype(F32) * F32(2.0) - F32(1.0)
        u = (t - t[0]) / c
        i0 = np.clip(np.floor(u).astype(np.int32), 0, n - 2)
        f = (u - i0).astype(F32)
        f = (f * f * (3 - 2 * f))[:, None]
        out += F32(amp) * (g[i0] + (g[i0 + 1] - g[i0]) * f)
        total += amp
        amp *= 0.5
    out /= F32(max(total, 1e-6))
    # A sine's standard deviation is 0.707, and the caller's amplitudes were
    # tuned against one. The floor keeps a short stroke, whose own spread is not
    # yet the field's, from being amplified into a swing it never had.
    sd = float(out.std())
    return np.clip(out * F32(0.707 / max(sd, 0.30)), -1.6, 1.6)


def _spread(vals: np.ndarray, u_log: np.ndarray, u: np.ndarray) -> np.ndarray:
    """Resample a per-logical-bristle field across the sampled tip.

    The tip is a handful of logical bristles, then sampled across at sub-pixel
    spacing. A field drawn per logical bristle has to be carried over to that
    sampling the same way the bristle weights are, or the drift would step from
    one bristle to the next instead of running continuously across the mark.

    Args:
        vals: The field, `(samples, logical bristles)`.
        u_log: The logical bristles' positions across the tip, ascending.
        u: The sampled positions across the tip.

    Returns:
        The field at `(samples, len(u))`.
    """
    idx = np.clip(np.searchsorted(u_log, u) - 1, 0, len(u_log) - 2)
    span = u_log[idx + 1] - u_log[idx]
    f = ((u - u_log[idx]) / np.where(span == 0, 1.0, span)).astype(F32)
    return vals[:, idx] * (1.0 - f) + vals[:, idx + 1] * f


def _smooth_path(
    x: np.ndarray, y: np.ndarray, radius: float, step: float
) -> tuple[np.ndarray, np.ndarray]:
    """Round a polyline's corners to a brush's own width.

    A generalised track turns 82 degrees at the 95th percentile of its
    vertices. A tip stamped straight through a corner like that folds over
    itself: the normal swings through the turn in a couple of samples, the far
    side of the tip runs backwards, and what lands is a bead. No brush draws a
    corner tighter than it is wide, so the path is smoothed to that radius
    before anything is stamped along it.

    Two box passes, which is a quadratic kernel: enough to take the cusp off
    without pulling a long straight off its line. The ends are held by edge
    padding, so a mark still starts and finishes where the way does.

    Args:
        x: Column coordinate per sample, in render pixels.
        y: Row coordinate per sample.
        radius: The corner radius, in render pixels.
        step: The spacing of the samples, in render pixels.

    Returns:
        The smoothed coordinates.
    """
    r = int(min(max(round(radius / max(step, 1e-3)), 1), max(len(x) // 3, 1)))
    for _ in range(2):
        for arr in (x, y):
            pad = np.pad(arr, (r, r), mode="edge")
            cs = np.cumsum(np.concatenate([[F32(0)], pad]), dtype=F32)
            arr[:] = (cs[2 * r + 1 :] - cs[: len(arr)]) / F32(2 * r + 1)
    return x, y


def stamp(
    acc: np.ndarray,
    pts: np.ndarray,
    b: Brush,
    rng: np.random.Generator,
    wmul: float = 1.0,
    aux: dict[str, np.ndarray] | None = None,
    wprof: np.ndarray | None = None,
) -> None:
    """Stamp one stroke's bristles into an ink accumulator.

    Args:
        acc: The accumulator, added to in place.
        pts: The path in render pixels.
        b: The brush.
        rng: The generator the bristle pattern is drawn from.
        wmul: A width multiplier for this stroke.
        aux: The accumulators from `ink_aux`, added to in place alongside the
            ink. None when neither reservoir nor directional break is on.
        wprof: A width multiplier along the stroke, sampled evenly from its
            start to its end and interpolated onto the stamps. This is what a
            broad nib is: the mark thickens and thins with the angle between
            the stroke and the nib, and there is no other way to say so,
            because pressure is generated inside here and width follows it.
    """
    h, w = acc.shape
    if len(pts) < 2:
        return
    d = np.diff(pts, axis=0)
    seg = np.hypot(d[:, 0], d[:, 1])
    total = float(seg.sum())
    if total < 2.5:
        return
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    n = max(int(total / b.step) + 2, 3)
    t = np.linspace(0.0, total, n).astype(F32)
    x = np.interp(t, cum, pts[:, 0]).astype(F32)
    y = np.interp(t, cum, pts[:, 1]).astype(F32)
    if b.smooth > 0:
        # Before the tangent, because the fold at a cusp is in the normal.
        x, y = _smooth_path(x, y, b.smooth, total / max(n - 1, 1))
    tx = np.gradient(x)
    ty = np.gradient(y)
    ln = np.hypot(tx, ty)
    ln[ln < 1e-5] = 1.0
    nx, ny = (-ty / ln).astype(F32), (tx / ln).astype(F32)

    ph = float(rng.random()) * 6.283
    if b.organic:
        # The pressure was two sines, so it came back every 2 pi press cells.
        press = 1.0 + b.press * _fbm1(t, 6.283 * b.press_cell * b.org_mult, b, rng)[:, 0]
    else:
        press = 1.0 + b.press * (
            np.sin(ph + t / b.press_cell) * 0.6 + np.sin(ph * 1.7 + t / (b.press_cell * 0.36)) * 0.4
        )
    # Set down loaded, lift to a point. Both ends taper by pressure, never by
    # opacity, and the lift is capped at a third of the stroke's own length.
    lift_px = max(min(b.lift, total * 0.34), 1.0)
    ends = np.clip(np.minimum(t, total - t) / lift_px, 0.0, 1.0) ** 0.7
    # The set-down is a nib touching the paper: a lot of ink in the first few
    # stamps, gone within about a width of travel, not a swelling.
    load_px = b.load_px if b.load_px > 0 else max(b.width * 0.85, 2.0)
    press = press * ends * (1.0 + b.load * np.exp(-t / load_px))
    width = b.width * wmul * (0.62 + 0.38 * press)
    if wprof is not None and len(wprof) > 1:
        width = width * np.interp(t, np.linspace(0.0, total, len(wprof)), np.asarray(wprof, F32))
    nib = None
    if b.pen_starve:
        # A nib does not break, it runs down: the line thins over a long run and
        # comes back full at the reload. The thinning is put on the width rather
        # than on the pressure because a pen's ink is saturated long before the
        # accumulator is, so darkness alone would not show.
        spent = 1.0 - np.exp(-np.mod(np.cumsum(press) * b.step, b.dip_px) / b.run_px)
        nib = (1.0 - b.pen_thin * spent).astype(F32)
        width = width * nib

    if b.organic:
        # And the line's own wander came back every 210 render pixels, which on
        # a road drawn end to end is the thing the eye picks out first.
        wob = b.wobble * _fbm1(t, 6.283 * 33.45 * b.unit * b.org_mult, b, rng)[:, 0]
    else:
        wob = b.wobble * (
            np.sin(ph * 2.3 + t / (46.0 * b.step / 0.55)) * 0.6
            + np.sin(ph * 3.1 + t / (15.0 * b.step / 0.55)) * 0.4
        )
    x = x + nx * wob
    y = y + ny * wob

    # The tip, as a handful of logical bristles: this is the pattern, not the
    # sampling. A real brush has two or three heavy tines and some fine ones,
    # so a low-frequency profile clumps them rather than leaving a comb.
    m = max(b.bristles, 2)
    u_log = np.linspace(-1.0, 1.0, m)
    keep = (rng.random(m) > b.gap).astype(np.float64)
    clump = 0.55 + 0.45 * np.sin(
        float(rng.random()) * 6.283 + u_log * float(rng.uniform(2.2, 5.5)) * 3.14
    )
    tex = b.texture
    bw_log = (rng.random(m) * 0.55 + 0.62) * keep * ((1.0 - tex) + tex * clump)
    drift_log = _tip_drift(m, b, rng)
    fp_log = rng.random(m) * 6.283
    fq_log = rng.random(m) * 0.6 + 0.7
    # Each bristle sets off with its own load, and the fat ones carry more, so
    # a mark thins from its edges in as the brush runs down.
    res_log = (0.55 + 0.9 * rng.random(m)) * (0.5 + 0.5 * bw_log) if b.starve else None
    dir_ph = rng.random(3) * 6.283 if b.dir_dry else None
    # The two fields that were a sine per bristle: the drift sideways, which was
    # one wavelength shared by the whole tip so the streaks breathed together,
    # and the break, whose per-bristle frequencies beat against each other into
    # a long section. Drawn per logical bristle and spread across the tip below.
    jit_log = along_log = None
    if b.organic:
        jit_log = _fbm1(t, 6.283 * 62.0 * b.unit * b.org_mult, b, rng, m)
        if b.coherence > 0:
            # The same sharing as the sine's phases, and for the same reason:
            # each bristle's drift was its own field and neighbours were driven
            # apart far enough to cross. Rescaled to the spread it had, because
            # smoothing independent fields together flattens them and the point
            # is who drifts with whom, not how far.
            was = float(jit_log.std())
            jit_log = _tip_band(jit_log, b.coherence * m)
            jit_log = jit_log * F32(was / max(float(jit_log.std()), 1e-6))
        along_log = _fbm1(t, 6.283 * 24.0 * b.unit * b.org_mult, b, rng, m)

    # The tip is then sampled across at sub-pixel spacing, so a wide brush is a
    # continuous edge rather than a row of separate lines, and no step shows.
    mean_w = float(np.mean(width))
    # Sampled across the tip's own width plus the room the drift needs. The tip
    # is not rigid: two bristles a nominal spacing apart can be driven twice
    # that apart, and a sampling that only covers the nominal width leaves the
    # stretched places with gaps between deposits, which is a light lane by a
    # different route. The drift is only counted when it is coherent, so a tip
    # left on the old draw is sampled exactly as it was.
    reach = mean_w + 4.0 * b.jitter if b.coherence > 0 else mean_w
    m_hi = int(min(max(m, reach / max(b.profile_px, 0.1) + 2), 512))
    u = np.linspace(-1.0, 1.0, m_hi).astype(F32)
    bw = np.interp(u, u_log, bw_log).astype(F32)
    dc = np.interp(u, u_log, drift_log[0]).astype(F32)
    ds = np.interp(u, u_log, drift_log[1]).astype(F32)
    fp = np.interp(u, u_log, fp_log).astype(F32)
    fq = np.interp(u, u_log, fq_log).astype(F32)
    res0 = np.interp(u, u_log, res_log).astype(F32) if b.starve else None
    prof = ((1.0 - 0.32 * np.abs(u)) ** 1.3).astype(F32)
    if b.solid > 0:
        # A loaded pen or fine liner: a flat core the bristles sit on top of.
        prof = prof * (1.0 - b.solid) + b.solid * np.clip((1.0 - np.abs(u)) * 6.0, 0.0, 1.0)
        bw = bw * (1.0 - b.solid) + b.solid

    if jit_log is not None:
        jitter = b.jitter * _spread(jit_log, u_log, u)
    else:
        # The same drift the sine always laid, written as a quadrature pair so
        # the phase can be shared across the tip: `dc` and `ds` are the cosine
        # and sine of one bristle's phase and square to 1, so the amplitude is
        # the brush's own and only who drifts with whom has changed.
        ph = (t / (62.0 * b.unit)).astype(F32)
        jitter = b.jitter * (dc[None, :] * np.sin(ph)[:, None] + ds[None, :] * np.cos(ph)[:, None])
    base = u[None, :] * width[:, None] * F32(0.5)
    off = base + jitter
    if b.coherence > 0:
        off = _unfold(off, base, jitter)
    px = x[:, None] + nx[:, None] * off
    py = y[:, None] + ny[:, None] * off
    # Each bristle carries and loses ink as it goes, and on a dry brush it lifts
    # off the paper entirely for a stretch: that is where the mark breaks.
    if along_log is not None:
        along = 0.5 + 0.5 * _spread(along_log, u_log, u)
    else:
        along = 0.5 + 0.5 * np.sin(fp[None, :] + t[:, None] * fq[None, :] / (24.0 * b.unit))
    cut = b.dry * 0.5
    along = np.clip((along - cut) / max(1.0 - cut, 1e-3), 0.0, 1.0)
    along = (1.0 - tex) + tex * along
    # Ink per stamp is normalised against the sampling, so the darkness numbers
    # mean the same thing whatever the step and the profile spacing are set to.
    # `unit` is in there because what the accumulator holds is a thickness and
    # not a count: on a grid twice as fine the same mark is spread across twice
    # as many pixels of tip, and without the factor it comes out half as dark.
    norm = (b.step / 0.55) * (m / m_hi) * b.unit
    # The tip's lanes: what the bristles weigh and where the brush is breaking,
    # which is everything that varies across the mark apart from its own shape.
    lane = (bw[None, :] * along).astype(F32)
    if b.band_px > 0 and mean_w > 0:
        # Held to what a mark this wide can show, so the bristle weights, the
        # dropped lanes and the break texture are all bandlimited together. The
        # stroke's own length is untouched, and so are the deposit positions:
        # the mark keeps its width and its edge.
        lane = _tip_band(lane, b.band_px * b.unit * m_hi / mean_w)
    if b.contrast != 1.0:
        # How hard the lanes are, about the tip's own mean, so the knob moves
        # the streaking and not the mark's profile or how much ink it carries.
        mid = lane.mean(axis=1, keepdims=True)
        lane = np.maximum(mid + (lane - mid) * b.contrast, F32(0.0))
    wgt = (prof[None, :] * lane * press[:, None] * b.darkness * norm).astype(F32)
    if b.coherence > 0 and m_hi > 2:
        # Each sample carries the strip of tip it actually stands on, not an
        # equal share of it. Once the bristles drift the samples are no longer
        # evenly spaced, and an equal share per sample turns every bunch into a
        # dark filament and every spread into a light one, which is the rest of
        # the streaking after the fold is gone. The strips sum to the tip's own
        # width, so the mark carries exactly the ink it did.
        span = np.empty_like(off)
        span[:, 1:-1] = (off[:, 2:] - off[:, :-2]) * F32(0.5)
        span[:, 0] = off[:, 1] - off[:, 0]
        span[:, -1] = off[:, -1] - off[:, -2]
        wgt = wgt * (span * F32(m_hi - 1) / np.maximum(width[:, None], 1e-6))

    if nib is not None:
        # And it lightens with it, by about half as much again: what the eye
        # reads on a pen line is the width, not the black.
        wgt = (wgt * (1.0 - 0.5 * b.pen_thin * spent)[:, None]).astype(F32)

    wgt_r = wgt_t = None
    if aux is not None and "res" in aux and not b.starve:
        # A brush sharing an accumulator with one that is on the reservoir but
        # not on it itself reads as full, never as empty.
        wgt_r = wgt
    if aux is not None and "tooth" in aux and not b.dir_dry:
        wgt_t = (wgt * F32(0.5)).astype(F32)
    if b.starve and aux is not None:
        # Ink is spent in proportion to what is laid down, so a heavy bristle
        # empties first and pressure spends it faster. `dip_px` is the reload:
        # the seam it leaves is what makes a long line look drawn.
        phase = np.mod(np.cumsum(press) * b.step, b.dip_px)[:, None]
        res = np.clip(
            b.res_floor + (1.0 - b.res_floor) * res0[None, :] * np.exp(-phase / b.run_px), 0.0, 1.3
        ).astype(F32)
        wgt = (wgt * (b.knee + (1.0 - b.knee) * res)).astype(F32)
        wgt_r = (wgt * res).astype(F32)
    if b.dir_dry and aux is not None:
        # The break texture, in the stroke's own frame: `dir_elong` times
        # longer along the mark than across it, so a dry brush leaves scratches
        # running with the line rather than blotches sitting on it.
        kx = F32(6.283 / max(b.dir_cell * b.dir_elong, 1.0))
        ky = F32(6.283 / max(b.dir_cell, 1.0))
        sl = t[:, None] * kx
        ul = off * ky
        tex_d = (
            0.50 * np.sin(sl + ul * 0.85 + dir_ph[0])
            + 0.30 * np.sin(sl * 2.3 - ul * 1.7 + dir_ph[1])
            + 0.20 * np.sin(sl * 0.55 + ul * 0.4 + dir_ph[2])
        )
        # Clipped rather than scaled, so the texture keeps its flats: the splat
        # averages it once and the gate would otherwise read a grey mush.
        wgt_t = (wgt * np.clip(0.5 + 0.85 * tex_d, 0.0, 1.0)).astype(F32)

    # Bilinear deposition. Rounding to the nearest pixel is what put the steps
    # and the stair-edges in the earlier marks.
    fx0 = np.floor(px)
    fy0 = np.floor(py)
    ax = (px - fx0).astype(F32)
    ay = (py - fy0).astype(F32)
    ix0 = fx0.astype(np.int32)
    iy0 = fy0.astype(np.int32)
    for dy in (0, 1):
        wy = ay if dy else (1.0 - ay)
        iy = np.clip(iy0 + dy, 0, h - 1)
        for dx in (0, 1):
            wx = ax if dx else (1.0 - ax)
            ix = np.clip(ix0 + dx, 0, w - 1)
            at = (iy.ravel(), ix.ravel())
            np.add.at(acc, at, (wgt * wx * wy).ravel())
            if wgt_r is not None:
                np.add.at(aux["res"], at, (wgt_r * wx * wy).ravel())
            if wgt_t is not None:
                np.add.at(aux["tooth"], at, (wgt_t * wx * wy).ravel())

    if b.pool > 0:
        # And it leaves a blot: tighter and denser than a swelling, so it reads
        # as the first touch rather than a bulge in the line.
        r = max(b.width * b.pool_radius_frac, 1.2)
        span = int(r * 2)
        yy, xx = np.ogrid[-span : span + 1, -span : span + 1]
        blob = np.exp(-(xx * xx + yy * yy) / (2 * r * r)).astype(F32) * b.pool * b.pool_gain
        cy, cx = int(round(float(y[0]))), int(round(float(x[0])))
        y0, y1 = max(cy - span, 0), min(cy + span + 1, h)
        x0, x1 = max(cx - span, 0), min(cx + span + 1, w)
        if y1 > y0 and x1 > x0:
            acc[y0:y1, x0:x1] += blob[
                y0 - cy + span : y1 - cy + span, x0 - cx + span : x1 - cx + span
            ]


def ink_density(
    acc: np.ndarray,
    b: Brush,
    sheet: Sheet,
    aux: dict[str, np.ndarray] | None = None,
    paper: np.ndarray | None = None,
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
    if b.bleed <= 0.4:
        return dens
    return np.clip(np.maximum(dens, blur(dens, b.bleed) * 1.35), 0, 1)


def scaled_brush(b: Brush, k: int) -> Brush:
    """The same brush on a grid `k` times finer than the plate's own.

    Everything the brush measures in pixels moves with the grid. `unit` carries
    the factor, so the wavelengths written into `stamp` stay the lengths they
    were rather than shrinking with the grid they are sampled on. The stamp
    spacing and the tip's own sampling are capped rather than scaled: a finer
    grid is asked for precisely so those two land under a pixel.

    Args:
        b: The brush on the plate's grid.
        k: Pixels of the finer grid per plate pixel.

    Returns:
        The brush on that grid, or `b` itself at `k` of 1.
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


def _grow(a: np.ndarray, h: int, w: int) -> np.ndarray:
    """One smooth field carried up to a finer grid, bilinear."""
    img = Image.fromarray(np.asarray(a, F32), "F").resize((w, h), Image.BILINEAR)
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
    img = Image.fromarray(np.asarray(a, F32), "F").resize((w, h), Image.LANCZOS)
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

    def __init__(self, shape: tuple[int, int], b: Brush, style: PaintStyle) -> None:
        """Open an accumulator for one class.

        Args:
            shape: The plate's pixel shape.
            b: The brush the class is read back with, for the accumulators its
                flags need.
            style: The paint style, for the grid and the joining.
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


def ribbon_alpha(
    d_route: np.ndarray,
    r_px: float,
    sheet: Sheet,
    fill: bool,
    tear_px: float,
    land: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """The trimmed extent of the painted ground, and its pooled edge.

    Args:
        d_route: Distance in pixels to the route.
        r_px: The ribbon radius in pixels.
        sheet: The paper's noise fields.
        fill: Fill the inside of a loop rather than dilating the line alone.
        tear_px: How far the torn edge wanders.
        land: The land side of a surveyed coast, when there is one.

    Returns:
        The ribbon's alpha, and the density of its pooled rim.
    """
    if fill:
        core = d_route < r_px
        core = fill_holes(core, step=max(4, int(r_px / 12)))
        s = (blur(core.astype(F32), r_px * 0.34) - 0.5) * (r_px * 0.9)
    else:
        s = blur(np.asarray(r_px - d_route, F32), r_px * 0.30)
    sig = s + (sheet.coarse - 0.5) * (r_px * 0.30) + (sheet.fine - 0.5) * tear_px
    alpha = smoothstep(sig, 2.6)
    rim = np.exp(-np.abs(sig) / F32(max(r_px * 0.045, 3.0))) * alpha
    if land is not None:
        # The coast is a hard edge, not a wash edge. Nothing the ribbon carries
        # is allowed over it: the torn edge stops at the surveyed line, and the
        # sea, which is painted separately and never trimmed, takes over there.
        alpha = alpha * land
        rim = rim * land
    return alpha, rim


# --------------------------------------------------------------------------- the card


def paper_plate(sheet: Sheet, plate: Plate, style: PaintStyle) -> np.ndarray:
    """The notebook card: cream rag, a worn border, a little foxing, no grid."""
    h, w = plate.h, plate.w
    base = rgb(style.paper_hex)
    img = np.repeat(base[None, None, :], h, 0).repeat(w, 1).copy()
    img *= (1.0 + style.paper_tooth * (sheet.paper - 0.5))[..., None]
    yy = np.minimum(np.arange(h)[:, None], h - 1 - np.arange(h)[:, None])
    xx = np.minimum(np.arange(w)[None, :], w - 1 - np.arange(w)[None, :])
    edge_px = np.minimum(yy, xx).astype(F32)
    worn = np.exp(-edge_px / F32(max(w * 0.012, 8.0)))
    worn = worn * (0.55 + 0.9 * sheet.noise(26.0, 2))
    img *= (1.0 - style.paper_worn * np.clip(worn, 0, 1))[..., None]
    vign = np.exp(-edge_px / F32(w * 0.34))
    img *= (1.0 - style.paper_vignette * vign)[..., None]
    fox = np.clip((sheet.noise(120.0, 2) - 0.80) * 5.0, 0, 1)
    img *= (1.0 - style.paper_foxing * fox)[..., None]
    if style.grid:
        step = max(style.grid_spacing_px * plate.w / max(style.display_px, 1), 4.0)
        rows = (np.arange(h) % step < 1.0)[:, None]
        cols = (np.arange(w) % step < 1.0)[None, :]
        line = np.clip(rows * 1.0 + cols * 0.55, 0, 1).astype(F32)
        img *= (1.0 - style.grid_opacity * 0.30 * line)[..., None]
    return np.clip(img, 0, 1)


def to_img(arr: np.ndarray, rng: np.random.Generator) -> Image.Image:
    """An RGB image with a little dither, so a flat wash has no banding."""
    d = (rng.random(arr.shape, dtype=np.float32) - rng.random(arr.shape, dtype=np.float32)) * 0.5
    return Image.fromarray(np.clip(arr * 255.0 + 0.5 + d, 0, 255).astype(np.uint8), "RGB")


def save_webp(img: Image.Image, path: Path, quality: int = 74, lossless: bool = False) -> int:
    """Write one WebP plate and return its size in bytes.

    Args:
        img: The plate.
        path: Where to write it.
        quality: The lossy encoder's quality, used only when `lossless` is off.
        lossless: Write the exact pixels the painter composed. This is what the
            ink wants: the lossy encoder works in 4 by 4 blocks on a half
            resolution chroma plane, which is wider than most of the marks on
            the plate, so it replaces a stroke's ramp with two flats and a step
            and takes the paper's grain with it.

    Returns:
        The file's size in bytes.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if lossless:
        img.save(path, format="WEBP", lossless=True, method=5)
    else:
        img.save(path, format="WEBP", quality=quality, method=5)
    return path.stat().st_size


def save_alpha(alpha: np.ndarray, path: Path, quality: int = 82, lossless: bool = False) -> int:
    """Write a white plate carrying alpha, for one the page tints itself.

    White rather than black, because an SVG mask reads luminance times alpha by
    default: a black plate would mask everything out whichever way it is read.

    WebP already stores the alpha channel losslessly, so this plate was never
    the one the encoder was hurting; `lossless` covers the flat white beside it
    and costs nothing, the file coming out slightly smaller than the lossy one.

    Args:
        alpha: The plate's alpha, in 0 to 1.
        path: Where to write it.
        quality: The lossy encoder's quality for the colour channels, used only
            when `lossless` is off.
        lossless: Write the exact pixels.

    Returns:
        The file's size in bytes.
    """
    h, w = alpha.shape
    rgba = np.full((h, w, 4), 255, np.uint8)
    rgba[..., 3] = np.clip(alpha * 255 + 0.5, 0, 255).astype(np.uint8)
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.fromarray(rgba, "RGBA")
    if lossless:
        img.save(path, format="WEBP", lossless=True, method=4)
    else:
        img.save(path, format="WEBP", quality=quality, method=4)
    return path.stat().st_size


def save_rgba(
    rgb: np.ndarray, alpha: np.ndarray, path: Path, quality: int = 88, lossless: bool = True
) -> int:
    """Write a plate carrying its own colour and its own alpha.

    The label plate is composited normally rather than multiplied, so it needs
    both: multiply can only darken, and a backing wash in the paper's own colour
    has to be able to lighten.

    Lossless by default, and for the same reason the base plates are: the lossy
    encoder transforms in 4 by 4 blocks on a half resolution chroma plane, and
    a thinned glyph stroke is between one and three pixels wide. It is the
    worst case the encoder has, not a marginal one, and a name is the thing on
    the card a reader looks at closest.

    Args:
        rgb: The colour, `(h, w, 3)` in 0 to 1.
        alpha: The coverage, `(h, w)` in 0 to 1.
        path: Where to write.
        quality: The lossy encoder's quality, used only when `lossless` is off.
        lossless: Write the exact pixels that were composed.

    Returns:
        The file's size in bytes.
    """
    h, w = alpha.shape
    out = np.empty((h, w, 4), np.uint8)
    out[..., :3] = np.clip(rgb * 255.0 + 0.5, 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(alpha * 255.0 + 0.5, 0, 255).astype(np.uint8)
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.fromarray(out, "RGBA")
    if lossless:
        img.save(path, format="WEBP", lossless=True, method=4)
    else:
        img.save(path, format="WEBP", quality=quality, method=4)
    return path.stat().st_size


# --------------------------------------------------------------------------- lettering


#: How wide a mark of each role is drawn, as a multiple of the type size it
#: belongs to. The lettering sets the weight; every other mark on a label is a
#: shade lighter than it, so the line recedes behind the name.
MARK_WEIGHT = {
    "glyph": 1.0,
    "leader": 0.72,
    "span": 0.9,
    "tick": 0.9,
    "underline": 0.66,
    "pin": 1.5,
}


def label_brushes(style: PaintStyle, scale: float) -> Callable[[str, float], Brush]:
    """A brush per role and type size, made once and kept.

    A nib rather than a brush, and with the route's own set-down turned right
    down: `MAJ6-e` lays a blot at the start of every stroke, which is character
    on a lane and a blob on the crossbar of a `t`.

    Args:
        style: The paint style, for the label brushes and their widths.
        scale: Render pixels per display pixel.

    Returns:
        `brush(role, size)`, the brush for one mark.
    """
    made: dict[tuple[str, int], Brush] = {}

    def brush(role: str, size: float) -> Brush:
        """The brush for one role at one type size."""
        key = (role, int(round(size * 4)))
        got = made.get(key)
        if got is not None:
            return got
        pen = role == "glyph"
        wid = style.label_pen_width_px if pen else style.label_leader_width_px
        if pen and style.label_route == "outline":
            wid *= style.label_outline_width_frac
        wid = wid * max(size, 1.0) / max(style.label_size_px, 1e-6)
        made[key], _hex = brush_from_id(
            style.label_brush if pen else style.label_leader_brush,
            wid * MARK_WEIGHT.get(role, 1.0),
            scale,
            style,
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

    return brush


def _pen_profile(pts: np.ndarray, angle: float, thin: float, samples: int = 24) -> np.ndarray:
    """A width along one stroke, from the angle between it and the nib.

    A broad nib held at a fixed angle draws its full width across itself and
    almost nothing along itself. That single fact is most of what separates a
    written letter from a plotted one, and it is why the same skeleton stamped
    at one width reads as a machine.

    Args:
        pts: The stroke in render pixels.
        angle: The nib's angle in radians, anticlockwise from the writing line.
        thin: How much of the width a stroke drawn straight along the nib loses.
        samples: How many points the profile is sampled at.

    Returns:
        The multiplier at evenly spaced points from the stroke's start to end.
    """
    if len(pts) < 2:
        return np.ones(2, F32)
    d = np.diff(pts, axis=0)
    seg = np.hypot(d[:, 0], d[:, 1])
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    if cum[-1] <= 1e-6:
        return np.ones(2, F32)
    at = np.linspace(0.0, cum[-1], samples)
    mid = np.clip(np.searchsorted(cum, at) - 1, 0, len(seg) - 1)
    theta = np.arctan2(d[mid, 1], d[mid, 0])
    across = np.abs(np.sin(theta - angle))
    return ((1.0 - thin) + thin * across).astype(F32)


def _dark_field(manifest: dict[str, Any], h: int, w: int) -> np.ndarray:
    """The painter's coarse darkness grid, back up at the plate's own size."""
    dark = manifest.get("dark") or {}
    grid = dark.get("v")
    if not grid:
        return np.full((h, w), 0.35, F32)
    small = np.asarray(grid, F32)
    return np.asarray(Image.fromarray(small, "F").resize((w, h), Image.BILINEAR), F32)


#: A colour a mark may name directly, as opposed to one of the three ink tokens.
_HEX = re.compile(r"#[0-9a-fA-F]{6}")


def label_plate(
    manifest: dict[str, Any], marks: list[Any], style: PaintStyle, path: Path | None = None
) -> Path | None:
    """Write the names, the leaders and the spans as one RGBA plate.

    The page composites this normally rather than multiplying it, which is the
    whole reason it is its own plate: the backing wash is the paper's own
    colour and multiply can only darken. Everything on it is stroked through
    the same ink engine as the roads and the rivers and gated on the same
    paper, so the lettering is made of the map's ink and not printed over it.

    Args:
        manifest: The painted plates' manifest, for the grid, the paper and the
            darkness under each name.
        marks: What to draw. Each carries `pts` in display pixels, a `role`
            naming its weight, an `ink` naming its colour, the type `size` it
            belongs to and the `pen` angle it was written with.
        style: The paint style.
        path: Where to write; `labels.webp` beside the other plates by default.

    Returns:
        The file written, or None when there was nothing to draw.
    """
    if not marks:
        return None
    rw, rh = manifest["render"]
    scale = rw / max(manifest["display"][0], 1)
    sheet = Sheet(
        rh,
        rw,
        gran_px=manifest.get("gran_px", 6.0),
        seed=style.sheet_seed,
        fibre=style.paper_fibre_mix if style.paper_fibre else 0.0,
        fibre_stretch=style.paper_fibre_stretch,
        fibre_angle=style.paper_fibre_angle,
        fibre_cell=max(style.paper_fibre_cell_px * rw / 1800.0, 1.6),
    )
    brush = label_brushes(style, scale)
    angle = math.radians(style.label_pen_angle_deg)
    inks = {
        "map": style.label_ink,
        "route": style.label_route_ink,
        "water": style.label_water_ink,
        "in_water": style.label_in_water_ink,
    }
    groups: dict[str, list[tuple[Brush, np.ndarray, np.ndarray | None, bool]]] = {}
    for mark in marks:
        pts = np.asarray(mark.pts, np.float64) * scale
        if len(pts) < 2:
            continue
        b = brush(mark.role, mark.size)
        prof = (
            _pen_profile(pts, angle + mark.pen, style.label_pen_thin)
            if mark.role == "glyph"
            else None
        )
        # Three of the inks are the style's own and are named; a span carries a
        # fourth, resolved from its intent by `labels`, and it arrives as the
        # colour itself. Anything else falls back to the map's ink rather than
        # writing a name in a colour nobody chose.
        key = str(mark.ink)
        if key not in inks:
            key = key if _HEX.fullmatch(key) else "map"
            inks.setdefault(key, key)
        groups.setdefault(key, []).append((b, pts, prof, bool(mark.wash)))
    if not groups:
        return None

    rng = np.random.default_rng(style.label_seed)
    layers: list[tuple[np.ndarray, np.ndarray]] = []
    cover = np.zeros((rh, rw), F32)
    dark = _dark_field(manifest, rh, rw)
    # A name is written a shade darker where the paper is bare and a shade
    # lighter over a wood, which is the difference between printed on and
    # written on.
    tint = (1.0 + 0.20 * (dark - 0.35))[..., None]
    for ink, items in groups.items():
        base = items[0][0]
        pad = InkPad((rh, rw), base, style)
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
                keep = InkPad((rh, rw), base, style)
                keep.lay(
                    [(b, line) for b, line, _p, w in items if w],
                    rng,
                    profiles=[prof for _b, _l, prof, w in items if w],
                )
                cover = np.maximum(cover, keep.read(base, sheet))
        layers.append(
            (np.clip(rgb(inks[ink])[None, None, :] * tint, 0.0, 1.0), np.clip(dens, 0.0, 1.0))
        )

    out_rgb = np.zeros((rh, rw, 3), F32)
    out_a = np.zeros((rh, rw), F32)
    if style.label_wash:
        layers.insert(0, _backing_wash(cover, dark, sheet, style, scale))
    for src_rgb, src_a in layers:
        a = np.clip(src_a, 0.0, 1.0)[..., None]
        keep = out_a[..., None] * (1.0 - a)
        total = np.maximum(a + keep, 1e-6)
        out_rgb = (src_rgb * a + out_rgb * keep) / total
        out_a = np.clip(a[..., 0] + out_a * (1.0 - a[..., 0]), 0.0, 1.0)

    path = path or (Path(manifest["dir"]) / "labels.webp")
    save_rgba(out_rgb, out_a, path, style.paper_quality, lossless=style.plate_lossless)
    return path


def _backing_wash(
    cover: np.ndarray, dark: np.ndarray, sheet: Sheet, style: PaintStyle, scale: float
) -> tuple[np.ndarray, np.ndarray]:
    """A faint lift of paper under a word block, through the wash machinery.

    Not a halo: a halo is an outline offset from the glyphs and it reads as a
    sticker cut round the letters. This is one soft blob a word, granulated on
    the paper's own pits with a pooled rim, and it is absent where the ground
    is already pale enough to read on, so it says "the paint was lifted before
    this was written" rather than sitting under every name on the sheet.

    Args:
        cover: The label ink's own density.
        dark: How dark the sheet is under each pixel.
        sheet: The paper.
        style: The paint style.
        scale: Render pixels per display pixel.

    Returns:
        The wash's colour and its alpha, ready to composite under the ink.
    """
    reach = max(style.label_wash_spread * style.label_size_px * scale, 2.0)
    near = edt(cover > 0.12)
    blob = blur(np.clip(1.0 - near / reach, 0.0, 1.0), reach * 0.35)
    dens = wash(
        np.clip(blob * 1.6, 0.0, 1.0),
        sheet,
        0.85,
        0.3,
        rim_px=max(reach * 0.4, 3.0),
        gran=0.3,
        gran_gamma=style.gran_gamma if style.paper_fibre else 0.0,
    )
    floor = style.label_wash_dark_floor
    gate = np.clip((dark - floor) / max(1.0 - floor, 1e-3), 0.0, 1.0)
    alpha = np.clip(dens * gate * style.label_wash_alpha, 0.0, 1.0)
    return np.broadcast_to(rgb(style.paper_hex), (*cover.shape, 3)).copy(), alpha


# --------------------------------------------------------------------------- painting


def plates_dir(key: str, cache_dir: Path) -> Path:
    """Where one activity's painted plates are cached, under the geo cache."""
    return Path(cache_dir) / PLATES_SUBDIR / key


def paint_hash(basemap: Basemap, style_digest: str) -> str:
    """A hash over the basemap and the style, so a repaint is only ever needed once.

    Args:
        basemap: The basemap `geo.journal_layers` assembled; its canonical text,
            the card frame and the layers, is hashed.
        style_digest: The digest of the style groups the base plates read.

    Returns:
        A short hex digest of the canonical text, a hyphen, and the style digest.
    """
    return hashlib.sha256(basemap.canonical().encode()).hexdigest()[:16] + "-" + style_digest


def label_geom(basemap: Basemap, tol_px: float) -> dict[str, Any]:
    """The lines a name can be set along, clipped to the card and simplified.

    The roads and the watercourses are in the geo payload and nowhere else, and
    the geo payload is transient: re-deriving it at label time costs seven
    seconds and a fetch that may not be possible. So the named centrelines and
    the coastline are kept here, in the card's own metres, at a tolerance that
    is generous because a baseline is read at a glance and never measured.

    Args:
        basemap: The basemap from `geo.journal_layers`.
        tol_px: Simplification tolerance in display pixels.

    Returns:
        `{"roads": [...], "rivers": [...], "coast": [...]}`, each entry a name,
        a class, a road number where OSM has one, and a polyline in card
        metres.
    """
    layers = basemap.layers
    tol = max(tol_px * float(basemap.card.mpp_display), 1.0)

    def lines(line: Line) -> list[list[list[float]]]:
        out = []
        for piece in [list(line)] if len(line) > 1 else []:
            kept = simplify(piece, tol)
            if len(kept) > 1:
                out.append([[round(x, 1), round(y, 1)] for x, y in kept])
        return out

    named: dict[str, list[dict[str, Any]]] = {
        "roads": [
            {"n": r.name, "c": r.cls, "r": r.ref, "w": 0.0, "wn": 0.0, "line": r.line}
            for r in layers.roads
        ],
        "rivers": [
            {
                "n": r.name,
                "c": r.cls,
                "r": "",
                "w": r.width_px,
                "wn": r.name_width_px,
                "line": r.line,
            }
            for r in layers.rivers
        ],
    }
    geom: dict[str, Any] = {"roads": [], "rivers": [], "coast": [], "crossings": []}
    for key in ("roads", "rivers"):
        for entry in named[key]:
            for line in lines(entry["line"]):
                if entry["n"]:
                    # `w` is the width this watercourse was actually painted at,
                    # which is its own where one could be measured and the class
                    # floor where it could not. A name clears the ink it is set
                    # beside, so it has to be the ink that was laid down and not
                    # what the class would have laid down.
                    geom[key].append(
                        {
                            "n": entry["n"],
                            "c": entry["c"],
                            "r": entry["r"],
                            "w": entry["w"],
                            "wn": entry["wn"],
                            "d": line,
                        }
                    )
                else:
                    # An unnamed lane can carry no name of its own, so it was
                    # left out of the geometry altogether and a label could be
                    # laid across one for nothing. It is kept here, without a
                    # name, purely so the crossing cost can see it.
                    geom["crossings"].append(line)
    for coast in layers.coastline:
        geom["coast"].extend(lines(coast))
    return geom


def labels_hash(labels: list[dict[str, Any]] | None, style: PaintStyle) -> str:
    """A hash over what is lettered and how, so a stale label plate is caught.

    The picks live in the analysis payload, not the geo payload, so `paint_hash`
    cannot see them and a plate keyed on it alone would letter yesterday's names
    over today's map. A caller compares this against the manifest's own before
    it draws a label plate, and draws nothing when they differ.

    Args:
        labels: The resolved labels, or None when nothing is lettered.
        style: The paint style, for the fields a label is drawn with.

    Returns:
        A short hex digest.
    """
    keys = (
        "label_font",
        "label_size_px",
        "label_max",
        "label_pin_colour",
        "label_ink",
        "label_glow_colour",
        "labels",
        "label_seed",
        "label_geom_tol_px",
        "home_glyph",
        "label_route",
        "label_face",
        "label_brush",
        "label_pen_width_px",
        "label_leader_brush",
        "label_leader_width_px",
        "label_pen_angle_deg",
        "label_pen_thin",
        "label_outline_width_frac",
        "label_wash",
        "label_wash_alpha",
        "label_wash_dark_floor",
        "label_wash_spread",
        "label_route_ink",
        "label_water_ink",
        "label_in_water_ink",
        "label_ground",
    )
    blob = json.dumps(
        {"labels": labels or [], "style": {k: getattr(style, k) for k in keys}},
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def load_plates(key: str, cache_dir: Path) -> Plates | None:
    """An activity's painted plates, or None when there are none.

    The renderer never paints: a page with no plates draws the vector map and
    says so, which is the honest answer offline and the same answer whether the
    painter has not been run or the activity is new. A manifest that cannot be
    read, or that names a plate no longer on disk, reads as no plates.
    """
    from pyntpot.maps.plates import Manifest, Plates

    path = plates_dir(key, cache_dir) / "plates.json"
    if not path.exists():
        return None
    try:
        manifest = Manifest.from_json(path.read_text())
    except (OSError, ValueError, KeyError, TypeError):
        return None
    plates = Plates(path.parent, manifest)
    if not all(plate.exists() for plate in plates.paths.values()):
        return None
    return plates


def coast_run(d_sea: np.ndarray, wet: np.ndarray, band: float) -> float:
    """Which way the shore runs, in radians, from the sea's own distance field.

    The gradient of the distance into the sea points across the coast, so the
    coast itself runs at right angles to it. Orientation has no sign, so the
    angles are doubled before they are averaged and halved after: a shore that
    turns a corner gives the run of the longer side rather than the mean of the
    two, which is what a painter's wrist would follow.

    Args:
        d_sea: Distance in render pixels from the land into the sea.
        wet: Where the sea is.
        band: How far out from the shore to read the direction, in pixels.

    Returns:
        The angle, in image coordinates with the row axis downward. 0 when
        there is no shore in the card.
    """
    gy, gx = np.gradient(blur(d_sea, 3.0))
    near = wet & (d_sea > 1.0) & (d_sea < band)
    mag = np.hypot(gx, gy)
    sel = near & (mag > 1e-3)
    if not sel.any():
        return 0.0
    ang = np.arctan2(gx[sel], -gy[sel])
    return 0.5 * float(math.atan2(float(np.sin(2 * ang).mean()), float(np.cos(2 * ang).mean())))


def sea_patches(dens: np.ndarray, sea_cov: np.ndarray, mpp: float, style: PaintStyle) -> np.ndarray:
    """Broad paler and deeper patches in the sea, worked along the shore.

    The sea is the largest single wash on the card and the one that has to
    stay flat everywhere it is not: a wash that big does not dry evenly, it
    dries in patches the width of the brush's own travel, and the pigment gets
    worked along the shore rather than across it. One low frequency field
    gives the patches, a second stretched along the coast's own run gives the
    streaking, and the streaking fades out to sea because that is where the
    brush stopped being dragged along an edge.

    Args:
        dens: The sea wash's density, in 0 to 1.
        sea_cov: The sea's coverage, for the shore the streaks follow.
        mpp: Metres per render pixel, so a patch is the same size on the
            ground whatever box the card holds.
        style: The paint style, for the cell, the swing and the streaking.

    Returns:
        The modulated density, in 0 to 1.
    """
    amount = float(np.clip(style.sea_variation_amount, 0.0, 1.0))
    if amount <= 0.0:
        return dens
    h, w = dens.shape
    rng = np.random.default_rng(style.sea_variation_seed)
    cell = max(style.sea_variation_cell_m / mpp, 8.0)
    wet = sea_cov > 0.5
    if not wet.any():
        wet = np.ones_like(wet)

    def centred(f: np.ndarray) -> np.ndarray:
        """The field about its own mean over the sea, in about -1 to 1.

        Over the sea, because the patches move pigment about rather than add
        it: a field centred on the whole card would lighten or darken a sea
        that sits in one corner of it.
        """
        return (f - float(f[wet].mean())) * 2.0

    swing = centred(fbm(h, w, cell, 3, rng))
    streak_w = float(np.clip(style.sea_variation_streak, 0.0, 1.0))
    if streak_w > 0.0:
        d_sea = edt(~wet)
        band = max(style.sea_variation_band_m / mpp, 4.0)
        angle = coast_run(d_sea, wet, band)
        streak = fbm_aniso(
            h, w, max(cell * 0.22, 3.0), 2, rng, max(style.sea_variation_elong, 1.0), angle
        )
        swing = swing + streak_w * centred(streak) * np.exp(-d_sea / F32(band))
        swing /= 1.0 + streak_w
    return np.clip(dens * (1.0 + amount * swing), 0.0, 1.0)


def _lines(lines: tuple[Line, ...]) -> list[list[Pt]]:
    """The lines long enough to draw, as the point lists the painter fills and strokes."""
    return [list(line) for line in lines if len(line) > 1]


def paint(
    basemap: Basemap,
    style: PaintStyle | None = None,
    out_dir: Path | None = None,
    labels: list[dict[str, Any]] | None = None,
    *,
    key: str,
    style_digest: str,
) -> Plates:
    """Paint one activity's plates and write them, with a manifest beside them.

    Two plates come out. `paper` is the card itself, drawn as it is. `wash`
    carries every pigment, white where it lays down nothing, and the page
    multiplies it over the card: the land cover and the relief are trimmed to
    the ribbon, the sea runs to the card edge, and the ink is drawn over the
    whole sheet.

    Args:
        basemap: The basemap from `geo.journal_layers`.
        style: The paint style; the defaults when it is not given.
        out_dir: Where to write; `data/geo/plates/<id>/` by default.
        labels: The resolved labels, when the caller has them. They are hashed
            into the manifest so a label plate painted from them can be told
            from a stale one. This module never resolves or places a label
            itself: `labels.py` imports from here and never the other way.
        key: The activity, written into the manifest as its `id`.
        style_digest: The digest of the style groups the base plates read,
            hashed into the manifest with the basemap.

    Returns:
        The plates, with their manifest: files, byte counts, timings and the
        darkness grid.
    """
    from pyntpot.maps.plates import DarkGrid, Manifest, Plates

    style = style or PaintStyle()
    aid = key
    out_dir = out_dir if out_dir is not None else plates_dir(aid)
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()

    card, layers = basemap.card, basemap.layers
    cx0, cy0, cx1, cy1 = card.box
    rw, rh = card.render
    plate = Plate(cx0, cy0, cx1, cy1, rw, rh)
    mpp = card.mpp
    sheet = Sheet(
        rh,
        rw,
        gran_px=max(layers.gran_m / mpp, 3.0),
        seed=style.sheet_seed,
        fibre=style.paper_fibre_mix if style.paper_fibre else 0.0,
        fibre_stretch=style.paper_fibre_stretch,
        fibre_angle=style.paper_fibre_angle,
        fibre_cell=max(style.paper_fibre_cell_px * rw / 1800.0, 1.6),
    )
    scale = rw / max(card.display[0], 1)
    # The phase 1 options, gathered once so every wash on this plate is laid the
    # same way: the granulation, the rim and the blooms, and the shared wet map.
    gran_gamma = style.gran_gamma if style.paper_fibre else 0.0
    rim_cov = max(5.0, 90.0 / mpp)
    flow = (
        (style.flow_rim_exp, style.flow_rim_ref_frac, style.flow_rim_frac)
        if style.flow_rim
        else None
    )
    bloom_rng = np.random.default_rng(style.bloom_seed) if style.blooms else None

    def bloom_arg(cov: np.ndarray) -> tuple | None:
        """The bloom argument for one wash, sized against its own area.

        `bloom_strength` scales the lift, which is the one number the whole
        bloom is built from: the centre gives up that share of its pigment and
        the ridge is laid from what the centre gave up. So one multiplier
        turns a demonstration of a backrun into a mark on the paper.
        """
        if bloom_rng is None or style.bloom_density <= 0:
            return None
        area = float((cov > 0.5).sum())
        n = int(
            np.clip(
                round(style.bloom_density * math.sqrt(area) / 260.0),
                1 if area > 400 else 0,
                style.bloom_max,
            )
        )
        lift = style.bloom_lift * max(style.bloom_strength, 0.0)
        return (bloom_rng, n, style.bloom_radius_frac, lift, style.bloom_warp) if n else None

    # ---- water first: it is cut out of every land pigment
    sea_rings = _lines(layers.sea)
    lake_rings = _lines(layers.lakes)
    sea_cov = fill_cov(sea_rings, plate) if sea_rings else np.zeros((rh, rw), F32)
    lake_cov = fill_cov(lake_rings, plate) if lake_rings else np.zeros((rh, rw), F32)
    water = np.maximum(sea_cov, lake_cov) > 0.5
    t_water = time.perf_counter()

    # ---- land cover: one label per pixel, so two land pigments cannot stack.
    # The outlines are deformed here, in metres, before anything is rasterised:
    # it is polygon work rather than pixel work, and the surveyed coast and the
    # lakes above are already filled, so neither of them is touched by it.
    cover_deform: Deform | None = None
    if style.silhouette_deform:
        floor_m, mult = style.silhouette_deform_max_m
        cover_deform = (
            np.random.default_rng(style.silhouette_deform_seed),
            style.silhouette_deform_amount,
            int(style.silhouette_deform_depth),
            style.silhouette_deform_decay,
            max(floor_m, mult * mpp),
            style.silhouette_deform_min_px * mpp,
        )
    order = [c for c in layers.cover_order if c in layers.cover]
    label = np.zeros((rh, rw), np.uint8)
    if style.land_cover:
        for i, cls in enumerate(order, 1):
            rings = _lines(layers.cover[cls])
            if rings:
                label[fill_cov(deform_rings(rings, cover_deform), plate) > 0.5] = i
        label[water] = 0
    wood_i = order.index("wood") + 1 if "wood" in order else -1
    wood_mask = (label == wood_i) if (wood_i > 0 and style.land_cover) else np.zeros((rh, rw), bool)

    # One wet field over the union of the cover, not one per class. Inside it
    # the classes are wet at the same time, so they bleed into each other and
    # no boundary between two of them carries its own rim; the outer silhouette
    # of the land sits outside it and keeps the edge it should have.
    wet_map = None
    if style.wet_bleed and style.land_cover and label.any():
        back = max(rim_cov * style.wet_bleed_edge_mult, 4.0)
        dry = label == 0
        if style.wet_close_px > 0:
            # The classes do not abut: they meet along hairlines of unmapped
            # ground a pixel or two wide, so the union of the cover taken as it
            # stands is cut through by dry lines exactly where two washes meet,
            # and no bleed width can reach a seam. Closing the union over gaps
            # this wide first is what puts the seams under water; it is a
            # dilate and an erode by the same distance, so the land's outer
            # silhouette comes back where it was.
            gap = F32(style.wet_close_px)
            dry = ~(edt(~(edt(label > 0) <= gap)) > gap)
        wet_map = smoothstep(edt(dry) - F32(back), back)

    def transp(key: str) -> float:
        """What this pigment shows over black, as a share of over white."""
        return float(style.pigment_transparency.get(key, style.km_transparency))

    trimmed: list[Layer] = []
    if style.land_cover:
        for i, cls in enumerate(order, 1):
            base, pool = style.cover_cfg.get(cls, (0.5, 0.2))
            cov = (label == i).astype(F32)
            if cov.any():
                trimmed.extend(
                    separated(
                        wash(
                            cov,
                            sheet,
                            base,
                            pool,
                            rim_px=rim_cov,
                            wet=wet_map,
                            bleed_px=style.wet_bleed_px,
                            bleed_mix=style.wet_bleed_mix,
                            rim_drop=style.wet_rim_drop,
                            gran_gamma=gran_gamma,
                            flow=flow,
                            blooms=bloom_arg(cov),
                        ),
                        cls,
                        rgb(style.pigments[cls]),
                        transp(cls),
                        sheet,
                        style,
                    )
                )
    else:
        pale = 1.0 - np.maximum(sea_cov, 0.0)
        trimmed.append(
            (
                wash(
                    pale,
                    sheet,
                    style.pale_base,
                    style.pale_pool,
                    rim_px=max(6.0, 120.0 / mpp),
                    gran_gamma=gran_gamma,
                    flow=flow,
                    blooms=bloom_arg(pale),
                ),
                rgb(style.pigments["pale"]),
                transp("pale"),
            )
        )
    t_cover = time.perf_counter()

    # ---- the wood, as a texture and a scatter of dabs. Both cross fade over
    # three printed scales, because a texture's scale cannot be changed after it
    # is printed; the two sliders walk between them.
    rng = np.random.default_rng(style.dither_seed)
    blotch_px = max(layers.blotch_m / mpp, 6.0)
    for weight, (sc, strength) in zip(
        _crossfade(style.wood_texture, len(style.wood_tex_scales)),
        zip(style.wood_tex_scales, style.wood_tex_strengths, strict=True),
        strict=True,
    ):
        if weight <= 0.002 or not wood_mask.any():
            continue
        field_n = fbm(rh, rw, blotch_px * sc, 3, rng)
        dens = np.clip((field_n - 0.40) * 1.7, 0, 1) * wood_mask * strength * weight
        trimmed.append((blur(dens, 2.0), rgb(style.pigments["wood"]), transp("wood")))

    dab_px = max(layers.dab_spacing_m / mpp, 26.0)
    for weight, (spacing, strength) in zip(
        _crossfade(style.wood_dabs, len(style.dab_spacings)),
        zip(style.dab_spacings, style.dab_strengths, strict=True),
        strict=True,
    ):
        if weight <= 0.002 or not wood_mask.any():
            continue
        step = max(int(dab_px * spacing), 8)
        dabs = np.zeros((rh, rw), F32)
        gy, gx = np.meshgrid(
            np.arange(step // 2, rh, step), np.arange(step // 2, rw, step), indexing="ij"
        )
        jy = np.clip((gy + (rng.random(gy.shape) - 0.5) * step * 0.7).astype(np.int32), 0, rh - 1)
        jx = np.clip((gx + (rng.random(gx.shape) - 0.5) * step * 0.7).astype(np.int32), 0, rw - 1)
        keep = wood_mask[jy, jx]
        if not keep.any():
            continue
        dabs[jy[keep], jx[keep]] = 1.0
        dab_r = max(step * 0.17, 4.0)
        dens = np.clip(blur(dabs, dab_r) * (dab_r**2) * 1.5, 0, 1) * wood_mask
        trimmed.append((dens * strength * weight, rgb(style.pigments["wood"]), transp("wood")))
    t_wood = time.perf_counter()

    # ---- lakes are trimmed with the rest of the land cover, so a reservoir two
    # valleys away does not float on the paper. The sea is not.
    if lake_cov.any():
        trimmed.append(
            (
                wash(
                    lake_cov,
                    sheet,
                    0.62,
                    0.32,
                    wobble=2.4,
                    dry=1.2,
                    rim_px=max(5.0, 70.0 / mpp),
                    gran=0.22,
                    gran_gamma=gran_gamma,
                    flow=flow,
                    blooms=bloom_arg(lake_cov),
                ),
                rgb(style.pigments["water"]),
                transp("water"),
            )
        )
    if style.relief and layers.elevation is not None:
        trimmed.append(
            (
                relief_density(layers.elevation, plate, sheet),
                rgb(style.pigments["relief"]),
                transp("relief"),
            )
        )
    t_relief = time.perf_counter()

    # ---- one bounded shallow-water pass over everything the ribbon carries,
    # on a quarter-resolution grid. It is run once for the whole sheet rather
    # than once a class, which is the point of it: the water does not know
    # where one wash stops and the next begins, so the drying runs across a
    # class boundary the way it does on paper. What comes back multiplies the
    # densities that are already there.
    if style.fluid_pass and trimmed:
        wet_all = (
            np.clip((label != 0).astype(F32) + lake_cov, 0.0, 1.0)
            if style.land_cover
            else np.clip(1.0 - sea_cov, 0.0, 1.0)
        )
        trimmed = fluid_modulate(trimmed, wet_all, sheet, style)
    t_fluid = time.perf_counter()

    # ---- the ink. Roads and watercourses are painted with the same machinery
    # as the wash: no vector stroke is drawn over the top.
    br = plate_brushes(style, scale, dict(layers.wet_px))
    ink_rng = np.random.default_rng(style.ink_seed)
    untrimmed: list[Layer] = []

    def lines_of(line: Line) -> list[np.ndarray]:
        return [plate.px(r) for r in _lines((line,))]

    # Every watercourse lands in the one pad and is read back with the major
    # river's brush, so the reservoir and the break texture are collected
    # against that brush too.
    water_pad = InkPad((rh, rw), br["major"][0], style)
    water_lines: list[tuple[Brush, np.ndarray]] = []
    # A watercourse is drawn at its own width where the payload measured one,
    # so a large river is a quarter of a kilometre wide on the sheet because it is
    # a quarter of a kilometre wide on the ground. The class still chooses the
    # brush and the ink; only how wide it is laid down comes from the river. The
    # pad itself is still read back through the class brush, so the reservoir
    # and the break texture of the water layer are what they always were.
    wide: dict[tuple[str, float], Brush] = {}
    profiles: list[np.ndarray | None] = []
    for r in layers.rivers:
        cls = r.cls
        brush, _hex = br.get(cls, br["minor"])
        px = float(r.width_px or 0.0) * style.river_mult
        if px > brush.width / scale:
            key = (cls, round(px, 2))
            if key not in wide:
                wide[key] = brush_from_id(style.brushes[cls], px, scale, style, cls)[0]
            brush = wide[key]
        # `wp` is the width along the river as a share of its widest point, so
        # an estuary narrows to a channel over its own length instead of being
        # drawn at one width throughout. The brush is built at the widest and
        # the profile only ever takes ink away.
        prof = r.profile
        for line in lines_of(r.line):
            water_lines.append((brush, line))
            profiles.append(np.asarray(prof, F32) if prof else None)
    water_pad.lay(water_lines, ink_rng, profiles=profiles)
    # The coast is chained rather than profiled: it is one line round the land,
    # cut into ways, and it has no width of its own to vary.
    coast_lines = [(br["coast"][0], line) for coast in layers.coastline for line in lines_of(coast)]
    if coast_lines:
        water_pad.lay(coast_lines, ink_rng)
    if water_pad.any():
        untrimmed.append((water_pad.read(br["major"][0], sheet), rgb(br["major"][1])))
    for key in ("road_major", "lane", "track"):
        if key != "road_major" and not layers.minor_roads:
            continue
        band = {"road_major": "major", "lane": "minor", "track": "path"}[key]
        pad = InkPad((rh, rw), br[key][0], style)
        pad.lay(
            [
                (br[key][0], line)
                for r in layers.roads
                if r.band == band
                for line in lines_of(r.line)
            ],
            ink_rng,
        )
        if pad.any():
            untrimmed.append((pad.read(br[key][0], sheet), rgb(br[key][1])))
    t_ink = time.perf_counter()

    # ---- the ribbon, and the card
    route_mask = stroke_mask([list(layers.route)], plate, 2.0)
    d_route = edt(route_mask)
    tear_px = max(rw * style.ribbon_tear_frac, style.ribbon_tear_floor_px)
    land = None
    if style.coast_hard_mask and sea_cov.any():
        # The land side of the surveyed coast, antialiased by one pixel, no more.
        land = np.clip(1.0 - blur(sea_cov, 0.8) * 1.6, 0.0, 1.0)
    r_px = layers.ribbon_m / mpp
    alpha, rim = ribbon_alpha(d_route, r_px, sheet, style.ribbon_fill, tear_px, land)

    # The stack is laid over white, because the page multiplies the wash plate
    # over the card; the ribbon then fades the ground out toward the tear, and
    # the sea, the rim and the ink go on top of what is left.
    ground = composite(trimmed, np.ones((rh, rw, 3), F32), style)
    ground = 1.0 - alpha[..., None] * (1.0 - ground)
    over: list[Layer] = []
    if sea_cov.any() and style.sea_to_edge:
        sea_dens = wash(
            sea_cov,
            sheet,
            0.60,
            0.34,
            wobble=2.0,
            dry=1.0,
            rim_px=max(6.0, 110.0 / mpp),
            gran=0.22,
            gran_gamma=gran_gamma,
            flow=flow,
            blooms=bloom_arg(sea_cov),
        )
        if style.sea_variation:
            sea_dens = sea_patches(sea_dens, sea_cov, mpp, style)
        over.append((sea_dens, rgb(style.pigments["water"]), transp("water")))
    over.append(
        (np.clip(rim * style.rim_strength, 0, 1), rgb(style.pigments["rim"]), transp("rim"))
    )
    over.extend(untrimmed)
    wash_plate = composite(over, ground, style)
    paper = paper_plate(sheet, plate, style)
    t_end = time.perf_counter()

    files, sizes = {}, {}
    for name, arr, quality in (
        ("paper", paper, style.paper_quality),
        ("wash", wash_plate, style.webp_quality),
    ):
        path = out_dir / f"{name}.webp"
        sizes[name] = save_webp(to_img(arr, rng), path, quality, style.plate_lossless)
        files[name] = path.name
    if style.route_pen:
        # The one route style that is not vector: the route drawn with the same
        # brush engine, as alpha the page tints with whatever ink it is set to.
        pen_brush, _ = brush_from_id(
            style.route_pen_brush, style.route_pen_width_px, scale, style, "route"
        )
        pen_pad = InkPad((rh, rw), pen_brush, style)
        pen_pad.lay(
            [(pen_brush, plate.px(list(layers.route)))], np.random.default_rng(style.ink_seed + 1)
        )
        path = out_dir / "pen.webp"
        sizes["pen"] = save_alpha(
            pen_pad.read(pen_brush, sheet), path, lossless=style.plate_lossless
        )
        files["pen"] = path.name

    # ---- a coarse map of how dark the sheet is, so a label can be placed on
    # light ground rather than across a wood.
    lum = (paper * wash_plate).mean(axis=2)
    gw, gh = style.dark_grid
    ys = np.linspace(0, rh, gh + 1).astype(int)
    xs = np.linspace(0, rw, gw + 1).astype(int)
    dark = [
        [round(float(1.0 - lum[ys[r] : ys[r + 1], xs[c] : xs[c + 1]].mean()), 3) for c in range(gw)]
        for r in range(gh)
    ]

    manifest = Manifest(
        key=aid,
        hash=paint_hash(basemap, style_digest),
        # The first track point in the painter's own metre space, so a caller
        # whose projection took a different origin can pin the two together.
        route0=layers.route[0],
        files=files,
        sizes=sizes,
        bytes=sum(sizes.values()),
        card=card,
        ribbon_m=layers.ribbon_m,
        span_m=basemap.span_m,
        places=tuple(basemap.places),
        candidates=tuple(basemap.candidates),
        # The named lines a label can be set along, which are in the geo payload
        # and nowhere else once this returns.
        label_geom=label_geom(basemap, style.label_geom_tol_px),
        # How wide each class of watercourse was actually painted, in display
        # pixels, so a river's name can be set clear of its own water rather
        # than in it. The label layer has no other way to know: it sees the
        # centreline and not the brush that was run along it.
        wet_px=dict(layers.wet_px),
        # The paper the ink was gated on, so a plate painted later gates on the
        # same sheet rather than on a second one that only looks similar.
        gran_px=round(max(layers.gran_m / mpp, 3.0), 3),
        labels_hash=labels_hash(labels, style),
        sources=tuple(basemap.sources),
        dark=DarkGrid(w=gw, h=gh, values=tuple(tuple(row) for row in dark)),
        wood_px=int(wood_mask.sum()),
        water_px=int(water.sum()),
        timing={
            "water_ms": round((t_water - t0) * 1000),
            "cover_ms": round((t_cover - t_water) * 1000),
            "wood_ms": round((t_wood - t_cover) * 1000),
            "relief_ms": round((t_relief - t_wood) * 1000),
            "fluid_ms": round((t_fluid - t_relief) * 1000),
            "ink_ms": round((t_ink - t_fluid) * 1000),
            "ribbon_ms": round((t_end - t_ink) * 1000),
            "total_ms": round((time.perf_counter() - t0) * 1000),
        },
    )
    (out_dir / "plates.json").write_text(manifest.to_json())
    return Plates(out_dir, manifest)


def _crossfade(value: float, n: int) -> list[float]:
    """Weights across `n` printed scales for a slider at `value` in 0 to 1.

    The same walk the exploration page's sliders make, so a value chosen
    there paints the blend that was previewed.
    """
    if n <= 1:
        return [max(0.0, min(1.0, value))]
    pos = max(0.0, min(1.0, value)) * (n - 1)
    gate = min(1.0, max(0.0, value) * 4.0)
    return [max(0.0, 1.0 - abs(pos - i)) * gate for i in range(n)]


def paint_activity(
    key: str,
    lat: list[float],
    lng: list[float],
    style: Style,
    *,
    cache_dir: Path,
    places: list[dict[str, Any]],
    force: bool = False,
) -> Plates | None:
    """Assemble the layers for one activity and paint them, unless they are current.

    Args:
        key: The activity, naming both the geo cache and the plates.
        lat: Track latitudes.
        lng: Track longitudes.
        style: The style: its flat painter style paints, its basemap group says
            what the basemap draws, and its base digest goes into the hash.
        cache_dir: Where the OSM, SRTM and land cover payloads live, and where
            the plates are written under `plates/`.
        places: The places to mark on the sheet.
        force: Repaint even when the cached plates match.

    Returns:
        The plates, freshly painted or already current, or None when there is
        nothing cached for this box.
    """
    from pyntpot._port import geo

    pstyle = style.paint_style()
    basemap = geo.journal_layers(
        key,
        lat,
        lng,
        pstyle,
        cache_dir=cache_dir,
        places=places,
        basemap_style=style.basemap,
    )
    if basemap is None:
        return None
    out_dir = plates_dir(key, cache_dir)
    digest = style.base_digest()
    want = paint_hash(basemap, digest)
    existing = load_plates(key, cache_dir)
    if existing is not None and existing.hash == want and not force:
        return existing
    return paint(basemap, pstyle, out_dir, key=key, style_digest=digest)


def with_display(style: PaintStyle, display_px: int) -> PaintStyle:
    """The same style at a different display width."""
    return replace(style, display_px=display_px)
