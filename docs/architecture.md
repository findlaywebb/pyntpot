# Architecture

pyntpot is a single distribution, `pyntpot`, with one package under `src/`. It paints
hand-drawn watercolour and pen-and-ink raster images, with route maps as its first
application.

## Layers

The target layering is `maps -> letters -> ink`, a P4 outcome. Until the port is split,
all code lives in `pyntpot._port`.

- `pyntpot.ink` is the painting engine: the sheet of paper and its noise fields, brushes,
  stamps, washes, pigment compositing and raster I/O. It imports nothing outside itself.
- `pyntpot.letters` is hand lettering: the vendored font, tracing glyphs to strokes by
  centreline or outline, and the hand that writes them. It imports `ink` only.
- `pyntpot.maps` is the route-map application: data providers, the cache, projection,
  layers, plates, label placement, composition, style and the CLI. It imports `letters`
  and `ink`.
- `pyntpot._port` is the interim private subpackage that holds the ported code with no
  layer contract. The split empties it.

The boundary is enforced by import-linter (`[tool.importlinter]` in `pyproject.toml`) and
the AST fitness tests in `tests/architecture/`. See `BOUNDARIES.md`.

## Exemptions

`tests/architecture/exemptions/` lists the code the gates stand down for while it is in
`_port`: files over the line budget and tests switched off by node id. Free-text notes live in `NOTES.md` there.
