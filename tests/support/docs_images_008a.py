"""The docs images 008a adds, the theme preview cards, and the budget share of its slice.

Key types: `IMAGES_008A`, the entries in theme order, which `support.docs_images.IMAGES`
appends; `SHARES_008A`, the slice's share of the image budget, which
`support.docs_images.SLICE_SHARE_BYTES` includes. Each entry paints the preview card
(`examples/theme_preview.py`) from the preview fixture in one packaged theme.

It holds no image path rule of its own: `support.docs_image` describes an entry, and
`support.docs_images` holds the older entries and the kind and total budgets.
"""

from support.docs_image import DocsImage

#: The most the preview slice's images may weigh together.
SHARES_008A: dict[str, int] = {
    "008a-preview": 200_000,
}

#: The packaged themes, each painted once.
THEMES_008A: tuple[str, ...] = ("default", "pen-and-ink", "sepia", "bold", "winter")

IMAGES_008A: tuple[DocsImage, ...] = tuple(
    DocsImage(
        f"preview/{name}.webp",
        "theme_preview",
        (("theme", name),),
        "preview",
        600,
        "page",
        "webp-lossy",
        "008a-preview",
    )
    for name in THEMES_008A
)
