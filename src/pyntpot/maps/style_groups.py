"""The map's own style groups, the route ink and the fields no painter reads.

Key types: `CardStyle` (the card's size and the dark grid),
`RibbonStyle` (the trimmed extent of the painted ground and the card's
frame), `CoverStyle` (land cover and the wood), `RouteStyle` (the route's
own painted plate), `BasemapStyle` (what the basemap draws and how much of
it), `LetteringStyle` (which names a map letters) and `RouteInkStyle` (how the
route is drawn on the card). `CONSUMER_ONLY` names the painter fields that no
module reads and so belong to no group.

Base groups feed the base plates; `LetteringStyle` feeds only the lettering;
`RouteInkStyle` is read only when the route is placed and drawn (`paint` takes the
strand merge reach from its width), so changing the ink repaints no plate. The defaults
are the default look; the default theme is these defaults with nothing overridden.

It paints, letters and fetches nothing. The route ink knows nothing of what a
track records, and holds no casing, glow or shadow: the compose step draws
none. Two `BasemapStyle` fields, `hillshade_opacity` and `pick_places`, have
no reader and are kept for the upstream consumer. The basemap's clip margin is derived from the card per
render and is not a style field.

Invariants: every field belongs to exactly one style group across the
package.
"""

from dataclasses import dataclass, field

from pyntpot.maps.providers.overpass import MINOR_ROADS

#: The painter fields no module reads, kept by the upstream consumer and left
#: out of every group.
CONSUMER_ONLY: tuple[str, ...] = (
    "cover_order",
    "label_font",
    "label_pin_colour",
    "label_glow_colour",
)


@dataclass(frozen=True, kw_only=True)
class CardStyle:
    """The card's display size, its supersampling, and the dark grid's size.

    Attributes:
        display_px: Display width of the card in CSS pixels; the height follows its aspect.
            900 is the width the plates were set at, and it is what decides whether the
            lanes and the tracks are drawn: below it, a display pixel is more than eight
            metres of ground and a lane is not a mark.
        supersample: Painted at this multiple of the display size, so the grain survives a
            retina screen. 2 is what the plates were set at.
        dark_grid: Cells across and down of the dark grid the label placer scores against.
    """

    display_px: int = 900
    supersample: int = 2
    dark_grid: tuple[int, int] = (80, 60)


@dataclass(frozen=True, kw_only=True)
class RibbonStyle:
    """The ribbon: the trimmed extent of the painted ground, and the card around it.

    Attributes:
        ribbon_k: Radius in metres is `ribbon_k * sqrt(box) + ribbon_c`, then the slider;
            this is the factor on the square root of the box.
        ribbon_c: The metres added to that, so a small box keeps a generous ribbon.
        ribbon_mult: The slider, as a multiplier on that. 1.0 leaves the fitted radius
            unchanged.
        ribbon_min_m: The smallest fitted radius, in metres.
        ribbon_max_m: The largest fitted radius, in metres.
        card_grow_mult: The card is framed as though the widest ribbon were on, so the same
            box is composed whatever the slider is set to: the track's bounds grow by the
            fitted radius times this.
        card_pad_frac: Padding round the grown bounds, as a fraction of their longer side.
        card_pad_ribbon_frac: The least padding, as a fraction of the fitted radius.
        card_aspect_min: The narrowest the card may be, as width over height; a narrower
            card is widened.
        card_aspect_max: The widest the card may be, as width over height; a wider card is
            made taller.
        ribbon_fill: Fill what the outside cannot reach, so the inside of a loop is painted.
        ribbon_tear_frac: Torn edge, as a fraction of the render width.
        ribbon_tear_floor_px: The torn edge's floor, in pixels.
        rim_strength: The pooled edge just inside the tear.
        coast_hard_mask: The coast is a hard edge: nothing the ribbon carries crosses it.
        sea_to_edge: The sea is painted to the edge of the card and never trimmed.
    """

    ribbon_k: float = 7.15
    ribbon_c: float = 158.0
    ribbon_mult: float = 1.0
    ribbon_min_m: float = 420.0
    ribbon_max_m: float = 1250.0
    card_grow_mult: float = 1.55
    card_pad_frac: float = 0.09
    card_pad_ribbon_frac: float = 0.55
    card_aspect_min: float = 1.12
    card_aspect_max: float = 1.62
    ribbon_fill: bool = True
    ribbon_tear_frac: float = 0.004
    ribbon_tear_floor_px: float = 5.0
    rim_strength: float = 0.40
    coast_hard_mask: bool = True
    sea_to_edge: bool = True


