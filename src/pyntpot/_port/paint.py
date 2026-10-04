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
from dataclasses import asdict, dataclass, field, fields, replace
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

from pyntpot._port.style import coerce_like
from pyntpot.ink.brush import Brush, brush_from_id
from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.io import save_alpha, save_webp, to_img
from pyntpot.ink.noise import F32, blur, edt, fbm, fbm_aniso, fill_holes, smoothstep
from pyntpot.ink.pad import InkPad
from pyntpot.ink.pigment import PIGMENTS, TRANSPARENCY, Layer, composite
from pyntpot.ink.raster import Deform, deform_rings, fill_cov, stroke_mask
from pyntpot.ink.sheet import PAPER, Canvas, Sheet, rgb
from pyntpot.ink.wash import WashOptions, fluid_modulate, separated, wash

if TYPE_CHECKING:
    from pyntpot.maps.basemap import Basemap, ElevationPatch, Line
    from pyntpot.maps.plates import Plates
    from pyntpot.maps.style import Style

Pt = tuple[float, float]
#: Painted plates live inside the geo cache, one directory per activity, so a
#: caller that redirects the cache redirects the plates with it.
PLATES_SUBDIR = "plates"

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
    #: How far a named road or watercourse is simplified before a label is set
    #: along it, in display pixels.
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


# --------------------------------------------------------------------------- washes


def relief_density(grid: ElevationPatch, plate: Canvas, sheet: Sheet) -> np.ndarray:
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


def plate_brushes(
    style: BrushStyle, scale: float, wet_px: dict[str, float]
) -> dict[str, tuple[Brush, str]]:
    """Every class's brush for one plate, sized against its own display pixel.

    Args:
        style: The brush style.
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


def paper_plate(sheet: Sheet, plate: Canvas, style: PaintStyle) -> np.ndarray:
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


# --------------------------------------------------------------------------- lettering


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


def labels_hash(labels: list[dict[str, Any]] | None, style: PaintStyle) -> str:
    """A hash over what is lettered and how, so a stale label plate is caught.

    The picks live in the analysis payload, not the geo payload, so `paint_hash`
    cannot see them and a plate keyed on it alone would letter yesterday's names
    over today's map. The label plate is keyed on this, so a plate lettered
    from other names or another hand is never drawn.

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
            (h, w), max(cell * 0.22, 3.0), 2, rng, max(style.sea_variation_elong, 1.0), angle
        )
        swing = swing + streak_w * centred(streak) * np.exp(-d_sea / F32(band))
        swing /= 1.0 + streak_w
    return np.clip(dens * (1.0 + amount * swing), 0.0, 1.0)


def _lines(lines: tuple[Line, ...]) -> list[list[Pt]]:
    """The lines long enough to draw, as the point lists the painter fills and strokes."""
    return [list(line) for line in lines if len(line) > 1]


