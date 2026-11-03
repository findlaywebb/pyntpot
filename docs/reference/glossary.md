<!-- Generated from GLOSSARY.md by tests/support/glossary.py. Edit GLOSSARY.md, then run: PYTHONPATH=tests uv run python -m support.glossary -->
# Glossary

Every term these docs use, what it means and where it lives in the code. The docs use one name for each of these and no other. A term underlined on a page shows its meaning when you point at it. The source is [GLOSSARY.md](https://github.com/findlaywebb/pyntpot/blob/main/GLOSSARY.md) in the repository.

## Painting

| Term | Meaning | In the code |
| --- | --- | --- |
| <span id="term-sheet"></span>sheet | The paper's noise fields, seeded; never the map. | `pyntpot.ink.Sheet` |
| <span id="term-tooth"></span>tooth | The paper's height, high where the paper stands up: a wash lightens where the tooth is high, and granulation settles where it is low. The sheet's `paper` field. | `pyntpot.ink.Sheet` |
| <span id="term-granulation"></span>granulation | Pigment settling into the paper's low places as a wash dries, so the wash reads grainy; the sheet's `gran_px` sets the size of its grain. | `pyntpot.ink.Sheet` |
| <span id="term-foxing"></span>foxing | The small rust specks of an old sheet of paper, laid by the paper plate; `PaperStyle.paper_foxing` sets how strong. | `pyntpot.ink.paper_plate`, `pyntpot.ink.PaperStyle` |
| <span id="term-canvas"></span>canvas | A world-unit box and the pixel grid it paints to. | `pyntpot.ink.Canvas` |
| <span id="term-wash"></span>wash | A pigment field laid on the paper. | `pyntpot.ink.wash` |
| <span id="term-coverage-mask"></span>coverage mask | The array in 0 to 1 that says where a wash goes, 1 inside the shape and 0 outside: the first argument of `wash`. | `pyntpot.ink.wash` |
| <span id="term-body"></span>body | The flat, even part of a wash inside its edge; `wash`'s `base` is the body's density. | `pyntpot.ink.wash` |
| <span id="term-pool"></span>pool | The extra density a wash carries in a band just inside its edge, where the pigment gathers as the water dries: a real wash's edge darkening. `wash`'s `pool`. | `pyntpot.ink.wash` |
| <span id="term-backrun"></span>backrun | A second front of water pushing deposited pigment ahead of it, leaving a pale centre and a dark, crenellated ridge where it dries. | `pyntpot.ink.bloom.bloom` |
| <span id="term-glaze"></span>glaze | Laying one pigment layer over another so the light passes through both and the colours mix as transparent films, by the Kubelka-Munk model, rather than multiplying; `PaperStyle.km_glazing` turns it on. | `pyntpot.ink.composite`, `pyntpot.ink.PaperStyle` |
| <span id="term-pigment"></span>pigment | A colour a wash or a mark lays, named by its key; what a full-strength wash of it transmits, and what it shows over black as a share of that. | `pyntpot.ink.PIGMENTS`, `pyntpot.ink.TRANSPARENCY` |
| <span id="term-painter-s-pigment"></span>painter's pigment | A pigment named by the tube a painter buys (`ultramarine`, `burnt_sienna`), not by map role; held beside `PIGMENTS` in its own table and read by no map style. | `pyntpot.ink.PAINTERS_PIGMENTS`, `pyntpot.ink.PAINTERS_TRANSPARENCY` |
| <span id="term-pigment-layer"></span>pigment layer | One layer of the pigment stack `composite` lays: a density, a pigment colour and optionally its transparency. Not the basemap's layers. | `pyntpot.ink.PigmentLayer` |
| <span id="term-density"></span>density | How much pigment or ink lies at a pixel, 0 to 1: what `wash` and `ink_density` return and a pigment layer carries. | `pyntpot.ink.ink_density` |
| <span id="term-brush"></span>brush | One mark-making tool, in render pixels: a tip of bristles stamped along a path. | `pyntpot.ink.Brush` |
| <span id="term-tip"></span>tip | The brush's bristles, sampled across and along a stroke as it is stamped. | `pyntpot.ink.Brush` |
| <span id="term-brush-sheet"></span>brush sheet | The catalogue of brush cells: stroke treatments by row `"1"` to `"8"`, the rows that are a nib, and ink colours by the id's three-letter prefix and column. A brush id `<PREFIX><row>-<column>` such as `MAJ2-a` is an opaque cell name; `ink` never reads the prefix as a feature class. | `pyntpot.ink.brush_from_id` |
| <span id="term-treatment"></span>treatment | One row of the brush sheet, `1` to `8`: how a brush behaves, how dark, how many bristles, how dry, whatever its width and ink. | `pyntpot.ink.brush_from_id` |
| <span id="term-dab"></span>dab | One small mark of a brush pressed and lifted rather than pulled: the wood's texture is laid in dabs. |  |
| <span id="term-accumulator"></span>accumulator | The float array a stroke's bristles deposit ink into, before `ink_density` turns it into a density. | `pyntpot.ink.ink_density` |
| <span id="term-line-class"></span>line class | The kind of a line on the map, such as a major road, a lane or a river, by which the style picks its brush and width. | `pyntpot.ink.BrushStyle` |

## Lettering

| Term | Meaning | In the code |
| --- | --- | --- |
| <span id="term-hand"></span>hand | The lettering writer, reading its face through `OutlineFont`. | `pyntpot.letters.Hand` |
| <span id="term-face"></span>face | The typeface the hand writes from: a font whose glyph outlines become pen paths. | `pyntpot.letters.FaceStyle` |
| <span id="term-glyph"></span>glyph | One character's shape in the face, read as an outline and traced into strokes. | `pyntpot.letters.Hand` |
| <span id="term-trace"></span>trace | How a glyph becomes strokes: `centreline` thins it to its skeleton and writes that, `outline` draws round its edge. The face style's `label_route` chooses it. | `pyntpot.letters.FaceStyle` |
| <span id="term-skeleton"></span>skeleton | The one-pixel centre line a glyph's filled shape is thinned to, which the centreline trace walks into pen strokes. | `pyntpot.letters.skeleton` |
| <span id="term-setting"></span>setting | One request to the hand: a text at a size, set along a line or flat beside an anchor, with its slant, tracking, ink and backing-wash flag. The outcome of placement, not an input to it. | `pyntpot.letters.Setting` |
| <span id="term-mark"></span>mark | One stroke the hand or a caller's furniture (the maps side's, for one) produces for the nib to run along, in display pixels, with its role, ink, size and pen tilt. | `pyntpot.letters.Mark` |
| <span id="term-backing-wash"></span>backing wash | A pale patch of the paper's own colour lifted under a name so it reads over paint; a setting's `wash` flag asks for it. | `pyntpot.letters.Setting` |
| <span id="term-nib-plate"></span>nib plate | The lettering's own RGBA plate: marks stroked through the ink engine on the paper's colour, composited normally rather than multiplied. The lettering stage keeps it in the fetch cache as `labels-centreline.webp` or `labels-outline.webp`. | `pyntpot.letters.nib_plate`, `pyntpot.letters.NibSurface` |
| <span id="term-leader"></span>leader | The thin line from a name set beside its anchor to that anchor, ending at its pin. |  |

