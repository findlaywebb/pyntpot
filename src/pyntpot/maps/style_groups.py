"""The map's own style groups, the route inks and the fields no painter reads.

Key types: `CardStyle` (the card's size and the dark grid),
`RibbonStyle` (the trimmed extent of the painted ground and the card's
frame), `CoverStyle` (land cover and the wood), `RouteStyle` (the route's
own painted plate), `BasemapStyle` (what the basemap draws and how much of
it), `LetteringPolicy` (which names a map letters), `RouteInk` (one sport's route
treatment) and `RouteInks` (one `RouteInk` per sport). `CONSUMER_ONLY` names the
painter fields that no module reads and so belong to no group.

Base groups feed the base plates; `LetteringPolicy` feeds only the lettering;
`RouteInks` is read only when the route is placed and drawn (`paint` takes the
strand gap from its width), so changing an ink repaints no plate. The defaults are the source classes' own defaults, not a
resolved theme: the effective basemap options and the resolved inks are
theme values. `RouteInks` has no defaults, because no class carries one.

It paints, letters and fetches nothing. Two `BasemapStyle` fields,
`hillshade_opacity` and `pick_places`, have no reader and are kept for the
upstream consumer. The basemap's clip margin is derived from the card per
render and is not a style field.

Invariants: every field belongs to exactly one style group across the
package.
"""

from dataclasses import dataclass, field
from typing import Any

#: The painter fields no module reads, kept by the upstream consumer and left
#: out of every group.
CONSUMER_ONLY: tuple[str, ...] = (
    "cover_order",
    "label_font",
    "label_pin_colour",
    "label_glow_colour",
)


@dataclass(frozen=True)
class CardStyle:
    """The card's display size, its supersampling, and the dark grid's size."""

    #: Display width of the card in CSS pixels; the height follows its aspect.
    #: 900 is the width the plates were set at, and it is what decides
    #: whether the lanes and the tracks are drawn: below it, a display pixel is
    #: more than eight metres of ground and a lane is not a mark.
    display_px: int = 900
    #: Painted at this multiple of the display size, so the grain survives a
    #: retina screen. 2 is what the plates were set at.
    supersample: int = 2
    #: Cells across and down of the dark grid the label placer scores against.
    dark_grid: tuple[int, int] = (80, 60)


@dataclass(frozen=True)
class RibbonStyle:
    """The ribbon: the trimmed extent of the painted ground, and the card around it."""

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


