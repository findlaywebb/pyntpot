# 0007 — Public API

Status: accepted

## Context

Until the façade landed, the only way to paint a map was to import the interim `_port`
modules. The façade under `pyntpot.maps` now carries the fetch, paint, letter and compose
steps over typed values, and the upstream SVG page reads several attributes of those
values. What is public has to be written down, or everything importable becomes public.

## Decision

`pyntpot.__all__` holds exactly these names and nothing else is public:

- Map types: `Track`, `Basemap`, `Style`, `Plates`, `Lettering`, `Annotations`.
- Map functions: `fetch`, `paint`, `letter`, `compose`.
- Engine names: `Sheet`, `Brush`, `Canvas` (the painter's `Plate`, exported under its
  glossary name), `stamp`, `wash`, `composite`, `Hand`.
- `__version__`, the installed distribution's version from `importlib.metadata`, assigned
  after the imports.

The map names are defined in `pyntpot.maps`, which re-exports them; the top-level package
imports them from there. The engine names are re-exported from `_port` until the split
moves the engine into `ink` and `letters`, so their `__module__` is still private. The
top-level package is not a `maps` adapter and `ink` and `letters` do not re-export `_port`
names.

### Boundary

Providers, the fetch cache, the attribution drawing, the card and the command line are
reached through `pyntpot.maps.*` and are not top-level names.

### Attributes the SVG page reads, as built

- `Basemap`: `projection`, `layers`, `track`, `track_time`.
- `Plates`: `manifest`, `paths`, `card`, `route_px` (the raw route in display pixels) and
  `strands` (one polyline: the route separated where it runs twice, the line `compose`
  draws).
- `Lettering`: `labels`, `spans`, `plate_path`.

### Behaviour fixed with the API

- `fetch` takes the style.
- `paint` uses the basemap's card as given.
- Route ink is fixed to the resolved default style, with no sport selection.

## Consequences

Anything not listed is free to move or be renamed. A new public name, or a change to one
above, needs a new ADR.
