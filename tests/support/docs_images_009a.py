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


IMAGES_009A: tuple[DocsImage, ...] = (
    # 009a-galleries: every brush id, every pigment, how pairs glaze and the bundled palettes.
    _gallery("brush-gallery-riv-str-lan", "brush_gallery", "riv-str-lan"),
    _gallery("brush-gallery-maj", "brush_gallery", "maj"),
    _gallery("brush-gallery-trk", "brush_gallery", "trk"),
    _gallery("pigment-gallery-roles", "pigment_gallery", "roles"),
    _gallery("pigment-gallery-painters", "pigment_gallery", "painters"),
    _gallery("pigment-gallery-glazes", "pigment_gallery", "glazes"),
    _gallery("palettes", "pigment_gallery", "palettes"),
)
