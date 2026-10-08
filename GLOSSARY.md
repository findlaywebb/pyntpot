# Glossary

One canonical name per concept; no synonyms. Check here before introducing a term, and
add the term here when you coin one.
| Term | Meaning |
|---|---|
| sheet | The paper's noise fields, seeded; never the map. `ink.sheet.Sheet`. |
| canvas | A world-unit box and the pixel grid it paints to. `ink.sheet.Canvas`. |
| plate | One painted raster layer written to disk: paper, wash, pen, labels. |
| plates | The set of plates plus its manifest for one render. `maps.plates.Plates`, with its manifest `plates.json`. |
| brush | One mark-making tool, in render pixels: a tip of bristles stamped along a path. `ink.brush.Brush`. |
| brush sheet | The catalogue of brush cells: stroke treatments by row `"1"` to `"8"`, the rows that are a nib, and ink colours by the id's three-letter prefix and column. A brush id `<PREFIX><row>-<column>` such as `MAJ2-a` is an opaque cell name; `ink` never reads the prefix as a feature class. `ink.brush.BRUSH_TREATMENTS`, `PEN_ROWS`, `BRUSH_COLOURS`. |
| wash | A pigment field laid on the paper. |
| hand | The lettering writer. `letters.hand.Hand`, reading its face through `letters.font.OutlineFont`. |
| trace | How a glyph becomes strokes: centreline or outline. `letters.trace.CENTRELINE` or `OUTLINE`, chosen by `letters.font.OutlineFont`. |
| track | The GPS path being mapped. `maps.track.Track`. |
| route | The painted line of the track on the map. |
| basemap | The fetched and projected layers for a bounding box. |
| lettering | Placed labels and spans plus their painted plate. |
| annotations | Caller-supplied landmarks, roads, places and span requests. `maps.annotations.Annotations`. |
| span | The placed stretch of the route with a name and an intent: resolved to a pair of track indices and drawn beside the route. `maps.lettering.label.Span`. |
| span request | A caller's ask to mark a stretch of the route, each end stated once by point index, kilometre or seconds from the start; lettering resolves it into a span. `maps.annotations.SpanRequest`. |
| map | The card as drawn so far, with everything painted and lettered on it; the maps side's word, which `ink` and `letters` never use. |
| display pixels | The card's display grid, origin top left, y down, that `Card.xy` maps card metres to; marks, settings and type sizes are in it. `maps.card.Card.xy`. |
| render pixels | The finer grid a plate is painted on: display pixels times `Card.render_scale`; brushes and canvases are in it. `maps.card.Card.to_render`. |
| card | The coordinate frame of one map: a box in card metres and the display and render pixel grids it maps to; converts between them. A canvas (`ink.sheet.Canvas`) is the raster a plate is painted on; a card is the frame that says where things go on it. |
| manifest | The plates' sidecar record (`plates.json`): the base hash, the files written and the measurements later stages read. |
| style | Every style group a map is painted, lettered and composed with, as one value (`maps.style.Style`). |
| style group | One layer's share of the style, a frozen dataclass of the fields its readers read: `PaperStyle`, `NibStyle`, `BasemapStyle` and the rest. |
| theme | A TOML file holding one style, a table per style group. The packaged default theme is the resolved default style. |
| credit | One data source's attribution: the full text, a link, and the short line drawn on the map. `maps.credit.Credit`. |
| elevation grid | An n by n lattice of elevations over a bounding box, as an elevation provider returns it and the fetch cache stores it. `maps.providers.base.ElevationGrid`. |
| layers | The typed geometry and measurements of a basemap that the painter reads; the base hash covers exactly these and the card. `maps.basemap.Layers`. |
| elevation patch | The elevation samples a basemap carries, placed in card metres. `maps.basemap.ElevationPatch`. |
| dark grid | The painter's coarse grid of how dark the painted map is, cell by cell, which label placement reads to keep names on light ground. `maps.plates.DarkGrid`. |
| setting | One request to the hand: a text at a size, set along a line or flat beside an anchor, with its slant, tracking, ink and backing-wash flag. The outcome of placement, not an input to it. `letters.setting.Setting`. |
| mark | One stroke the hand or a caller's furniture (the maps side's, for one) produces for the nib to run along, in display pixels, with its role, ink, size and pen tilt. `letters.setting.Mark`. |
| candidate | One ranked annotation option for a track: a named road, a climb, a settlement or a landmark, with its rank within its kind, where it is, and the row the export writes. `maps.candidates.candidate.Candidate`. |
| backdrop | What every name on the card is priced against: the card, the route in display pixels, the dark grid and the named road centrelines. `maps.lettering.placement_costs.Backdrop`. |
| terms | What one name is priced against where it is tried: the card, the dark grid, the boxes already on the map, the roads it is charged for crossing and the weighted route. `maps.lettering.placement_costs.Terms`. |
| reference | One entry of docs/explanation/references.md: a technique, its key, its canonical source and design input, and where the code implements it. |