@dataclass(frozen=True, kw_only=True)
class CoverStyle:
    """Land cover and the wood: the classes, their pigments, and the wood's texture and dabs.

    `land_cover` paints the cover classes, or the pale single wash when off;
    `relief` paints the relief from the elevation grid. `dither_seed` seeds the
    wood dabs.

    Attributes:
        dither_seed: Seeds, so the same box paints the same map every time.
        land_cover: Paint the cover classes; off, the pale single wash.
        relief: Paint the relief from the elevation grid.
        relief_strength: Multiplies the relief's density, and the ceiling it is held to.
            1.0 is the quiet relief.
        min_patch_px: Display pixels below which a painted cover patch takes its largest
            painted neighbour's class; a patch nothing painted touches is kept. Zero keeps
            every patch.
        cover_cfg: How dark a wash of each class goes, and how hard its edge pools.
        pigments: Multiply colours: what a full-strength wash of each pigment transmits.
        pale_base: The pale single wash drawn instead of the classes when cover is off: its
            density.
        pale_pool: How hard that pale wash's edge pools.
        wood_texture: The wood's texture slider; 0.75 is its default. It is a cross fade over
            three printed scales, because a texture's scale cannot be changed after it is
            printed.
        wood_dabs: The wood's dabs slider, a cross fade the same way; 0.78 is its default.
        wood_tex_scales: The three printed scales of the wood's texture.
        wood_tex_strengths: The strength of the texture at each of those scales.
        dab_spacings: The three dab spacings the dabs slider fades across.
        dab_strengths: The strength of the dabs at each of those spacings.
    """

    dither_seed: int = 23
    land_cover: bool = True
    relief: bool = True
    relief_strength: float = 1.0
    min_patch_px: float = 0.0
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
    pale_base: float = 0.50
    pale_pool: float = 0.16
    wood_texture: float = 0.75
    wood_dabs: float = 0.78
    wood_tex_scales: tuple[float, ...] = (2.1, 1.0, 0.45)
    wood_tex_strengths: tuple[float, ...] = (0.30, 0.40, 0.48)
    dab_spacings: tuple[float, ...] = (1.7, 1.0, 0.6)
    dab_strengths: tuple[float, ...] = (0.34, 0.36, 0.38)


@dataclass(frozen=True, kw_only=True)
class RouteStyle:
    """The route's own painted plate: whether it is drawn, with which nib, how wide.

    The plate is an alpha plate, tinted at compose time by the route's ink,
    so a theme can change the ink without repainting.

    Attributes:
        route_pen: Paint the route's own plate.
        route_pen_brush: The brush the plate is drawn with.
        route_pen_width_px: The plate's line width, in display pixels.
    """

    route_pen: bool = True
    route_pen_brush: str = "MAJ6-e"
    route_pen_width_px: float = 3.0


