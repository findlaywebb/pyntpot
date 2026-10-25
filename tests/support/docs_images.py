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

Pins across platforms. Each entry also has a lossless reference master, a PNG at
`tests/golden/docs/<image path with .png>`, `MASTER_WIDTH` pixels wide at most (the
entry's width if narrower). Lossy re-encoding amplifies sub-LSB float noise, so on CI the
master, not the lossy file, is compared (ADR 0033).

It does not paint, encode or read any image: `tests/golden/make_docs_images.py` paints
and encodes, `tests/golden/test_docs_images.py` pins, and
`tests/architecture/test_docs_images.py` checks the registry against the files and the
Markdown that shows them.
"""

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Literal

#: Where the committed images live, relative to the repo root.
IMAGES_DIR = "docs/images"

#: Where the lossless reference masters live, relative to the repo root.
MASTERS_DIR = "tests/golden/docs"

#: The widest a reference master is; a narrower entry keeps its own width.
MASTER_WIDTH = 240

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
        quality: The lossy encoders' quality, or `None` for the encoding's own default.
    """

    image: str
    stem: str
    options: tuple[Option, ...]
    fixture: str | None
    width: int
    kind: Kind
    encoding: Encoding
    slice: str
    quality: int | None = None


def master_path(image: str) -> str:
    """Return a docs image's reference master path under `MASTERS_DIR`: its path with `.png`."""
    return str(PurePosixPath(image).with_suffix(".png"))


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
    "P7.V12b": 1_000_000,
    "P7.13": 2_700_000,
    "P7.14": 200_000,
    "P7.V10": 300_000,
    "P7.V12d": 150_000,
    "P7.V12c": 600_000,
    "P7.V12a": 300_000,
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


def _stages(
    stem: str, prefix: str, figures: tuple[str, ...], width: int, encoding: Encoding, slice_: str
) -> tuple[DocsImage, ...]:
    """Return one page entry per figure of a script that paints its figures a stage at a time, `width` pixels wide."""
    return tuple(
        DocsImage(
            f"explanation/{prefix}-{figure}.webp",
            stem,
            (("figure", figure), ("size", width)),
            None,
            width,
            "page",
            encoding,
            slice_,
        )
        for figure in figures
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
    _gallery("route-map", "route_map", 720, "webp-lossy", "ambleside"),
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
    _rung("route-map", "route_map", 900, "webp-lossy", "ambleside"),
    # P7.6b: painting with Python, the fern.
    DocsImage(
        "painting-with-python/fern.webp", "fern", (), None, 600, "page", "webp-lossy", "P7.6b"
    ),
    # P7.6c: Painting with Python, pictures.
    DocsImage(
        "painting-with-python/derwentwater.webp",
        "derwentwater",
        (),
        None,
        720,
        "page",
        "webp-lossy",
        "P7.6c",
    ),
    DocsImage(
        "painting-with-python/svg-drawing.webp",
        "svg_drawing",
        (),
        None,
        720,
        "page",
        "webp-lossy",
        "P7.6c",
    ),
    # P7.9: the reference's two sheets.
    DocsImage(
        "reference/pigment-swatches.webp",
        "pigment_swatches",
        (),
        None,
        960,
        "page",
        "webp-lossy",
        "P7.9",
    ),
    DocsImage(
        "reference/brush-sheet.webp",
        "brush_sheet",
        (("figure", "grid"),),
        None,
        960,
        "page",
        "webp-lossy",
        "P7.9",
    ),
    # P7.8: the how-to guides' result images.
    DocsImage(
        "how-to/route-ink.webp",
        "how_to_route_ink",
        (),
        "ambleside",
        720,
        "page",
        "webp-lossy",
        "P7.8",
    ),
    DocsImage(
        "how-to/own-shapes.webp",
        "how_to_own_shapes",
        (),
        None,
        480,
        "page",
        "webp-lossy",
        "P7.8",
    ),
    # P7.7: the Ambleside card in each example theme.
    *(
        DocsImage(
            f"map-styles/{name}.webp",
            "map_styles",
            (("figure", name),),
            "ambleside",
            720,
            "page",
            "webp-lossy",
            "P7.7",
        )
        for name in ("pen-and-ink", "sepia", "bold", "winter")
    ),
    # P7.10: the explanation essays' figures, a wash and a name each built a stage at a time.
    *_stages(
        "wash_stages",
        "wash",
        ("mask", "body", "rim", "grain", "overlap"),
        480,
        "webp-lossy",
        "P7.10",
    ),
    DocsImage(
        "explanation/wash-glaze.webp",
        "wash_stages",
        (("figure", "glaze"), ("size", 800)),
        None,
        800,
        "page",
        "webp-lossy",
        "P7.10",
    ),
    *_stages(
        "nib_stages",
        "nib",
        ("centreline", "ground", "backing", "set-down", "runs-dry"),
        360,
        "webp-lossless",
        "P7.10",
    ),
)


#: The five focus places the README's gallery shows: fixture, theme, then the fetch margin the
#: fixture was recorded with in metres (`None` for the library's default).
_PLACES: tuple[tuple[str, str | None, float | None], ...] = (
    ("skye", "examples/themes/skye.toml", 18000.0),
    ("yr-wyddfa", "examples/themes/yr-wyddfa.toml", 3000.0),
    ("oxford", "examples/themes/oxford.toml", None),
    ("y-fenni", "examples/themes/y-fenni.toml", None),
)


def _place_card(fixture: str, theme: str | None, margin: float | None, slice_: str) -> DocsImage:
    """Return one place card entry: the card at 720 pixels, in its theme, with its curated callouts."""
    return DocsImage(
        f"places/{fixture}.webp",
        "place_card",
        (
            ("size", 720),
            ("place", fixture),
            *((("theme", theme),) if theme else ()),
            *((("margin_m", margin), ("landcover_margin_m", margin)) if margin else ()),
        ),
        fixture,
        720,
        "page",
        "webp-lossy",
        slice_,
    )


IMAGES += (
    # P7.13: the README's wordmark and hero, the place cards, and the social preview.
    DocsImage("word.webp", "word", (), None, 480, "page", "webp-lossless", "P7.13"),
    DocsImage(
        "hero.webp",
        "place_card",
        (("size", 1200), ("place", "ambleside"), ("theme", "examples/themes/ambleside.toml")),
        "ambleside",
        1200,
        "hero",
        "webp-lossy",
        "P7.13",
    ),
    *(_place_card(fixture, theme, margin, "P7.13") for fixture, theme, margin in _PLACES),
    DocsImage(
        "social-preview.jpg",
        "social_preview",
        (("place", "ambleside"), ("theme", "examples/themes/ambleside.toml")),
        "ambleside",
        1280,
        "preview",
        "jpeg",
        "P7.13",
    ),
)

IMAGES += (
    # P7.V10: the Ambleside hero card, in its showcase theme.
    _place_card("ambleside", "examples/themes/ambleside.toml", None, "P7.V10"),
    # P7.V12d: the SVG drawing a step at a time (the finished painting is P7.6c's entry above).
    *(
        DocsImage(
            f"painting-with-python/svg-{figure}.webp",
            "svg_drawing",
            (("figure", figure),),
            None,
            720,
            "page",
            encoding,
            "P7.V12d",
        )
        for figure, encoding in (
            ("flat", "webp-lossless"),
            ("washes", "webp-lossy"),
            ("ink", "webp-lossy"),
        )
    ),
)

IMAGES += (
    # P7.V12c: the tree, the tree family and the fern family.
    DocsImage(
        "painting-with-python/tree.webp",
        "trees",
        (("figure", "tree"),),
        None,
        600,
        "page",
        "webp-lossy",
        "P7.V12c",
    ),
    DocsImage(
        "painting-with-python/tree-family.webp",
        "trees",
        (("figure", "family"),),
        None,
        720,
        "page",
        "webp-lossy",
        "P7.V12c",
    ),
    DocsImage(
        "painting-with-python/fern-family.webp",
        "fern_family",
        (),
        None,
        900,
        "page",
        "webp-lossy",
        "P7.V12c",
    ),
)

IMAGES += (
    # P7.V12b: the watercolour tutorial's variation grids, one per rung, and the hand and nib page's two grids.
    *(
        DocsImage(
            f"tutorials/grid-{figure}.webp",
            "tutorial_grids",
            (("figure", figure),),
            None,
            720,
            "page",
            encoding,
            "P7.V12b",
        )
        for figure, encoding in (
            ("paper", "webp-lossy"),
            ("wash", "webp-lossy"),
            ("brush", "webp-lossy"),
            ("pigments", "webp-lossy"),
            ("nib", "webp-lossless"),
            ("lettering", "webp-lossless"),
            ("composition", "webp-lossy"),
        )
    ),
    *(
        DocsImage(
            f"explanation/nib-{figure}.webp",
            "nib_stages",
            (("figure", figure), ("size", 840)),
            None,
            840,
            "page",
            "webp-lossless",
            "P7.V12b",
        )
        for figure in ("angles", "hands")
    ),
)

IMAGES += (
    # P7.V12a: the route-ink grid, three treatments by four colours on the Ambleside card, and the command-line how-to's map.
    DocsImage(
        "how-to/route-ink-grid.webp",
        "how_to_route_ink",
        (("figure", "grid"), ("theme", "examples/themes/ambleside.toml")),
        "ambleside",
        720,
        "page",
        "webp-lossy",
        "P7.V12a",
    ),
    DocsImage(
        "how-to/command-line.webp",
        "route_map",
        (),
        "lynmouth",
        720,
        "page",
        "webp-lossy",
        "P7.V12a",
    ),
)
