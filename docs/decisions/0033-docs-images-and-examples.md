# 0033 — Every docs image is painted by a registered script and pinned

Status: accepted

Amends 0006 (the golden set grows) and 0026 (the examples' imports).

## Context

The README and `docs/` carry pictures, and the rule from the P7 research is that the pictures
carry the style. A picture painted once by hand and committed would drift from the code that
paints it. The goldens of ADR 0006 already pin the Lynmouth plates; the docs images need the
same pin, a registry that says which script paints which file, and budgets so that the
repository does not fill with pictures.

## Decision

- **The registry.** `tests/support/docs_images.py` holds the frozen dataclass `DocsImage`
  (path under `docs/images/`, script stem, options, fixture, width, kind, encoding, slice)
  and the tuple `IMAGES`. Every file under `docs/images/` is registered and every entry has
  its file; every image a Markdown file in the README or `docs/` shows is registered
  (`tests/architecture/test_docs_images.py`).
- **The script contract.** An image script lives in `examples/`, imports only public names,
  and has `main(out_dir: Path, **options) -> Path`, writing exactly one image per call and
  returning its path. A script that paints several figures takes `figure=`, and the registry
  holds one entry per figure. A script that reads a fixture takes `track`, `cache_dir`,
  `features` and `elevation`, and may take `theme`, a path relative to the repo root loaded
  with `Style.from_toml`. The pin and `make_docs_images.py` copy the fixture to a temporary
  cache and pass providers with a budget of 0 at `http://127.0.0.1:9`, so no request is made.
- **The pin.** `tests/golden/test_docs_images.py` (marker `golden`) decodes each committed
  image and a fresh paint encoded the same way, and requires them equal locally and within
  `test_parity.py`'s bound under `--golden-tolerance`. `tests/golden/make_docs_images.py`
  repaints entries and compares directories, as `make_golden.py` does.
- **Encodings.** Lossless WebP (method 5) for pen, nib and lettering figures; lossy WebP
  (quality 90, method 5) for washes, swatch sheets, mixed figures and maps; JPEG (quality 88)
  for the social preview only. Images are downsized to the entry's width and never enlarged.
  Over its kind's budget, a wash goes lossy, any other entry to a smaller width; still over,
  the slice stops.
- **Budgets** (decimal kilobytes): thumbnail 60 KB, page 250 KB, hero 400 KB, preview 900 KB
  (GitHub's limit is 1 MB). Slice shares: P7.4 0.5 MB, P7.5 0.5, P7.6a 0.4, P7.6b 0.4,
  P7.6c 0.4, P7.7 0.6, P7.8 0.3, P7.9 0.5, P7.10 0.5, P7.13 2.7, P7.14 0.2; `docs/images/`
  in all 7 MB. The test pins them.
- **README links.** None is relative. A link or image into this repo is an absolute URL on
  `raw.githubusercontent.com/findlaywebb/pyntpot/` or `github.com/findlaywebb/pyntpot/` at
  `main` or a `v*` tag, so the page reads the same on PyPI. Badges and other sites are free.
- **The examples' imports (amends 0026).** Beyond the standard library, numpy and Pillow,
  an example may import the packages in the `_THIRD_PARTY` literal of
  `tests/architecture/test_examples.py`, which this ADR mirrors: `numpy`, `PIL` and
  `pyntpot`. No package was added.
- **The SVG reader.** The spike added `svgelements` to the `dev` group. `uv run python -W
  error -c "import svgelements"` was clean, but `uv run ty check` on a small use reported
  `unresolved-import` on `SVG` and `Path` (the package ships no type information and builds
  its namespace with star imports), and exited 1. The package was removed. A drawing that
  needs reading is parsed with `xml.etree` and the path subset M, L, C and Z.

## Consequences

- A docs image cannot change unless the script that paints it changes, and the change shows
  in the pin.
- Later slices append blocks of entries under a comment naming the slice.
- The golden job grows by the pins; its time is recorded in the run log.
- The examples may not import a vector reader; the SVG page says pyntpot does not read SVG
  itself.
