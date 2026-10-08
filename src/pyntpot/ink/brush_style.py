"""The brush: what the ink engine draws a stroke with.

Key type: `BrushStyle`, the ink seed, the widths and treatments of each class
of line, and the bristle, reservoir and stroke-quality settings of the brush
itself. A frozen dataclass of plain values, each field documented by its `#:`
comment.

It draws nothing and reads no theme. The defaults are the painter's own class
defaults, not a resolved theme. The paper and the wash live in
`pyntpot.ink.style`.

Invariants: every field belongs to exactly one style group across the
package; the module imports nothing outside `ink`.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BrushStyle:
    """The brushes: which brush each line class takes, how wide, and how it behaves.

    The reservoir, directional dry brush and stroke-quality switches are off
    or inert by default, until a theme turns one on; `ink_ss`,
    `bristle_bandlimit_px` and `bristle_drift_coherence` are the exceptions
    and are on.
    """

    #: Seeds, so the same box paints the same plate every time.
    ink_seed: int = 91
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
    #: track used: a lane is a pen, a track is the dry broken brush.
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
    #: Ink starvation with reload. Each bristle sets off with its own load,
    #: spends it with distance along the stroke, faster under more pressure,
    #: and the paper gate tightens as the load falls, so a long lane starts
    #: loaded and breaks into skips that run along the mark rather than
    #: everywhere at once.
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
    #: Non-repeating drift. Off the flag every wander in a stroke is a sine, so
    #: a long mark repeats itself: the bristle drift at 390 render pixels and shared by
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
    #: The coarsest feature, as a share of the sine's own wavelength. At 0.5 a
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
    #: same number from 0.447 to 0.414, which is nothing. 0 leaves the tip
    #: unsmoothed. The lanes a mark is genuinely wide enough to show survive
    #: it: the major river at 16.8 px keeps its own.
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
    #: the next, are the tip folded over itself: at 0 every bristle's drift phase
    #: is drawn independently of the one beside it, so two neighbours can be
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
    #: independently, from a normal draw, and turns neither of those on.
    bristle_drift_coherence: float = 0.25
