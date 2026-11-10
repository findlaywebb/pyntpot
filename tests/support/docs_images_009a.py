"""The docs images 009a adds, one block for each of its slices, and the budget share of each.

Key types: `IMAGES_009A`, the entries in slice order, which `support.docs_images.IMAGES`
appends; `SHARES_009A`, each slice's share of the image budget, which
`support.docs_images.SLICE_SHARE_BYTES` includes. Each slice appends its own block under a
comment naming it and its share, so a landing conflict is resolved by keeping both.

It holds no image path rule of its own: `support.docs_image` describes an entry, and
`support.docs_images` holds the older entries and the kind and total budgets.
"""

from support.docs_image import DocsImage

#: The most each 009a slice's images may weigh together.
SHARES_009A: dict[str, int] = {
    "009a-galleries": 500_000,
    "009a-line-effects": 600_000,
}


def _gallery(image: str, stem: str, figure: str, width: int = 720) -> DocsImage:
    """Return one lossy reference swatch sheet of the galleries slice."""
    return DocsImage(
        f"reference/{image}.webp",
        stem,
        (("figure", figure),),
        None,
        width,
        "page",
        "webp-lossy",
        "009a-galleries",
    )


def _sweep(image: str, figure: str, page_dir: str = "how-to", width: int = 720) -> DocsImage:
    """Return one line effect sweep: lossy, except the pen casing's, which is lossless."""
    pen = figure == "pen-casing"
    return DocsImage(
        f"{page_dir}/{image}.webp",
        "line_effect_grids",
        (("figure", figure),),
        None,
        width,
        "page",
        "webp-lossless" if pen else "webp-lossy",
        "009a-line-effects",
    )


def _how_to(image: str, figure: str) -> DocsImage:
    """Return one how-to figure of the line effects, painted on the Ambleside fixture."""
    return DocsImage(
        f"how-to/{image}.webp",
        "how_to_line_effects",
        (("figure", figure),),
        "ambleside",
        720,
        "page",
        "webp-lossy",
        "009a-line-effects",
    )


IMAGES_009A: tuple[DocsImage, ...] = (
    # 009a-galleries: every brush id, every pigment, how pairs glaze and the bundled palettes.
    _gallery("brush-gallery-riv-str-lan", "brush_gallery", "riv-str-lan"),
    _gallery("brush-gallery-maj", "brush_gallery", "maj"),
    _gallery("brush-gallery-trk", "brush_gallery", "trk"),
    _gallery("pigment-gallery-roles", "pigment_gallery", "roles"),
    _gallery("pigment-gallery-painters", "pigment_gallery", "painters"),
    _gallery("pigment-gallery-glazes", "pigment_gallery", "glazes"),
    _gallery("palettes", "pigment_gallery", "palettes"),
    # 009a-line-effects: the sweeps (the how-to's and the tutorial's), then the slice's other figures.
    _sweep("casing-sweep", "casing"),
    _sweep("glow-sweep", "glow"),
    _sweep("shadow-sweep", "shadow"),
    _sweep("pen-casing-sweep", "pen-casing", "painting-with-python", 600),
    _how_to("line-effects", "card"),
    _how_to("line-effects-presets", "presets"),
)