@dataclass(frozen=True)
class CoverStyle:
    """Land cover and the wood: the classes, their pigments, and the wood's texture and dabs.

    `land_cover` paints the cover classes, or the pale single wash when off;
    `relief` paints the relief from the elevation grid. `dither_seed` seeds the
    wood dabs.
    """

    #: Seeds, so the same box paints the same sheet every time.
    dither_seed: int = 23
    land_cover: bool = True
    relief: bool = True
    #: How dark a wash of each class goes, and how hard its edge pools.
    cover_cfg: dict[str, tuple[float, float]] = field(
        default_factory=lambda: {
            "farmland": (0.52, 0.2),
            "meadow": (0.55, 0.22),
            "orchard": (0.55, 0.24),
            "scrub": (0.58, 0.26),
            "heath": (0.6, 0.26),
            "sand": (0.5, 0.22),
            "rock": (0.52, 0.26),
            "wetland": (0.6, 0.28),
            "built": (0.55, 0.2),
            "works": (0.58, 0.22),
            "wood": (0.72, 0.3),
        }
    )
    #: Multiply colours: what a full-strength wash of each pigment transmits.
    pigments: dict[str, str] = field(
        default_factory=lambda: {
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
    )
    #: The pale single wash drawn instead of the classes when cover is off.
    pale_base: float = 0.50
    pale_pool: float = 0.16
    #: Both are a cross fade over three printed scales, because a texture's
    #: scale cannot be changed after it is printed. 0.75 and 0.78 are the
    #: defaults for the two sliders.
    wood_texture: float = 0.75
    wood_dabs: float = 0.78
    wood_tex_scales: tuple[float, ...] = (2.1, 1.0, 0.45)
    wood_tex_strengths: tuple[float, ...] = (0.30, 0.40, 0.48)
    dab_spacings: tuple[float, ...] = (1.7, 1.0, 0.6)
    dab_strengths: tuple[float, ...] = (0.34, 0.36, 0.38)


@dataclass(frozen=True)
class RouteStyle:
    """The route's own painted plate: whether it is drawn, with which nib, how wide.

    The plate is an alpha plate, tinted at compose time by the route's ink,
    so a theme can change the ink without repainting.
    """

    route_pen: bool = True
    route_pen_brush: str = "MAJ6-e"
    route_pen_width_px: float = 3.0


@dataclass(frozen=True)
class BasemapStyle:
    """What the basemap draws, and how much of it: relief, roads, rivers, landmarks, shapes."""

    #: `bands` (posterised vector relief), `raster` (the greyscale PNG),
    #: `contours`, `hachures`, or `off`. Bands carry the shape at a tenth of
    #: the raster's bytes and stay crisp at any size the page draws.
    hillshade_mode: str = "off"
    hillshade_levels: int = 5
    hillshade_opacity: float = 0.5
    #: Hachures: seed spacing, the gradient below which nothing is drawn, and
    #: the longest stroke. All three are stated for a 4 km box and scaled up.
    hachure_spacing_m: float = 75.0
    hachure_min_slope: float = 0.035
    hachure_max_length_m: float = 90.0
    #: `fill` or `waves`.
    sea_style: str = "fill"
    #: Contour interval in metres, used when the mode is `contours`. A 20 m
    #: interval draws a hatch, not a map.
    contour_interval: float = 50.0
    #: `all`, `key` (major plus interacted), or `major`.
    roads: str = "key"
    #: `all`, `key` (rivers plus interacted streams), or `rivers`.
    rivers: str = "key"
    #: Metres within which a minor road or a stream counts as touched.
    interaction_m: float = 60.0
    #: Metres of that contact needed before it counts, unless the track crosses.
    interaction_run_m: float = 100.0
    #: `heuristic`, `all` or `payload`.
    landmarks: str = "heuristic"
    landmark_max: int = 8
    landmark_radius_m: float = 300.0
    #: Names the payload picked: `pick_landmarks` replaces the landmark
    #: heuristic when given, and `pick_roads` keeps a minor road it names.
    pick_landmarks: tuple[str, ...] = ()
    pick_roads: tuple[str, ...] = ()
    pick_places: tuple[str, ...] = ()
    #: The generalisation stage, which runs before anything is drawn: the wood,
    #: the parkland and the sea are rasterised, closed, opened, decluttered and
    #: traced back as a few smooth shapes. Off draws the raw OSM outlines.
    generalise: bool = True
    #: Metres per cell of the working grid, stated for a 4 km box and scaled up.
    cell_m: float = 60.0
    #: Radius of the morphological close and open, in cells.
    morph_cells: int = 2
    #: Hectares below which a blob, or a hole in one, is dropped.
    min_area_ha: float = 4.0
    #: Chaikin passes on a traced outline, and on a road or a river.
    smooth_passes: int = 3
    #: Metres of loose-edge wobble on a wash. Zero draws the measured edge.
    blob_jitter_m: float = 22.0
    #: Cells pulled in for the second, darker pass of pigment inside a wash.
    inset_cells: int = 2
    #: Metres between tree glyphs inside a wood. Zero scatters none.
    tree_spacing_m: float = 450.0
    #: Build every relief variant rather than the one the mode asks for, so a
    #: page can switch between them without a rebuild.
    all_variants: bool = False


@dataclass(frozen=True)
class LetteringPolicy:
    """Which names a map letters, and how many: the landmark cap and the switches."""

    #: The landmark cap. The ground carries its own names and the landmarks
    #: compete with them; three leaves room for both. Spans have their own cap
    #: in `lettering.spans.SPAN_MAX`.
    label_max: int = 3
    #: Letter the map at all. Off, no hand is opened: the lettering stage
    #: places no labels or spans and draws no label plate, and the attribution
    #: line is not written either.
    labels: bool = True
    #: Letter the settlements, the watercourses and the roads the box holds, as
    #: the hierarchy asks: a settlement beside its dot with no leader, a river
    #: along its own water in spaced italic, a road number along its own tarmac.
    label_ground: bool = True
    #: How far a named road or watercourse is simplified before a label is set
    #: along it, in display pixels.
    label_geom_tol_px: float = 8.0
    #: Letter the user's marked places, each under its own name.
    home_glyph: bool = True


#: The route ink, for every sport: a burnt maroon
#: on the pinker side, blended from the original rose (#e01c64) toward maroon,
#: and lifted back toward it.
#:
#: The maroon read as one more dark mark on a sheet already carrying dark
#: washes: against cream it had the contrast (6.5:1) and against a wood or a
#: built-up wash it had almost none, and the route is the one line on the card
#: the reader is looking for. This is about 40% more luminous and carries more
#: chroma with it, which is what actually separates it from a green or a grey
#: wash, and it still holds 5:1 on the paper. It is not the rose: that was
#: too hot, and this sits between the two.
ROUTE_INK = "#c22050"
#: Every route effect key, each at its off value. No module reads it, so nothing
#: fills in a key a theme's effect table leaves out.
ROUTE_EFFECT_OFF: dict[str, Any] = {
    "glow_px": 0.0,
    "glow_opacity": 0.0,
    "casing_colour": "cream",
    "casing_px": 0.0,
    "adaptive_pct": 0.0,
    "shadow_px": 0.0,
    "shadow_blur_px": 0.0,
    "blend": "normal",
}
#: The three casings the lab offered. Anything else is taken as a colour.
CASING_COLOURS = {"cream": "#f2e9d4", "dark": "#241c14", "white": "#ffffff"}
#: The drop shadow's pigment, from the lab: a brown black, not a grey.
ROUTE_SHADOW = "#120d07"


@dataclass(frozen=True)
class RouteInk:
    """One sport's route treatment: its style, width, colour and effect keys."""

    style: str
    px: float
    colour: str
    effect: dict[str, Any]

    @property
    def casing(self) -> str:
        """The casing's colour: one of the three names, or a colour as given."""
        named = str(self.effect["casing_colour"])
        return CASING_COLOURS.get(named, named)


@dataclass(frozen=True)
class RouteInks:
    """One resolved route ink per sport; only `paint` and `compose` read it."""

    #: The ink a run is drawn in.
    run: RouteInk
    #: The ink a ride is drawn in.
    ride: RouteInk
    #: The ink a swim is drawn in.
    swim: RouteInk
    #: The ink any other sport is drawn in.
    other: RouteInk