@dataclass(frozen=True, kw_only=True)
class BasemapStyle:
    """What the basemap draws, and how much of it: relief, roads, rivers, landmarks, shapes.

    Attributes:
        hillshade_mode: `bands` (posterised vector relief), `raster` (the greyscale PNG),
            `contours`, `hachures`, or `off`. Bands carry the shape at a tenth of the
            raster's bytes and stay crisp at any size the page draws.
        hillshade_levels: How many bands the posterised relief is cut into.
        hillshade_opacity: The relief's opacity; no module reads it, and it is kept for the
            upstream consumer.
        hachure_spacing_m: Hachures: seed spacing. Stated for a 4 km box and scaled up.
        hachure_min_slope: Hachures: the gradient below which nothing is drawn.
        hachure_max_length_m: Hachures: the longest stroke. Stated for a 4 km box and
            scaled up.
        sea_style: `fill` or `waves`.
        contour_interval: Contour interval in metres, used when the mode is `contours`. A
            20 m interval draws a hatch, not a map.
        roads: `all`, `key` (major plus interacted), or `major`.
        minor_road_classes: The minor highway classes `roads = "all"` keeps; the fetch query
            is unchanged.
        rivers: `all`, `key` (rivers plus interacted streams), or `rivers`.
        interaction_m: Metres within which a minor road or a stream counts as touched.
        interaction_run_m: Metres of that contact needed before it counts, unless the track
            crosses.
        landmarks: `heuristic`, `all` or `payload`.
        landmark_max: The most landmarks the heuristic keeps, stated for a 4 km box.
        landmark_radius_m: Metres from the track within which the heuristic looks for
            landmarks, stated for a 4 km box.
        pick_landmarks: Names the payload picked: `pick_landmarks` replaces the landmark
            heuristic when given.
        pick_roads: Names the payload picked: `pick_roads` keeps a minor road it names.
        pick_places: Names the payload picked; no module reads it, and it is kept for the
            upstream consumer.
        name_tags: The OSM tags that name a feature, in order of preference: the map letters
            the first one an element carries, else nothing. `("name:cy", "name")` letters
            Welsh names where OSM has them. The candidate export keeps reading `name`.
        generalise: The generalisation stage, which runs before anything is drawn: the
            wood, the parkland and the sea are rasterised, closed, opened, decluttered and
            traced back as a few smooth shapes. Off draws the raw OSM outlines.
        cell_m: Metres per cell of the working grid, stated for a 4 km box and scaled up.
        morph_cells: Radius of the morphological close and open, in cells.
        min_area_ha: Hectares below which a blob, or a hole in one, is dropped.
        smooth_passes: Chaikin passes on a traced outline, and on a road or a river.
        blob_jitter_m: Metres of loose-edge wobble on a wash. Zero draws the measured edge.
        inset_cells: Cells pulled in for the second, darker pass of pigment inside a wash.
        tree_spacing_m: Metres between tree glyphs inside a wood. Zero scatters none.
        all_variants: Build every relief variant rather than the one the mode asks for, so
            a page can switch between them without a rebuild.
    """

    hillshade_mode: str = "off"
    hillshade_levels: int = 5
    hillshade_opacity: float = 0.5
    hachure_spacing_m: float = 75.0
    hachure_min_slope: float = 0.035
    hachure_max_length_m: float = 90.0
    sea_style: str = "fill"
    contour_interval: float = 50.0
    roads: str = "key"
    minor_road_classes: tuple[str, ...] = MINOR_ROADS
    rivers: str = "key"
    interaction_m: float = 60.0
    interaction_run_m: float = 100.0
    landmarks: str = "all"
    landmark_max: int = 40
    landmark_radius_m: float = 300.0
    pick_landmarks: tuple[str, ...] = ()
    pick_roads: tuple[str, ...] = ()
    pick_places: tuple[str, ...] = ()
    name_tags: tuple[str, ...] = ("name",)
    generalise: bool = False
    cell_m: float = 60.0
    morph_cells: int = 2
    min_area_ha: float = 4.0
    smooth_passes: int = 3
    blob_jitter_m: float = 22.0
    inset_cells: int = 2
    tree_spacing_m: float = 450.0
    all_variants: bool = False


@dataclass(frozen=True, kw_only=True)
class LetteringStyle:
    """Which names a map letters, and how many: the landmark cap and the switches.

    Attributes:
        label_max: The landmark cap. The ground carries its own names and the landmarks
            compete with them; three leaves room for both. Spans have their own cap in
            `lettering.spans.SPAN_MAX`.
        labels: Letter the map at all. Off, the lettering stage opens no hand: it places no
            labels or spans and draws no nib plate. The attribution follows `compose`'s
            `attribution` flag alone.
        label_ground: Letter the settlements, the watercourses and the roads the box holds,
            as the hierarchy asks: a settlement beside its dot with no leader, a river along
            its own water in spaced italic, a road number along its own tarmac.
        label_geom_tol_px: How far a named road or watercourse is simplified before a label
            is set along it, in display pixels.
        home_glyph: Letter the user's marked places, each under its own name.
    """

    label_max: int = 3
    labels: bool = True
    label_ground: bool = True
    label_geom_tol_px: float = 8.0
    home_glyph: bool = True


@dataclass(frozen=True, kw_only=True)
class RouteInkStyle:
    """How the route is drawn on the map: its style, width, colour, blend and opacity.

    Only `paint` (the strand merge reach, from `px`) and the compose step read it.

    Attributes:
        style: `"pen"` tints the painted pen plate when one was painted; any other value
            (every theme says `"solid"`) draws the line.
        px: Width in display pixels; it also sets how near two passes of a retraced route
            have to come to be drawn as one stroke.
        colour: Colour as `#rrggbb`.
        blend: `"normal"` lays the ink over the card; `"multiply"` multiplies it in, so a
            dark wash stays dark under it. The compose step rejects any other value.
        opacity: How much of the ink is laid, from 0 to 1.
    """

    style: str = "solid"
    px: float = 5.4
    colour: str = "#c22050"
    blend: str = "normal"
    opacity: float = 1.0
