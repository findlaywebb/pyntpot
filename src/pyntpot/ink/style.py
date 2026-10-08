"""The paper and the wash: what the ink engine lays paper and a wash with.

Key types: `PaperStyle`, the paper, its encoder and the compositing of the
pigment stack over it; `WashStyle`, how a wash wets, bleeds, rims, blooms,
separates and flows once it is down. Both are frozen dataclasses of plain
values, each field documented by its `#:` comment.

It paints nothing and reads no theme: a group is a value a painter is handed.
The defaults are the painter's own class defaults, not a resolved theme; the
theme supplies the values a painting is made with. The brush settings live in
`pyntpot.ink.brush_style`.

Invariants: every field belongs to exactly one style group across the
package; a group never imports anything outside `ink`.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PaperStyle:
    """The paper: its encoder, grid, paper, seed and the compositing over it.

    Read by the painter for every plate and by the lettering, which lays its
    backing wash on the same paper. The compositing and fibre fields are off
    or inert by default, until a theme turns one on.
    """

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
    #: setting. Off is the lossy encoder, and the two quality numbers below are
    #: what it uses; the plates are then about eighteen times smaller.
    plate_lossless: bool = True
    webp_quality: int = 74
    paper_quality: int = 80
    #: The notebook grid. Off by default.
    grid: bool = False
    grid_spacing_px: float = 26.0
    grid_opacity: float = 0.34
    paper_hex: str = "#f3ead6"
    #: Paper texture, the worn border, the vignette and the foxing.
    paper_tooth: float = 0.085
    paper_worn: float = 0.20
    paper_vignette: float = 0.05
    paper_foxing: float = 0.09
    #: Seeds, so the same box paints the same paper every time.
    sheet_seed: int = 11
    #: Kubelka-Munk glazing in place of multiply for the pigment stack. Multiply
    #: is transmission with no scattering, so two washes crossing lose chroma
    #: and go grey; Kubelka-Munk gives each pigment absorption and scattering
    #: derived from what it shows over white and over black, and composites the
    #: layers optically, so the greens and blues keep their hue where they meet.
    km_glazing: bool = False
    #: Per-pigment transparency, as `TRANSPARENCY`. Ink and anything unnamed
    #: takes the default below.
    pigment_transparency: dict[str, float] = field(
        default_factory=lambda: {
            "farmland": 0.1,
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
            "relief": 0.3,
            "rim": 0.18,
        }
    )
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


@dataclass(frozen=True)
class WashStyle:
    """How a laid wash behaves: wet bleed, flow rim, blooms, sea, silhouette, fluid.

    Every switch here is off or inert by default, until a theme turns one on.
    """

    #: One wet-area field shared across the land classes, so a wash knows another
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
    #: mass is the one edge that should stay hard, so the wet field has to end
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
    #: How wide a gap in the land cover the wet field closes over, in render
    #: pixels, before it backs off from the land's edge. Measured, not guessed:
    #: on a woodland plate the classes meet along hairlines of unmapped ground,
    #: the median class seam sits 2 px from one, and a wet field taken from the
    #: raw union is therefore punched full of holes exactly where two washes
    #: meet. At 5 px the share of seam that is wet goes from 0.00 to 0.58 while
    #: the dry share of the card moves 0.148 to 0.140, so the land's outer
    #: silhouette is where it was. 0 is the union as it stands.
    wet_close_px: float = 0.0
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
    #: is not thrown across the canvas on a wide box.
    silhouette_deform_max_m: tuple[float, float] = (16.0, 3.0)
    #: Where the recursion stops, in render pixels: a segment shorter than this
    #: is already below the wash's own edge noise.
    silhouette_deform_min_px: float = 1.6
    silhouette_deform_seed: int = 73
    #: Two-pigment washes. A real wood green is not one pigment: it is a
    #: staining green with a heavier blue-black in it, and the two separate as
    #: the wash dries, the heavy one settling into the paper's tooth while the
    #: light one floats over it. Curtis' pigment separation, as one
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
    #: One bounded shallow-water pass over the whole canvas, on a coarse grid:
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