## Maps

| Term | Meaning | In the code |
| --- | --- | --- |
| <span id="term-track"></span>track | The recorded GPS path being mapped: its points, and optionally their heights and times. | `pyntpot.maps.Track` |
| <span id="term-route"></span>route | The painted line of the track on the map; not the track itself. |  |
| <span id="term-map"></span>map | The picture of one track: the paper, washes, pen and lettering laid on its card, as `compose` returns it and `pyntpot map` writes it. The maps side's word, which `ink` and `letters` never use. | `pyntpot.maps.compose` |
| <span id="term-card"></span>card | The coordinate frame of one map: a box in card metres and the display and render pixel grids it maps to; converts between them. A canvas is the raster a plate is painted on; a card is the frame that says where things go on it. Not the picture: that is the map. | `pyntpot.maps.card.Card` |
| <span id="term-display-pixels"></span>display pixels | The card's display grid, origin top left, y down, that `Card.xy` maps card metres to; marks, settings and type sizes are in it. | `pyntpot.maps.card.Card` |
| <span id="term-render-pixels"></span>render pixels | The finer grid a plate is painted on: display pixels times `Card.render_scale`; brushes and canvases are in it. | `pyntpot.maps.card.Card` |
| <span id="term-plate"></span>plate | One painted raster layer: paper, wash, pen, labels; the painter writes each to disk. |  |
| <span id="term-plates"></span>plates | The set of plates plus its manifest, `plates.json`, for one render. | `pyntpot.maps.Plates` |
| <span id="term-manifest"></span>manifest | The plates' sidecar record (`plates.json`): the base hash, the files written and the measurements later stages read. | `pyntpot.maps.plates.Manifest` |
| <span id="term-basemap"></span>basemap | The fetched and projected layers for a bounding box. | `pyntpot.maps.Basemap`, `pyntpot.maps.fetch` |
| <span id="term-ribbon"></span>ribbon | The trimmed extent of the painted ground round the track: the washes stop at its edge and the paper shows beyond it; its radius grows with the root of the track's box. | `pyntpot.maps.Style` |
| <span id="term-cover-class"></span>cover class | The kind of a land cover area, such as wood, meadow or water, by which the style picks its pigment and wash. | `pyntpot.maps.Style` |
| <span id="term-cover-patch"></span>cover patch | One four-connected piece of a single cover class on the painter's label raster; a theme's `min_patch_px` folds the small ones into their largest neighbour. | `pyntpot.maps.painter.patches.patches` |
| <span id="term-dark-grid"></span>dark grid | The painter's coarse grid of how dark the painted map is, cell by cell, which label placement reads to keep names on light ground. | `pyntpot.maps.plates.DarkGrid` |
| <span id="term-elevation-grid"></span>elevation grid | An n by n lattice of elevations over a bounding box, as an elevation provider returns it and the fetch cache stores it. | `pyntpot.maps.providers.base.ElevationGrid` |
| <span id="term-lettering"></span>lettering | Placed labels and spans plus their painted plate. | `pyntpot.maps.Lettering`, `pyntpot.maps.letter` |
| <span id="term-label"></span>label | One name on the map as the lettering places it: its text, its anchor, its kind and the box it takes. | `pyntpot.maps.lettering.label.Label` |
| <span id="term-annotations"></span>annotations | Caller-supplied landmarks, roads, places, span requests and journal notes. | `pyntpot.maps.Annotations` |
| <span id="term-landmark"></span>landmark | A named thing a map letters beside the route, such as a fell, a bridge or a bakery: one the caller names, at its own coordinates or looked up among the basemap's candidates, or one the lettering ranks and picks itself. | `pyntpot.maps.Annotations` |
| <span id="term-place"></span>place | A settlement the caller names for the lettering always to letter. | `pyntpot.maps.Annotations` |
| <span id="term-journal-note"></span>journal note | A sentence of the caller's own, at most 60 characters, pinned to a lat/lng on the card: lettered as a flat block with a leader, seated before any other name and never moved or dropped after it; at most 6 a map. | `pyntpot.maps.JournalNote` |
| <span id="term-span"></span>span | The placed stretch of the route with a name and an intent: resolved to a pair of track indices and drawn beside the route. | `pyntpot.maps.lettering.label.Span` |
| <span id="term-span-request"></span>span request | A caller's ask to mark a stretch of the route, each end stated once by point index, kilometre or seconds from the start; lettering resolves it into a span. | `pyntpot.maps.annotations.SpanRequest` |
| <span id="term-candidate"></span>candidate | One ranked annotation option for a track: a named road, a climb, a settlement or a landmark, with its rank within its kind, where it is, and the row the export writes. | `pyntpot.maps.candidates.candidate.Candidate` |
| <span id="term-candidate-export"></span>candidate export | What a track passes, for a caller to choose names from: the route's totals and the settlements it passed, in order, each climb grounded in that route, and every landmark candidate beside it, as one JSON-ready dictionary read from the fetch cache under the track's key. | `pyntpot.maps.candidate_export` |
| <span id="term-vector-layers"></span>vector layers | The basemap's layers as SVG path data in card metres, read from the fetch cache under the track's key, with the landmarks and places chosen for the box (the style's picks replacing the chosen landmarks), for a caller that draws its own map instead of painting one. Not the painter's layers. | `pyntpot.maps.VectorLayers`, `pyntpot.maps.vector_layers` |
| <span id="term-style"></span>style | Every style group a map is painted, lettered and composed with, as one value. | `pyntpot.maps.Style` |
| <span id="term-style-group"></span>style group | One layer's share of the style, a frozen dataclass of the fields its readers read: `PaperStyle`, `NibStyle`, `BasemapStyle` and the rest. | `pyntpot.maps.Style` |
| <span id="term-theme"></span>theme | A TOML file holding one style, a table per style group. The packaged default theme is the resolved default style. | `pyntpot.maps.Style` |
| <span id="term-digest"></span>digest | A hash of some of the style's groups: `base_digest` keys the base plates, `lettering_digest` the lettering and `digest` the whole style, so a change repaints only what its digest covers. | `pyntpot.maps.Style` |
| <span id="term-route-ink"></span>route ink | How the route is drawn on the map: its `style` (`pen`, or any other value for a solid line), its width in display pixels, its colour, its blend and its opacity; the width also sets how near two passes of a retraced route have to come to be drawn as one stroke. The style field `Style.route_ink`, a theme's `[route_ink]` table; a caller feeds its colour and width through `Style.with_route_ink`. | `pyntpot.maps.Style` |
| <span id="term-credit"></span>credit | One data source's attribution: the full text, a link, and the short line drawn on the map. | `pyntpot.maps.credit.Credit` |
| <span id="term-fetch-cache"></span>fetch cache | The directory a fetch keeps its provider payloads in, keyed on the track's box, the margin and the providers' ids, which also holds each key's plates and lettering. | `pyntpot.maps.Cache` |
| <span id="term-fetch-margins"></span>fetch margins | How far beyond a track's extent the features and elevation, and the land cover, are fetched; each 0 to 20 000 m, the land cover at least the features. `Cache.margins` holds them. | `pyntpot.maps.FetchMargins` |
| <span id="term-provider"></span>provider | A source of map data behind the `Features` or `Elevation` protocol; the shipped ones are `OverpassFeatures` and `OpenTopoData`. | `pyntpot.maps.OverpassFeatures`, `pyntpot.maps.OpenTopoData` |

## Reading the docs

| Term | Meaning | In the code |
| --- | --- | --- |
| <span id="term-rung"></span>rung | One step of the watercolour tutorial: a script in `examples/` and the section that teaches it. There are seven, from stretching the paper to composing the painting. |  |
| <span id="term-reference"></span>reference | One entry of docs/explanation/references.md: a technique, its key, its canonical source and design input, and where the code implements it. |  |