def paint(
    basemap: Basemap,
    style: Style,
    out_dir: Path | None = None,
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
        pstyle: The paint pstyle; the defaults when it is not given.
        out_dir: Where to write; `data/geo/plates/<id>/` by default.
        key: The activity, naming the default plates directory.
        style_digest: The digest of the pstyle groups the base plates read,
            hashed into the manifest with the basemap.

    Returns:
        The plates, with their manifest: files, byte counts, measurements and
        the darkness grid.
    """
    from pyntpot.maps.plates import DarkGrid, Manifest, Plates

    pstyle = style.paint_style()
    aid = key
    out_dir = out_dir if out_dir is not None else plates_dir(aid)
    out_dir.mkdir(parents=True, exist_ok=True)

    card, layers = basemap.card, basemap.layers
    cx0, cy0, cx1, cy1 = card.box
    rw, rh = card.render
    plate = Canvas(cx0, cy0, cx1, cy1, rw, rh)
    mpp = card.mpp
    sheet = Sheet(
        rh,
        rw,
        gran_px=max(layers.gran_m / mpp, 3.0),
        seed=pstyle.sheet_seed,
        fibre=pstyle.paper_fibre_mix if pstyle.paper_fibre else 0.0,
        fibre_stretch=pstyle.paper_fibre_stretch,
        fibre_angle=pstyle.paper_fibre_angle,
        fibre_cell=max(pstyle.paper_fibre_cell_px * rw / 1800.0, 1.6),
    )
    scale = rw / max(card.display[0], 1)
    # The phase 1 options, gathered once so every wash on this plate is laid the
    # same way: the granulation, the rim and the blooms, and the shared wet map.
    gran_gamma = pstyle.gran_gamma if pstyle.paper_fibre else 0.0
    rim_cov = max(5.0, 90.0 / mpp)
    flow = (
        (pstyle.flow_rim_exp, pstyle.flow_rim_ref_frac, pstyle.flow_rim_frac)
        if pstyle.flow_rim
        else None
    )
    bloom_rng = np.random.default_rng(pstyle.bloom_seed) if pstyle.blooms else None

    def bloom_arg(cov: np.ndarray) -> tuple | None:
        """The bloom argument for one wash, sized against its own area.

        `bloom_strength` scales the lift, which is the one number the whole
        bloom is built from: the centre gives up that share of its pigment and
        the ridge is laid from what the centre gave up. So one multiplier
        turns a demonstration of a backrun into a mark on the paper.
        """
        if bloom_rng is None or pstyle.bloom_density <= 0:
            return None
        area = float((cov > 0.5).sum())
        n = int(
            np.clip(
                round(pstyle.bloom_density * math.sqrt(area) / 260.0),
                1 if area > 400 else 0,
                pstyle.bloom_max,
            )
        )
        lift = pstyle.bloom_lift * max(pstyle.bloom_strength, 0.0)
        return (bloom_rng, n, pstyle.bloom_radius_frac, lift, pstyle.bloom_warp) if n else None

    # ---- water first: it is cut out of every land pigment
    sea_rings = _lines(layers.sea)
    lake_rings = _lines(layers.lakes)
    sea_cov = fill_cov(sea_rings, plate) if sea_rings else np.zeros((rh, rw), F32)
    lake_cov = fill_cov(lake_rings, plate) if lake_rings else np.zeros((rh, rw), F32)
    water = np.maximum(sea_cov, lake_cov) > 0.5

    # ---- land cover: one label per pixel, so two land pigments cannot stack.
    # The outlines are deformed here, in metres, before anything is rasterised:
    # it is polygon work rather than pixel work, and the surveyed coast and the
    # lakes above are already filled, so neither of them is touched by it.
    cover_deform: Deform | None = None
    if pstyle.silhouette_deform:
        floor_m, mult = pstyle.silhouette_deform_max_m
        cover_deform = (
            np.random.default_rng(pstyle.silhouette_deform_seed),
            pstyle.silhouette_deform_amount,
            int(pstyle.silhouette_deform_depth),
            pstyle.silhouette_deform_decay,
            max(floor_m, mult * mpp),
            pstyle.silhouette_deform_min_px * mpp,
        )
    order = [c for c in layers.cover_order if c in layers.cover]
    label = np.zeros((rh, rw), np.uint8)
    if pstyle.land_cover:
        for i, cls in enumerate(order, 1):
            rings = _lines(layers.cover[cls])
            if rings:
                label[fill_cov(deform_rings(rings, cover_deform), plate) > 0.5] = i
        label[water] = 0
    wood_i = order.index("wood") + 1 if "wood" in order else -1
    wood_mask = (
        (label == wood_i) if (wood_i > 0 and pstyle.land_cover) else np.zeros((rh, rw), bool)
    )

    # One wet field over the union of the cover, not one per class. Inside it
    # the classes are wet at the same time, so they bleed into each other and
    # no boundary between two of them carries its own rim; the outer silhouette
    # of the land sits outside it and keeps the edge it should have.
    wet_map = None
    if pstyle.wet_bleed and pstyle.land_cover and label.any():
        back = max(rim_cov * pstyle.wet_bleed_edge_mult, 4.0)
        dry = label == 0
        if pstyle.wet_close_px > 0:
            # The classes do not abut: they meet along hairlines of unmapped
            # ground a pixel or two wide, so the union of the cover taken as it
            # stands is cut through by dry lines exactly where two washes meet,
            # and no bleed width can reach a seam. Closing the union over gaps
            # this wide first is what puts the seams under water; it is a
            # dilate and an erode by the same distance, so the land's outer
            # silhouette comes back where it was.
            gap = F32(pstyle.wet_close_px)
            dry = ~(edt(~(edt(label > 0) <= gap)) > gap)
        wet_map = smoothstep(edt(dry) - F32(back), back)

    def transp(key: str) -> float:
        """What this pigment shows over black, as a share of over white."""
        return float(pstyle.pigment_transparency.get(key, pstyle.km_transparency))

    trimmed: list[Layer] = []
    if pstyle.land_cover:
        for i, cls in enumerate(order, 1):
            base, pool = pstyle.cover_cfg.get(cls, (0.5, 0.2))
            cov = (label == i).astype(F32)
            if cov.any():
                trimmed.extend(
                    separated(
                        wash(
                            cov,
                            sheet,
                            base,
                            pool,
                            WashOptions(
                                rim_px=rim_cov,
                                wet=wet_map,
                                bleed_px=pstyle.wet_bleed_px,
                                bleed_mix=pstyle.wet_bleed_mix,
                                rim_drop=pstyle.wet_rim_drop,
                                gran_gamma=gran_gamma,
                                flow=flow,
                                blooms=bloom_arg(cov),
                            ),
                        ),
                        cls,
                        rgb(pstyle.pigments[cls]),
                        transp(cls),
                        sheet,
                        style.wash,
                    )
                )
    else:
        pale = 1.0 - np.maximum(sea_cov, 0.0)
        trimmed.append(
            (
                wash(
                    pale,
                    sheet,
                    pstyle.pale_base,
                    pstyle.pale_pool,
                    WashOptions(
                        rim_px=max(6.0, 120.0 / mpp),
                        gran_gamma=gran_gamma,
                        flow=flow,
                        blooms=bloom_arg(pale),
                    ),
                ),
                rgb(pstyle.pigments["pale"]),
                transp("pale"),
            )
        )

    # ---- the wood, as a texture and a scatter of dabs. Both cross fade over
    # three printed scales, because a texture's scale cannot be changed after it
    # is printed; the two sliders walk between them.
    rng = np.random.default_rng(pstyle.dither_seed)
    blotch_px = max(layers.blotch_m / mpp, 6.0)
    for weight, (sc, strength) in zip(
        _crossfade(pstyle.wood_texture, len(pstyle.wood_tex_scales)),
        zip(pstyle.wood_tex_scales, pstyle.wood_tex_strengths, strict=True),
        strict=True,
    ):
        if weight <= 0.002 or not wood_mask.any():
            continue
        field_n = fbm(rh, rw, blotch_px * sc, 3, rng)
        dens = np.clip((field_n - 0.40) * 1.7, 0, 1) * wood_mask * strength * weight
        trimmed.append((blur(dens, 2.0), rgb(pstyle.pigments["wood"]), transp("wood")))

    dab_px = max(layers.dab_spacing_m / mpp, 26.0)
    for weight, (spacing, strength) in zip(
        _crossfade(pstyle.wood_dabs, len(pstyle.dab_spacings)),
        zip(pstyle.dab_spacings, pstyle.dab_strengths, strict=True),
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
        trimmed.append((dens * strength * weight, rgb(pstyle.pigments["wood"]), transp("wood")))

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
                    WashOptions(
                        wobble=2.4,
                        dry=1.2,
                        rim_px=max(5.0, 70.0 / mpp),
                        gran=0.22,
                        gran_gamma=gran_gamma,
                        flow=flow,
                        blooms=bloom_arg(lake_cov),
                    ),
                ),
                rgb(pstyle.pigments["water"]),
                transp("water"),
            )
        )
    if pstyle.relief and layers.elevation is not None:
        trimmed.append(
            (
                relief_density(layers.elevation, plate, sheet),
                rgb(pstyle.pigments["relief"]),
                transp("relief"),
            )
        )

    # ---- one bounded shallow-water pass over everything the ribbon carries,
    # on a quarter-resolution grid. It is run once for the whole sheet rather
    # than once a class, which is the point of it: the water does not know
    # where one wash stops and the next begins, so the drying runs across a
    # class boundary the way it does on paper. What comes back multiplies the
    # densities that are already there.
    if pstyle.fluid_pass and trimmed:
        wet_all = (
            np.clip((label != 0).astype(F32) + lake_cov, 0.0, 1.0)
            if pstyle.land_cover
            else np.clip(1.0 - sea_cov, 0.0, 1.0)
        )
        trimmed = fluid_modulate(trimmed, wet_all, sheet, style.wash)

    # ---- the ink. Roads and watercourses are painted with the same machinery
    # as the wash: no vector stroke is drawn over the top.
    br = plate_brushes(style.brush, scale, dict(layers.wet_px))
    ink_rng = np.random.default_rng(pstyle.ink_seed)
    untrimmed: list[Layer] = []

    def lines_of(line: Line) -> list[np.ndarray]:
        return [plate.px(r) for r in _lines((line,))]

    # Every watercourse lands in the one pad and is read back with the major
    # river's brush, so the reservoir and the break texture are collected
    # against that brush too.
    water_pad = InkPad((rh, rw), br["major"][0], style.brush)
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
        px = float(r.width_px or 0.0) * pstyle.river_mult
        if px > brush.width / scale:
            key = (cls, round(px, 2))
            if key not in wide:
                wide[key] = brush_from_id(style.brush.brushes[cls], px, scale, style.brush, cls)[0]
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
        pad = InkPad((rh, rw), br[key][0], style.brush)
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

    # ---- the ribbon, and the card
    route_mask = stroke_mask([list(layers.route)], plate, 2.0)
    d_route = edt(route_mask)
    tear_px = max(rw * pstyle.ribbon_tear_frac, pstyle.ribbon_tear_floor_px)
    land = None
    if pstyle.coast_hard_mask and sea_cov.any():
        # The land side of the surveyed coast, antialiased by one pixel, no more.
        land = np.clip(1.0 - blur(sea_cov, 0.8) * 1.6, 0.0, 1.0)
    r_px = layers.ribbon_m / mpp
    alpha, rim = ribbon_alpha(d_route, r_px, sheet, pstyle.ribbon_fill, tear_px, land)

    # The stack is laid over white, because the page multiplies the wash plate
    # over the card; the ribbon then fades the ground out toward the tear, and
    # the sea, the rim and the ink go on top of what is left.
    ground = composite(trimmed, np.ones((rh, rw, 3), F32), style.paper)
    ground = 1.0 - alpha[..., None] * (1.0 - ground)
    over: list[Layer] = []
    if sea_cov.any() and pstyle.sea_to_edge:
        sea_dens = wash(
            sea_cov,
            sheet,
            0.60,
            0.34,
            WashOptions(
                wobble=2.0,
                dry=1.0,
                rim_px=max(6.0, 110.0 / mpp),
                gran=0.22,
                gran_gamma=gran_gamma,
                flow=flow,
                blooms=bloom_arg(sea_cov),
            ),
        )
        if pstyle.sea_variation:
            sea_dens = sea_patches(sea_dens, sea_cov, mpp, pstyle)
        over.append((sea_dens, rgb(pstyle.pigments["water"]), transp("water")))
    over.append(
        (np.clip(rim * pstyle.rim_strength, 0, 1), rgb(pstyle.pigments["rim"]), transp("rim"))
    )
    over.extend(untrimmed)
    wash_plate = composite(over, ground, style.paper)
    paper = paper_plate(sheet, plate, pstyle)

    files, sizes = {}, {}
    for name, arr, quality in (
        ("paper", paper, pstyle.paper_quality),
        ("wash", wash_plate, pstyle.webp_quality),
    ):
        path = out_dir / f"{name}.webp"
        sizes[name] = save_webp(to_img(arr, rng), path, quality, lossless=pstyle.plate_lossless)
        files[name] = path.name
    if pstyle.route_pen:
        # The one route pstyle that is not vector: the route drawn with the same
        # brush engine, as alpha the page tints with whatever ink it is set to.
        pen_brush, _ = brush_from_id(
            pstyle.route_pen_brush, pstyle.route_pen_width_px, scale, style.brush, "route"
        )
        pen_pad = InkPad((rh, rw), pen_brush, style.brush)
        pen_pad.lay(
            [(pen_brush, plate.px(list(layers.route)))], np.random.default_rng(pstyle.ink_seed + 1)
        )
        path = out_dir / "pen.webp"
        sizes["pen"] = save_alpha(
            pen_pad.read(pen_brush, sheet), path, lossless=pstyle.plate_lossless
        )
        files["pen"] = path.name

    # ---- a coarse map of how dark the sheet is, so a label can be placed on
    # light ground rather than across a wood.
    lum = (paper * wash_plate).mean(axis=2)
    gw, gh = pstyle.dark_grid
    ys = np.linspace(0, rh, gh + 1).astype(int)
    xs = np.linspace(0, rw, gw + 1).astype(int)
    dark = [
        [round(float(1.0 - lum[ys[r] : ys[r + 1], xs[c] : xs[c + 1]].mean()), 3) for c in range(gw)]
        for r in range(gh)
    ]

    manifest = Manifest(
        hash=paint_hash(basemap, style_digest),
        files=files,
        sizes=sizes,
        bytes=sum(sizes.values()),
        card=card,
        ribbon_m=layers.ribbon_m,
        span_m=basemap.span_m,
        # How wide each class of watercourse was actually painted, in display
        # pixels, so a river's name can be set clear of its own water rather
        # than in it. The label layer has no other way to know: it sees the
        # centreline and not the brush that was run along it.
        wet_px=dict(layers.wet_px),
        # The paper the ink was gated on, so a plate painted later gates on the
        # same sheet rather than on a second one that only looks similar.
        gran_px=round(max(layers.gran_m / mpp, 3.0), 3),
        dark=DarkGrid(w=gw, h=gh, values=tuple(tuple(row) for row in dark)),
        wood_px=int(wood_mask.sum()),
        water_px=int(water.sum()),
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


def with_display(style: PaintStyle, display_px: int) -> PaintStyle:
    """The same style at a different display width."""
    return replace(style, display_px=display_px)
