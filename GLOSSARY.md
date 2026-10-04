# Glossary

One canonical name per concept; no synonyms. Check here before introducing a term, and
add the term here when you coin one. The ported code keeps its old names until the split.

| Term | Meaning |
|---|---|
| sheet | The paper's noise fields, seeded. Today `paint.Sheet`. |
| canvas | A world-unit box and the pixel grid it paints to. Today `paint.Plate`. |
| plate | One painted raster layer written to disk: paper, wash, pen, labels. |
| plates | The set of plates plus its manifest for one render. Today `plates.json`. |
| brush | One mark-making tool. Today `paint.Brush`. |
| wash | A pigment field laid on the sheet. |
| hand | The lettering writer. Today `labels.Hand`. |
| trace | How a glyph becomes strokes: centreline or outline. Today `outlinefont.route`. |
| track | The GPS path being mapped. Today `lat, lng` lists. |
| route | The painted line of the track on the map. |
| basemap | The fetched and projected layers for a bounding box. |
| lettering | Placed labels and spans plus their painted plate. |
| annotations | Caller-supplied landmarks, roads, places and span requests. `maps.annotations.Annotations`. |
| span | The placed stretch of the route with a name and an intent: resolved to a pair of track indices and drawn beside the route. Today `labels.Span`. |
| span request | A caller's ask to mark a stretch of the route, each end stated once by point index, kilometre or seconds from the start; lettering resolves it into a span. `maps.annotations.SpanRequest`. |
| card | The coordinate frame of one map: a box in card metres and the display and render pixel grids it maps to; converts between them. A canvas (today `paint.Plate`) is the raster a plate is painted on; a card is the frame that says where things go on it. |
| manifest | The plates' sidecar record (`plates.json`): the base hash, the files written and the measurements later stages read. |
| style | Every style group a map is painted, lettered and composed with, as one value (`maps.style.Style`). |
| style group | One layer's share of the style, a frozen dataclass of the fields its readers read: `PaperStyle`, `NibStyle`, `BasemapStyle` and the rest. |
| theme | A TOML file holding one style, a table per style group. The packaged default theme is the resolved default style. |
| credit | One data source's attribution: the full text, a link, and the short line drawn on the map. `maps.credit.Credit`. |
| elevation grid | An n by n lattice of elevations over a bounding box, as an elevation provider returns it and the fetch cache stores it. `maps.providers.base.ElevationGrid`. |
| layers | The typed geometry and measurements of a basemap that the painter reads; the base hash covers exactly these and the card. `maps.basemap.Layers`. |
| elevation patch | The elevation samples a basemap carries, placed in card metres. `maps.basemap.ElevationPatch`. |
| dark grid | The painter's coarse grid of how dark the painted sheet is, cell by cell, which label placement reads to keep names on light ground. `maps.plates.DarkGrid`. |
| setting | One request to the hand: a text at a size, set along a line or flat beside an anchor, with its slant, tracking, ink and backing-wash flag. The outcome of placement, not an input to it. `letters.setting.Setting`. |
| mark | One stroke the hand or the map's furniture produces for the nib to run along, in card pixels, with its role, ink, size and pen tilt. `letters.setting.Mark`. |
