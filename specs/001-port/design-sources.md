# 001-port: design sources

Recovered 2026-10-04 from the three design conversations behind the map
renderer. Two of the three read no external source; this list is from the
third. Every entry is **unverified** until P6.3 checks it live and writes
`docs/explanation/references.md`; an entry that cannot be verified is
recorded there as "cited in design, not verified". The right-hand note
says which rule or technique the source informed.

## Watercolour and ink simulation

- Curtis, Anderson, Seims, Fleischer, Salesin. *Computer-Generated
  Watercolor*. SIGGRAPH 1997.
  https://grail.cs.washington.edu/projects/watercolor/paper_small.pdf
  Edge darkening, wet-area mask and capillary layer, backruns, outward
  flow at the wet boundary, granulation following paper height,
  Kubelka-Munk glazing, the shallow-water pass.
- Van Laerhoven, Van Reeth. *Real-time simulation of watery paint*. 2005.
  Kubelka-Munk compositing in place of multiply.
- Bousseau et al. *Interactive watercolor rendering with temporal
  coherence and abstraction*. NPAR 2006. Edge darkening as a distance
  term scaled to wash size.
- Luft, Deussen. *Real-time watercolor illustrations of plants*. The
  shared wet-area map so adjacent washes bleed.
- Chu, Tai. *MoXi: real-time ink dispersion in absorbent paper*. SIGGRAPH
  2005. Ink starvation; lattice-Boltzmann reference; the brush reservoir.
- Baxter, Lin. *A versatile interactive 3D brush model*. Pacific Graphics
  2004. Per-bristle ink reservoir with reload.
- Kubelka, Munk. 1931. The two-flux K and S pigment model. Glazing, and
  deriving S from reflectance so washes do not go black.
- Deegan et al., coffee-ring drying; and a 2019 arXiv study of watercolour
  drying patterns (cited by name only). Blooms as a second liquid front
  depositing a dendritic ridge.
- Lee, wet-on-wet painting; WetBrush lattice-Boltzmann work (named in a
  survey list only). Fluid pass scope; rejected at full resolution.
- Tyler Hobbs. *A guide to simulating watercolor paint with generative
  art*. 2017.
  https://www.tylerxhobbs.com/words/a-guide-to-simulating-watercolor-paint-with-generative-art
  Recursive midpoint polygon deformation for wash silhouettes; its alpha
  stacking rejected.
- axelinternet. p5-watercolor. https://github.com/axelinternet/p5-watercolor
  Implementation reference for the Hobbs method.
- Horn. *Hill shading and the reflectance map*. 1981. Hillshade from the
  elevation grid (slope and aspect).
- Douglas, Peucker. 1973. Line simplification. Chaikin. 1974. Corner
  cutting. Generalisation and smoothing of woods, roads, rivers and the
  route before painting.
- Lanczos resampling (named). Swatch and ink supersampling.
- Zhang, Suen. 1984. Thinning algorithm (named in the code, not in the
  conversations). Glyph centrelines.
- Marching squares (named in the code). Contours from the elevation grid.
- Euclidean distance transform; fractional Brownian motion and value
  noise (named in the code). Wet edges, paper and wash fields.

## Map styles and cartography

- Zach Watson, Stamen Design. *Watercolor process*.
  https://stamen.com/watercolor-process-3dd5135861fe/
  Mask, blur, noise, texture and multiply recipe; paper grain; rim
  darkening via blurred mask.
- Stadia Maps. Stamen Watercolor style docs.
  https://docs.stadiamaps.com/map-styles/stamen-watercolor/
  Why the method is raster only.
- ICA Map Design Commission. *MapCarte 95/365: A Pictorial Guide to the
  Lakeland Fells, Alfred Wainwright, 1955 to 1966*. 2014.
  https://mapdesign.icaci.org/2014/04/mapcarte-95365-pictorial-guide-to-the-lakeland-fells-by-alfred-wainwright-1955-1966/
  Pen-and-ink restraint, route weight, hatching moire warning.
- Adventures in Mapping. 2024. https://adventuresinmapping.com/2024/02/14/7595/
  Antiquarian ink style: ringed water, glyph hills. Rejected for needing
  a symbol library.
- Urban Sketching World. *Line and wash*.
  https://urbansketchingworld.com/line-and-wash/
  The chosen idiom: ink first, wash after, wash allowed to miss the line.
- The Postman's Knock. *Illustrated wedding maps*.
  https://thepostmansknock.com/illustrated-wedding-maps/
  Extent idiom: trim to a blob then bleed the edge.
- osmanyy.com. *Risograph CSS*. https://osmanyy.com/projects/risograph-css/
  Multiply as the medium, per-plate misregistration, paper card on a dark
  page.
- OpenStreetMap via the Overpass API, and OSM tagging (landuse, natural,
  waterway, highway, boundary, historic, tourism, natural=coastline).
  Woods, land cover classes, rivers, roads, landmarks, coastline, the
  land-on-the-left coast convention.
- OpenTopoData SRTM 30 m; Open-Elevation mentioned as a fallback.
  Elevation grid for contours, hillshade, hachures and the sea mask.
- Google Fonts: Patrick Hand (vendored, SIL OFL 1.1). Caveat was
  considered and is no longer used.
- SVG filter effects (feTurbulence, feDisplacementMap, feGaussianBlur,
  feDropShadow) and CSS mix-blend-mode (named). Edge bleed, paper grain,
  glow, shadow, overprint in the upstream consumer's SVG page.
- WCAG AA contrast ratios, 3:1 for marks and 4.5:1 for text (named).
  Route colour against paper and wash; label contrast.

## Named only, no source read

- Walk-guide and notebook route maps, National Trust and Ramblers trail
  leaflets, travel-journal watercolour maps, Ordnance Survey double-line
  road style. The journal card, notebook grid and double-line road
  treatment in the swatches.
- Search terms given to a researcher: "watercolour effect SVG filter",
  "generative watercolor p5", "Stamen watercolor tiles recreation".
- MapTiler and Stadia notes on Stamen Watercolor; only the Stadia page
  above was read.
