"""The registry of every image the README and `docs/` show, and the budgets they keep to.

Key types: `DocsImage`, one committed image and the script run that paints it; `IMAGES`,
the registry, in slice order; `KIND_BUDGET_BYTES`, the size one file may reach by its
kind; `SLICE_SHARE_BYTES`, what each slice's images may add up to; `TOTAL_BUDGET_BYTES`,
the whole of `docs/images/`.

The script contract. An image script lives in `examples/`, imports only public names
(plus the third-party packages `tests/architecture/test_examples.py` allows), and has
`main(out_dir: Path, **options) -> Path`, writing exactly one image per call and
returning its path. A script that paints several figures takes a keyword that selects
one (`figure=`), and the registry holds one entry per figure. The registry and the pin
read the returned path only; a script may write other files beside it (`lettering.py`
and `composition.py` write a plate too), which are ignored. A script that reads a
fixture takes the keywords `track` (the GPX `Path`, which the script reads itself),
`cache_dir`, `features` and `elevation`, and may take `theme: str | None`, a path
relative to the repo root loaded with `Style.from_toml`, `Style.default()` when absent.
`make_docs_images.py` and the pin test copy `tests/fixtures/<fixture>/` to a temporary
cache directory and pass `track=<copy> / "track.gpx"`, that `cache_dir`, and
`OverpassFeatures` and `OpenTopoData` with a budget of 0 at `http://127.0.0.1:9`, exactly
as `tests/examples/test_route_map_example.py` does; `theme` comes from the entry's
`options`. A non-golden test of a script passes a small `size=` option.

Sizes are decimal: a kilobyte is 1000 bytes. Encodings: lossless WebP for pen, nib and
lettering figures; lossy WebP for washes, swatch sheets, mixed figures and maps; JPEG for
the social preview only. Over its kind's budget, an entry goes lossy if it is a wash,
else to a smaller width.

Adding entries. A slice appends one block of entries under a comment naming the slice;
a landing conflict is resolved by keeping both blocks. The slice's share must be in
`SLICE_SHARE_BYTES`.

It does not paint, encode or read any image: `tests/golden/make_docs_images.py` paints
and encodes, `tests/golden/test_docs_images.py` pins, and
`tests/architecture/test_docs_images.py` checks the registry against the files and the
Markdown that shows them.
"""

from dataclasses import dataclass
from typing import Literal

#: Where the committed images live, relative to the repo root.
IMAGES_DIR = "docs/images"

Kind = Literal["thumbnail", "page", "hero", "preview"]
Encoding = Literal["webp-lossless", "webp-lossy", "jpeg"]
Option = tuple[str, str | int | float]


@dataclass(frozen=True)
class DocsImage:
    """One committed image: where it lives and which script run paints it.

    Attributes:
        image: The file's path under `docs/images/`.
        stem: The script in `examples/`, without `.py`.
        options: Keyword arguments for the script's `main`, as name and value pairs.
        fixture: The directory under `tests/fixtures/` the script reads, or `None`.
        width: The width the image is downsized to, never enlarged.
        kind: Which size budget the file keeps to.
        encoding: How the file is written.
        slice: The plan slice that registered it, a key of `SLICE_SHARE_BYTES`.
    """

    image: str
    stem: str
    options: tuple[Option, ...]
    fixture: str | None
    width: int
    kind: Kind
    encoding: Encoding
    slice: str


#: The most one file may weigh, by kind. The social preview stays under GitHub's 1 MB limit.
KIND_BUDGET_BYTES: dict[str, int] = {
    "thumbnail": 60_000,
    "page": 250_000,
    "hero": 400_000,
    "preview": 900_000,
}

#: The most one slice's images may weigh together.
SLICE_SHARE_BYTES: dict[str, int] = {
    "P7.4": 500_000,
    "P7.5": 500_000,
    "P7.6a": 400_000,
    "P7.6b": 400_000,
    "P7.6c": 400_000,
    "P7.7": 600_000,
    "P7.8": 300_000,
    "P7.9": 500_000,
    "P7.10": 500_000,
    "P7.13": 2_700_000,
    "P7.14": 200_000,
}

#: The most all of `docs/images/` may weigh.
TOTAL_BUDGET_BYTES = 7_000_000


def _gallery(
    name: str, stem: str, width: int, encoding: Encoding, fixture: str | None = None
) -> DocsImage:
    """Return one gallery thumbnail entry."""
    return DocsImage(
        f"gallery/{name}.webp", stem, (), fixture, width, "thumbnail", encoding, "P7.4"
    )


IMAGES: tuple[DocsImage, ...] = (
    # P7.4: the gallery, one thumbnail per tutorial rung.
    _gallery("paper", "paper", 360, "webp-lossy"),
    _gallery("wash", "wash", 360, "webp-lossy"),
    _gallery("brush-stroke", "brush_stroke", 360, "webp-lossy"),
    _gallery("pigments", "pigments", 480, "webp-lossy"),
    _gallery("nib-line", "nib_line", 320, "webp-lossless"),
    _gallery("lettering", "lettering", 360, "webp-lossless"),
    _gallery("composition", "composition", 480, "webp-lossy"),
    _gallery("route-map", "route_map", 720, "webp-lossy", "keswick"),
    # P7.6a: curves and symmetry.
    DocsImage(
        "curves/rose.webp",
        "curves",
        (("figure", "rose"),),
        None,
        640,
        "page",
        "webp-lossy",
        "P7.6a",
    ),
    DocsImage(
        "curves/lissajous.webp",
        "curves",
        (("figure", "lissajous"),),
        None,
        640,
        "page",
        "webp-lossy",
        "P7.6a",
    ),
    DocsImage(
        "curves/spirograph.webp",
        "curves",
        (("figure", "spirograph"),),
        None,
        640,
        "page",
        "webp-lossy",
        "P7.6a",
    ),
    DocsImage(
        "curves/kaleidoscope.webp", "kaleidoscope", (), None, 640, "page", "webp-lossy", "P7.6a"
    ),
)


def _rung(
    name: str, stem: str, width: int, encoding: Encoding, fixture: str | None = None
) -> DocsImage:
    """Return one tutorial page image entry, painted by a rung's script."""
    return DocsImage(f"tutorials/{name}.webp", stem, (), fixture, width, "page", encoding, "P7.5")


IMAGES += (
    # P7.5: the tutorials' page images, one per rung, each at its own width.
    _rung("paper", "paper", 360, "webp-lossy"),
    _rung("wash", "wash", 360, "webp-lossy"),
    _rung("brush-stroke", "brush_stroke", 360, "webp-lossy"),
    _rung("pigments", "pigments", 720, "webp-lossy"),
    _rung("nib-line", "nib_line", 360, "webp-lossless"),
    _rung("lettering", "lettering", 360, "webp-lossless"),
    _rung("composition", "composition", 480, "webp-lossy"),
    _rung("route-map", "route_map", 900, "webp-lossy", "keswick"),
    # P7.6b: painting with Python, the fern and the gasket.
    DocsImage(
        "painting-with-python/fern.webp", "fern", (), None, 600, "page", "webp-lossy", "P7.6b"
    ),
    DocsImage(
        "painting-with-python/gasket.webp", "gasket", (), None, 640, "page", "webp-lossy", "P7.6b"
    ),
)
