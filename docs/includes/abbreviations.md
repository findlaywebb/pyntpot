<!-- Generated from GLOSSARY.md by tests/support/glossary.py. Edit GLOSSARY.md, then run: PYTHONPATH=tests uv run python -m support.glossary -->

*[tooth]: The paper's height, high where the paper stands up: a wash lightens where the tooth is high, and granulation settles where it is low. The sheet's paper field.

*[Tooth]: The paper's height, high where the paper stands up: a wash lightens where the tooth is high, and granulation settles where it is low. The sheet's paper field.

*[granulation]: Pigment settling into the paper's low places as a wash dries, so the wash reads grainy; the sheet's gran_px sets the size of its grain.

*[Granulation]: Pigment settling into the paper's low places as a wash dries, so the wash reads grainy; the sheet's gran_px sets the size of its grain.

*[foxing]: The small rust specks of an old sheet of paper, laid by the paper plate; PaperStyle.paper_foxing sets how strong.

*[Foxing]: The small rust specks of an old sheet of paper, laid by the paper plate; PaperStyle.paper_foxing sets how strong.

*[coverage mask]: The array in 0 to 1 that says where a wash goes, 1 inside the shape and 0 outside: the first argument of wash.

*[coverage masks]: The array in 0 to 1 that says where a wash goes, 1 inside the shape and 0 outside: the first argument of wash.

*[edge darkening]: The extra density a wash carries in a band just inside its edge, where the pigment gathers as the water dries: a real wash's edge darkening. wash's pool.

*[Edge darkening]: The extra density a wash carries in a band just inside its edge, where the pigment gathers as the water dries: a real wash's edge darkening. wash's pool.

*[backrun]: A second front of water pushing deposited pigment ahead of it, leaving a pale centre and a dark, crenellated ridge where it dries.

*[backruns]: A second front of water pushing deposited pigment ahead of it, leaving a pale centre and a dark, crenellated ridge where it dries.

*[Backruns]: A second front of water pushing deposited pigment ahead of it, leaving a pale centre and a dark, crenellated ridge where it dries.

*[glaze]: Laying one pigment layer over another so the light passes through both and the colours mix as transparent films, by the Kubelka-Munk model, rather than multiplying; PaperStyle.km_glazing turns it on.

*[glazes]: Laying one pigment layer over another so the light passes through both and the colours mix as transparent films, by the Kubelka-Munk model, rather than multiplying; PaperStyle.km_glazing turns it on.

*[glazed]: Laying one pigment layer over another so the light passes through both and the colours mix as transparent films, by the Kubelka-Munk model, rather than multiplying; PaperStyle.km_glazing turns it on.

*[glazing]: Laying one pigment layer over another so the light passes through both and the colours mix as transparent films, by the Kubelka-Munk model, rather than multiplying; PaperStyle.km_glazing turns it on.

*[Glazing]: Laying one pigment layer over another so the light passes through both and the colours mix as transparent films, by the Kubelka-Munk model, rather than multiplying; PaperStyle.km_glazing turns it on.

*[Kubelka-Munk]: Laying one pigment layer over another so the light passes through both and the colours mix as transparent films, by the Kubelka-Munk model, rather than multiplying; PaperStyle.km_glazing turns it on.

