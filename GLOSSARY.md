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
| annotations | Caller-supplied landmarks, roads, places and spans. Today `MapPicks`. |
| span | A stretch of the route with a name and an intent. |
