# Architecture

pyntpot is a single distribution, `pyntpot`, with one package under `src/`. It paints
hand-drawn watercolour and pen-and-ink raster images, with route maps as its first
application.

## Layers

The layering is `maps -> letters -> ink`: each layer imports only the layers to its right.

- `pyntpot.ink` is the painting engine: the sheet of paper and its noise fields, brushes,
  stamps, washes, pigment compositing and raster I/O. It imports nothing outside itself.
- `pyntpot.letters` is hand lettering: the vendored font, tracing glyphs to strokes by
  centreline or outline, and the hand that writes them. It imports `ink` only.
- `pyntpot.maps` is the route-map application: data providers, the cache, projection,
  layers, plates, label placement, composition, style and the CLI. It imports `letters`
  and `ink`.

The boundary is enforced by import-linter (`[tool.importlinter]` in `pyproject.toml`) and
the AST fitness tests in `tests/architecture/`. See `BOUNDARIES.md`.

## Exemptions

`tests/architecture/exemptions/` is the one sanctioned relaxation of the gates: files over
the line budget and tests switched off by node id. It is empty; the files hold a header
comment only.