*[painter's pigment]: A pigment named by the tube a painter buys (ultramarine, burnt_sienna), not by map role; held beside PIGMENTS in its own table and read by no map style.

*[painter's pigments]: A pigment named by the tube a painter buys (ultramarine, burnt_sienna), not by map role; held beside PIGMENTS in its own table and read by no map style.

*[pigment layer]: One layer of the pigment stack composite lays: a density, a pigment colour and optionally its transparency. Not the basemap's layers.

*[pigment layers]: One layer of the pigment stack composite lays: a density, a pigment colour and optionally its transparency. Not the basemap's layers.

*[brush sheet]: The catalogue of brush cells: stroke treatments by row "1" to "8", the rows that are a nib, and ink colours by the id's three-letter prefix and column. A brush id <PREFIX><row>-<column> such as MAJ2-a is an opaque cell name; ink never reads the prefix as a feature class.

*[treatment]: One row of the brush sheet, 1 to 8: how a brush behaves, how dark, how many bristles, how dry, whatever its width and ink.

*[treatments]: One row of the brush sheet, 1 to 8: how a brush behaves, how dark, how many bristles, how dry, whatever its width and ink.

*[dab]: One small mark of a brush pressed and lifted rather than pulled: the wood's texture is laid in dabs.

*[dabs]: One small mark of a brush pressed and lifted rather than pulled: the wood's texture is laid in dabs.

*[accumulator]: The float array a stroke's bristles deposit ink into, before ink_density turns it into a density.

*[accumulators]: The float array a stroke's bristles deposit ink into, before ink_density turns it into a density.

*[line class]: The kind of a line on the map, such as a major road, a lane or a river, by which the style picks its brush and width.

*[line classes]: The kind of a line on the map, such as a major road, a lane or a river, by which the style picks its brush and width.

*[pigment registry]: The one catalogue of pigments: each with its canonical name, colour, transparency (or none, meaning the paper's km_transparency) and Colour Index code, looked up by name with the nearest names suggested on a miss. Read-only: adding pigments gives a new registry.

*[line effect]: A casing, glow or shadow laid round a line class or the route, composited on the colours beneath rather than glazed; off unless a theme sets one. Never applied to lettering or leaders.

*[line effects]: A casing, glow or shadow laid round a line class or the route, composited on the colours beneath rather than glazed; off unless a theme sets one. Never applied to lettering or leaders.

*[effect stack]: A line class's ordered line effects, at most one of each kind, applied in order; a theme gives one, or an effect preset's name, per line class.

*[effect stacks]: A line class's ordered line effects, at most one of each kind, applied in order; a theme gives one, or an effect preset's name, per line class.

*[effect preset]: A named effect stack, such as cased, halo or lifted, that a line class takes by name.

*[effect presets]: A named effect stack, such as cased, halo or lifted, that a line class takes by name.

*[casing]: A line effect: a band of a colour round a line and under it, so the line reads against what it crosses. A pen casing leaves the paper between two ink lines, with the wash beneath it lifted back to the paper.

*[casings]: A line effect: a band of a colour round a line and under it, so the line reads against what it crosses. A pen casing leaves the paper between two ink lines, with the wash beneath it lifted back to the paper.

*[pen casing]: A line effect: a band of a colour round a line and under it, so the line reads against what it crosses. A pen casing leaves the paper between two ink lines, with the wash beneath it lifted back to the paper.

*[glyph]: One character's shape in the face, read as an outline and traced into strokes.

*[glyphs]: One character's shape in the face, read as an outline and traced into strokes.

*[skeleton]: The one-pixel centre line a glyph's filled shape is thinned to, which the centreline trace walks into pen strokes.

*[skeletons]: The one-pixel centre line a glyph's filled shape is thinned to, which the centreline trace walks into pen strokes.

*[backing wash]: A pale patch of the paper's own colour lifted under a name so it reads over paint; a setting's wash flag asks for it.

*[backing washes]: A pale patch of the paper's own colour lifted under a name so it reads over paint; a setting's wash flag asks for it.

*[Backing wash]: A pale patch of the paper's own colour lifted under a name so it reads over paint; a setting's wash flag asks for it.

*[nib plate]: The lettering's own RGBA plate: marks stroked through the ink engine on the paper's colour, composited normally rather than multiplied. The lettering stage keeps it in the fetch cache as labels-centreline.webp or labels-outline.webp.

*[nib plates]: The lettering's own RGBA plate: marks stroked through the ink engine on the paper's colour, composited normally rather than multiplied. The lettering stage keeps it in the fetch cache as labels-centreline.webp or labels-outline.webp.

*[Nib plate]: The lettering's own RGBA plate: marks stroked through the ink engine on the paper's colour, composited normally rather than multiplied. The lettering stage keeps it in the fetch cache as labels-centreline.webp or labels-outline.webp.

*[leader]: The thin line from a name set beside its anchor to that anchor, ending at its pin.

*[leaders]: The thin line from a name set beside its anchor to that anchor, ending at its pin.

*[display pixels]: The card's display grid, origin top left, y down, that Card.xy maps card metres to; marks, settings and type sizes are in it.

*[render pixels]: The finer grid a plate is painted on: display pixels times Card.render_scale; brushes and canvases are in it.

*[basemap]: The fetched and projected layers for a bounding box.

*[basemaps]: The fetched and projected layers for a bounding box.

*[ribbon]: The trimmed extent of the painted ground round the track: the washes stop at its edge and the paper shows beyond it; its radius grows with the root of the track's box.

*[cover class]: The kind of a land cover area, such as wood, meadow or water, by which the style picks its pigment and wash.

*[cover classes]: The kind of a land cover area, such as wood, meadow or water, by which the style picks its pigment and wash.

*[cover patch]: One four-connected piece of a single cover class on the painter's label raster; a theme's min_patch_px folds the small ones into their largest neighbour.

*[cover patches]: One four-connected piece of a single cover class on the painter's label raster; a theme's min_patch_px folds the small ones into their largest neighbour.

*[dark grid]: The painter's coarse grid of how dark the painted map is, cell by cell, which label placement reads to keep names on light ground.

*[elevation grid]: An n by n lattice of elevations over a bounding box, as an elevation provider returns it and the fetch cache stores it.

*[elevation grids]: An n by n lattice of elevations over a bounding box, as an elevation provider returns it and the fetch cache stores it.

*[journal note]: A sentence of the caller's own, at most 60 characters, pinned to a lat/lng on the card: lettered as a flat block with a leader, seated before any other name and never moved or dropped after it; at most 6 a map.

*[journal notes]: A sentence of the caller's own, at most 60 characters, pinned to a lat/lng on the card: lettered as a flat block with a leader, seated before any other name and never moved or dropped after it; at most 6 a map.

*[span request]: A caller's ask to mark a stretch of the route, each end stated once by point index, kilometre or seconds from the start; lettering resolves it into a span.

*[span requests]: A caller's ask to mark a stretch of the route, each end stated once by point index, kilometre or seconds from the start; lettering resolves it into a span.

*[candidate export]: What a track passes, for a caller to choose names from: the route's totals and the settlements it passed, in order, each climb grounded in that route, and every landmark candidate beside it, as one JSON-ready dictionary read from the fetch cache under the track's key.

*[vector layers]: The basemap's layers as SVG path data in card metres, read from the fetch cache under the track's key, with the landmarks and places chosen for the box (the style's picks replacing the chosen landmarks), for a caller that draws its own map instead of painting one. Not the painter's layers.

*[style group]: One layer's share of the style, a frozen dataclass of the fields its readers read: PaperStyle, NibStyle, BasemapStyle and the rest. Each is a frozen, keyword-only dataclass named <Group>Style.

*[style groups]: One layer's share of the style, a frozen dataclass of the fields its readers read: PaperStyle, NibStyle, BasemapStyle and the rest. Each is a frozen, keyword-only dataclass named <Group>Style.

*[base theme]: The theme an override theme's extends names; its values hold wherever the override is silent. default when extends is absent.

*[colour alias]: A theme's or a palette's own name for a colour, standing for a pigment name or a hex; it names no other alias and no built-in pigment, and resolves to its hex when the theme loads.

*[colour aliases]: A theme's or a palette's own name for a colour, standing for a pigment name or a hex; it names no other alias and no built-in pigment, and resolves to its hex when the theme loads.

*[palette]: A named, shareable set of colour aliases that a theme chooses with palette, by name like a theme; it imports from and exports to a GIMP .gpl file.

*[palettes]: A named, shareable set of colour aliases that a theme chooses with palette, by name like a theme; it imports from and exports to a GIMP .gpl file.

*[route ink]: How the route is drawn on the map: its drawn_as (pen or solid), its width in display pixels, its colour, its blend and its opacity; the width also sets how near two passes of a retraced route have to come to be drawn as one stroke. The style field Style.route_ink, a theme's route_ink table; a caller feeds its colour and width through Style.with_route_ink.

*[fetch cache]: The directory a fetch keeps its provider payloads in, keyed on the track's box, the margin and the providers' ids, which also holds each key's plates and lettering.

*[fetch margins]: How far beyond a track's extent the features and elevation, and the land cover, are fetched; each 0 to 20 000 m, the land cover at least the features. Cache.margins holds them.

*[rung]: One step of the watercolour tutorial: a script in examples/ and the section that teaches it. There are seven, from stretching the paper to composing the painting.

*[rungs]: One step of the watercolour tutorial: a script in examples/ and the section that teaches it. There are seven, from stretching the paper to composing the painting.
