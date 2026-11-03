"""The gallery shows every registered image but the site chrome, under its pages in nav order.

Images come from `support.docs_images.IMAGES` and the order from `mkdocs.yml`'s nav, so a
new image or page is covered with no test edit. An image under `site/` is the site's own
chrome, not a picture of the docs, and is not shown.
"""

import re

from support.docs_images import IMAGES
from support.site_pages import DOCS, MKDOCS, nav, resolve

_GALLERY = DOCS / "gallery.md"
_IMAGE = re.compile(r"!\[[^\]]*\]\(\s*<?(?P<href>[^)\s>]+)>?\s*\)")
_HEADING_LINK = re.compile(r"^### \[[^\]]*\]\(\s*<?(?P<href>[^)\s>]+)>?\s*\)", re.MULTILINE)


def _shown() -> set[str]:
    """Return the paths under `docs/images/` of every image the gallery shows."""
    images = DOCS / "images"
    shown: set[str] = set()
    for found in _IMAGE.finditer(_GALLERY.read_text()):
        target = resolve(_GALLERY, found["href"])
        if target is not None and target.is_relative_to(images):
            shown.add(target.relative_to(images).as_posix())
    return shown


def _heading_pages() -> list[str]:
    """Return the site pages the gallery's `###` headings link to, as paths under `docs/`, in page order."""
    pages: list[str] = []
    for found in _HEADING_LINK.finditer(_GALLERY.read_text()):
        target = resolve(_GALLERY, found["href"])
        if target is not None and target.is_relative_to(DOCS):
            pages.append(target.relative_to(DOCS).as_posix())
    return pages


def test_the_gallery_shows_every_registered_image_but_the_site_chrome() -> None:
    """Every registered image outside `site/` appears in the gallery."""
    missing = sorted(
        entry.image
        for entry in IMAGES
        if not entry.image.startswith("site/") and entry.image not in _shown()
    )
    assert not missing, f"docs/gallery.md does not show: {missing}"


def test_the_gallery_lists_its_pages_in_nav_order() -> None:
    """The pages the gallery's headings link to run in the nav's order."""
    order = [entry.path for entry in nav(MKDOCS.read_text())]
    pages = _heading_pages()
    assert pages, "the gallery's headings link no site page"
    unknown = [page for page in pages if page not in order]
    assert not unknown, f"gallery headings link pages outside the nav: {unknown}"
    positions = [order.index(page) for page in pages]
    out_of_order = [
        f"{pages[index]} after {pages[index - 1]}"
        for index in range(1, len(pages))
        if positions[index] <= positions[index - 1]
    ]
    assert not out_of_order, f"gallery headings out of nav order: {out_of_order}"
