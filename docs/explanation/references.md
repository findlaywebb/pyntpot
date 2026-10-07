# References

The sources behind each technique pyntpot implements: per technique, its key, its canonical source, the work read while designing it, and the code that carries it out.

Each source was fetched and checked on the date its status shows; the status says how, and a line without one cites no new source.

A docstring names an entry by its key, in the line ``Source: `<key>` in docs/explanation/references.md.``

## `kubelka-munk` Kubelka-Munk glazing

- Canonical source: Kubelka; Munk (1931). *Zeitschrift für technische Physik* 12, 593. [verified-via-index: cited in the reference list of Kubelka 1948, https://doi.org/10.1364/JOSA.38.000448, whose Optica page 200 shows its title, author and year, by first author, year, journal, volume and first page; second author from the design record; title, initials and last page in no fetched record, so not cited; 2026-10-07]
- Design input: Curtis, C. J.; Anderson, S. E.; Seims, J. E.; Fleischer, K. W.; Salesin, D. H. (1997, year from the design record, not shown on the page). Computer-Generated Watercolor. https://grail.cs.washington.edu/projects/watercolor/paper_small.pdf [verified: PDF 200, title and every author in the text; 2026-10-07]
- Design input: Van Laerhoven, T.; Van Reeth, F. (2005). Real-time simulation of watery paint. *Computer Animation and Virtual Worlds* 16(3-4), 429-439. https://doi.org/10.1002/cav.95 [verified-via-index: Crossref record by bibliographic search, publisher page 403 challenge; 2026-10-07]
- Design input: the canonical source above.
- Implemented in: `pyntpot.ink.pigment.km_rt`, `pyntpot.ink.pigment.km_plate`

## `multiply-compositing` multiply compositing

- Canonical source: W3C (2024). Compositing and Blending Level 1. W3C Candidate Recommendation Draft, 21 March 2024. https://www.w3.org/TR/compositing-1/ [verified: page 200, title and w3c-state W3C Candidate Recommendation Draft, updated 2024-03-21; 2026-10-07]
- Design input: Watson, Z. (Stamen Design) (2012). Watercolor Process. https://stamen.com/watercolor-process-3dd5135861fe/ [verified: page 200 with its pinned words, published 2012-03-26; 2026-10-07]
- Design input: Osman (osmanyy.com) (2025). Risograph.css. https://osmanyy.com/projects/risograph-css/ [verified: page 200 with its pinned words, published 2025-07-03; 2026-10-07]
- Implemented in: `pyntpot.ink.pigment.multiply_plate`, `pyntpot.ink.pigment.composite`, `pyntpot.maps.compose._plates`

## `zhang-suen` Zhang-Suen thinning

- Canonical source: Zhang, T. Y.; Suen, C. Y. (1984). A fast parallel algorithm for thinning digital patterns. *Communications of the ACM* 27(3), 236-239. https://doi.org/10.1145/357994.358023 [verified-via-index: Crossref record, publisher page 403 challenge; 2026-10-07]
- Design input: original design reading not recorded; the canonical source stands in.
- Implemented in: `pyntpot.letters.skeleton.thin`

## `douglas-peucker` Douglas-Peucker simplification

- Canonical source: DOUGLAS, D. H.; PEUCKER, T. K. (1973). ALGORITHMS FOR THE REDUCTION OF THE NUMBER OF POINTS REQUIRED TO REPRESENT A DIGITIZED LINE OR ITS CARICATURE. *Cartographica* 10(2), 112-122. https://doi.org/10.3138/FM57-6770-U75U-7727 [verified-via-index: Crossref record, publisher page 403 challenge; 2026-10-07]
- Design input: the canonical source above.
- Implemented in: `pyntpot.ink.polyline.simplify`

## `chaikin` Chaikin corner cutting

- Canonical source: Chaikin, G. M. (1974). An algorithm for high-speed curve generation. *Computer Graphics and Image Processing* 3(4), 346-349. https://doi.org/10.1016/0146-664X(74)90028-8 [verified-via-index: Crossref record, publisher page 200 stub without authors; 2026-10-07]
- Design input: the canonical source above.
- Implemented in: `pyntpot.ink.polyline.smooth`

## `catmull-rom` Catmull-Rom spline

- Canonical source: Catmull, E.; Rom, R. (1974). A CLASS OF LOCAL INTERPOLATING SPLINES. *Computer Aided Geometric Design*, 317-326. https://doi.org/10.1016/B978-0-12-079050-0.50020-5 [verified-via-index: Crossref record, publisher page 200 stub without authors; 2026-10-07]
- Design input: original design reading not recorded; the canonical source stands in.
- Implemented in: `pyntpot.ink.curves.spline`

## `marching-squares` marching squares contours

- Canonical source: Lorensen, W. E.; Cline, H. E. (1987). Marching cubes: A high resolution 3D surface construction algorithm. *ACM SIGGRAPH Computer Graphics* 21(4), 163-169. https://doi.org/10.1145/37402.37422 [verified-via-index: Crossref record, publisher page 403 challenge; 2026-10-07]
- Design input: original design reading not recorded; the canonical source stands in.
- Implemented in: `pyntpot.maps.contours.marching_squares`
- Note: the 2-D case: `pyntpot.maps.contours.marching_squares` traces one level's contour polylines through the square cells of a grid of samples, each crossing interpolated linearly along a cell edge.

## `lanczos` Lanczos reduction

- Canonical source: Duchon, C. E. (1979). Lanczos Filtering in One and Two Dimensions. *Journal of Applied Meteorology* 18(8), 1016-1022. https://doi.org/10.1175/1520-0450(1979)018<1016:LFIOAT>2.0.CO;2 [verified-via-index: Crossref record, publisher page 403; 2026-10-07]
- Design input: original design reading not recorded; the canonical source stands in.
- Implemented in: `pyntpot.ink.pad._reduce`, `pyntpot.maps.compose._plates`, `pyntpot.maps.compose._route`, `pyntpot.maps.compose._paste_labels`
- Note: the filter is applied through Pillow: each site resizes with `Image.Resampling.LANCZOS` and computes no window of its own.

## `value-noise` value noise

- Canonical source: Lewis, J. P. (1989). Algorithms for solid noise synthesis. *ACM SIGGRAPH Computer Graphics* 23(3), 263-270. https://doi.org/10.1145/74334.74360 [verified-via-index: Crossref record, publisher page 403 challenge; 2026-10-07]
- Design input: original design reading not recorded; the canonical source stands in.
- Implemented in: `pyntpot.ink.noise.value_noise`, `pyntpot.ink.noise._value_noise_at`, `pyntpot.ink.tip._fbm1`

## `fbm` fractional Brownian motion

- Canonical source: Mandelbrot, B. B.; Van Ness, J. W. (1968). Fractional Brownian Motions, Fractional Noises and Applications. *SIAM Review* 10(4), 422-437. https://doi.org/10.1137/1010093 [verified-via-index: Crossref record, publisher page 403 challenge; 2026-10-07]
- Design input: original design reading not recorded; the canonical source stands in.
- Implemented in: `pyntpot.ink.noise.fbm`, `pyntpot.ink.noise.fbm_aniso`, `pyntpot.ink.tip._fbm1`

## `chamfer-distance` chamfer distance transform

- Canonical source: Borgefors, G. (1986). Distance transformations in digital images. *Computer Vision, Graphics, and Image Processing* 34(3), 344-371. https://doi.org/10.1016/S0734-189X(86)80047-0 [verified-via-index: Crossref record, publisher page 200 stub without authors; 2026-10-07]
- Design input: original design reading not recorded; the canonical source stands in.
- Implemented in: `pyntpot.ink.noise.edt`
- Note: the code's two-pass mask uses weights 1 and 1.41421356 (`pyntpot.ink.noise.edt`), one sweep down the rows and one back up.

## `box-blur` Gaussian by three box passes

- Canonical source: Wells, W. M. (1986). Efficient Synthesis of Gaussian Filters by Cascaded Uniform Filters. *IEEE Transactions on Pattern Analysis and Machine Intelligence* PAMI-8(2), 234-239. https://doi.org/10.1109/TPAMI.1986.4767776 [verified-via-index: Crossref record, publisher page 202 with an empty body; 2026-10-07]
- Design input: Watson, Z. (Stamen Design) (2012). Watercolor Process. https://stamen.com/watercolor-process-3dd5135861fe/ [verified: page 200 with its pinned words, published 2012-03-26; 2026-10-07]
- Implemented in: `pyntpot.ink.noise.blur`

## `hillshade` hillshade from slope and aspect

- Canonical source: Horn, B. K. P. (1981). Hill shading and the reflectance map. *Proceedings of the IEEE* 69(1), 14-47. https://doi.org/10.1109/PROC.1981.11918 [verified-via-index: Crossref record, publisher page 202 with an empty body; 2026-10-07]
- Design input: the canonical source above.
- Implemented in: `pyntpot.maps.relief._shade`
- Note: slope and aspect come from `numpy.gradient` central differences (`pyntpot.maps.relief._shade`).

## `hachures` hachures down the slope

- Canonical source: Imhof, E. (2007). Cartographic Relief Presentation. ESRI Press. ISBN 9781589480261. [verified-via-index: OpenLibrary ISBN record 9781589480261 and author record OL1273097A; 2026-10-07]
- Design input: original design reading not recorded; the canonical source stands in.
- Implemented in: `pyntpot.maps.relief_strokes.hachures`

## `midpoint-displacement` recursive midpoint displacement

- Canonical source: Fournier, A.; Fussell, D.; Carpenter, L. (1982). Computer rendering of stochastic models. *Communications of the ACM* 25(6), 371-384. https://doi.org/10.1145/358523.358553 [verified-via-index: Crossref record, publisher page 403 challenge; 2026-10-07]
- Design input: Hobbs, T. (2017). A Guide to Simulating Watercolor Paint with Generative Art. https://www.tylerxhobbs.com/words/a-guide-to-simulating-watercolor-paint-with-generative-art [verified: page 200 with its pinned words, 2017 in the body; 2026-10-07]
- Design input: Hultman, A. (axelinternet) (2018, last commit, approximate). p5-watercolor. https://github.com/axelinternet/p5-watercolor [maintainer-checked: run log 2026-10-07, owner axelinternet (Axel Hultman), About and README p5 implementation of Tyler Hobbs generative watercolor simulation, last commit about 2018; own page 403; route 5 matched, git ls-remote exit 0 at a3e995a and raw README 200, "p5 implementation of Typer Hobbs generative watercolor simulation"; 2026-10-07]
- Implemented in: `pyntpot.ink.raster.deform_ring`, `pyntpot.ink.polyline.deform_line`

## `edge-darkening` edge darkening as outward flow

- Canonical source: Curtis, C. J.; Anderson, S. E.; Seims, J. E.; Fleischer, K. W.; Salesin, D. H. (1997). Computer-generated watercolor. *Proceedings of the 24th annual conference on Computer graphics and interactive techniques - SIGGRAPH '97*, 421-430. https://doi.org/10.1145/258734.258896 [verified-via-index: Crossref record, publisher page 403 Cloudflare block; 2026-10-07]
- Design input: the canonical source above.
- Design input: Bousseau, A.; Kaplan, M.; Thollot, J.; Sillion, F. X. (2006). Interactive watercolor rendering with temporal coherence and abstraction. *Proceedings of the 4th international symposium on Non-photorealistic animation and rendering*, 141-149. https://doi.org/10.1145/1124728.1124751 [verified-via-index: Crossref record by bibliographic search, publisher page 403 challenge; 2026-10-07]
- Design input: Watson, Z. (Stamen Design) (2012). Watercolor Process. https://stamen.com/watercolor-process-3dd5135861fe/ [verified: page 200 with its pinned words, published 2012-03-26; 2026-10-07]
- Implemented in: `pyntpot.ink.wash.flow_edge`

## `backruns` backruns (blooms)

- Canonical source: Curtis, C. J.; Anderson, S. E.; Seims, J. E.; Fleischer, K. W.; Salesin, D. H. (1997). Computer-generated watercolor. *Proceedings of the 24th annual conference on Computer graphics and interactive techniques - SIGGRAPH '97*, 421-430. https://doi.org/10.1145/258734.258896 [verified-via-index: Crossref record, publisher page 403 Cloudflare block; 2026-10-07]
- Design input: the canonical source above.
- Design input: Deegan et al. Coffee-ring drying, named in the design record without a title. [named-only: deegan-coffee-ring; 2026-10-07]
- Design input: A 2019 arXiv study of watercolour drying patterns, named in the design record without a title. [named-only: arxiv-watercolour-drying; 2026-10-07]
- Implemented in: `pyntpot.ink.wash.bloom`

## `granulation` granulation following the paper

- Canonical source: Curtis, C. J.; Anderson, S. E.; Seims, J. E.; Fleischer, K. W.; Salesin, D. H. (1997). Computer-generated watercolor. *Proceedings of the 24th annual conference on Computer graphics and interactive techniques - SIGGRAPH '97*, 421-430. https://doi.org/10.1145/258734.258896 [verified-via-index: Crossref record, publisher page 403 Cloudflare block; 2026-10-07]
- Design input: the canonical source above.
- Implemented in: `pyntpot.ink.sheet.Sheet.pits`, `pyntpot.ink.wash.wash`

## `shallow-water` the shallow-water pass

- Canonical source: Curtis, C. J.; Anderson, S. E.; Seims, J. E.; Fleischer, K. W.; Salesin, D. H. (1997). Computer-generated watercolor. *Proceedings of the 24th annual conference on Computer graphics and interactive techniques - SIGGRAPH '97*, 421-430. https://doi.org/10.1145/258734.258896 [verified-via-index: Crossref record, publisher page 403 Cloudflare block; 2026-10-07]
- Design input: the canonical source above.
- Design input: Lee. Wet-on-wet painting, named in the design record without a title. [named-only: lee-wet-on-wet; 2026-10-07]
- Design input: WetBrush, a lattice-Boltzmann painting work, named in a survey list in the design record without a title. [named-only: wetbrush; 2026-10-07]
- Implemented in: `pyntpot.ink.shallow_water.shallow_water`

## `wet-area-bleed` bleed inside a shared wet-area map

- Canonical source: Luft, T.; Deussen, O. (2006). Real-time watercolor illustrations of plants using a blurred depth test. *Proceedings of the 4th international symposium on Non-photorealistic animation and rendering*, 11-20. https://doi.org/10.1145/1124728.1124732 [verified-via-index: Crossref record, publisher page 403 challenge; 2026-10-07]
- Design input: Curtis, C. J.; Anderson, S. E.; Seims, J. E.; Fleischer, K. W.; Salesin, D. H. (1997, year from the design record, not shown on the page). Computer-Generated Watercolor. https://grail.cs.washington.edu/projects/watercolor/paper_small.pdf [verified: PDF 200, title and every author in the text; 2026-10-07]
- Design input: the canonical source above.
- Implemented in: `pyntpot.ink.wash.wash`, `pyntpot.maps.painter.cover.wet_field`

## `bristle-brush` bristle brush tip and stamp

- Canonical source: Strassmann, S. (1986). Hairy brushes. *ACM SIGGRAPH Computer Graphics* 20(4), 225-232. https://doi.org/10.1145/15886.15911 [verified-via-index: Crossref record, publisher page 403 challenge; 2026-10-07]
- Design input: Chu, N. S.-H.; Tai, C.-L. (2005). MoXi: real-time ink dispersion in absorbent paper. *ACM SIGGRAPH 2005 Papers*, 504-511. https://doi.org/10.1145/1186822.1073221 [verified-via-index: Crossref record, publisher page 403 challenge; 2026-10-07]
- Design input: Baxter, W. V.; Lin, M. C. (2004). A versatile interactive 3D brush model. *12th Pacific Conference on Computer Graphics and Applications, 2004. PG 2004. Proceedings.*, 316-325. https://doi.org/10.1109/pccga.2004.1348363 [verified-via-index: Crossref record by bibliographic search, issued null, year from the container title PG 2004, publisher page 202 with an empty body; 2026-10-07]
- Implemented in: `pyntpot.ink.stamp.stamp`

## `nib` pen nib stroke

- Canonical source: Nearest published work: Strassmann, S. (1986). Hairy brushes. *ACM SIGGRAPH Computer Graphics* 20(4), 225-232. https://doi.org/10.1145/15886.15911 [verified-via-index: Crossref record, publisher page 403 challenge; 2026-10-07]
- Design input: original design reading not recorded; the canonical source stands in.
- Implemented in: `pyntpot.letters.nib.plate`
- Note: the marks are laid through the library's bristle ink pad (`pyntpot.ink.pad.InkPad`); this library's own are the broad-nib width, which follows the angle between the stroke and the nib (`pyntpot.letters.nib._pen_profile`), the optional backing wash under the marks that ask for one, and each ink's layer composited normally over the last rather than multiplied.

## `label-placement` label placement (clearance, set along a line, one name a place)

- Canonical source: Imhof, E. (1975). Positioning Names on Maps. *The American Cartographer* 2(2), 128-144. https://doi.org/10.1559/152304075784313304 [verified-via-index: Crossref record, publisher page 403 challenge; 2026-10-07]
- Design input: original design reading not recorded; the canonical source stands in.
- Implemented in: `pyntpot.maps.lettering.placement.place`

## `ink-reservoir` per-bristle ink reservoir with reload

- Canonical source: Baxter, W. V.; Lin, M. C. (2004). A versatile interactive 3D brush model. *12th Pacific Conference on Computer Graphics and Applications, 2004. PG 2004. Proceedings.*, 316-325. https://doi.org/10.1109/pccga.2004.1348363 [verified-via-index: Crossref record by bibliographic search, issued null, year from the container title PG 2004, publisher page 202 with an empty body; 2026-10-07]
- Design input: Chu, N. S.-H.; Tai, C.-L. (2005). MoXi: real-time ink dispersion in absorbent paper. *ACM SIGGRAPH 2005 Papers*, 504-511. https://doi.org/10.1145/1186822.1073221 [verified-via-index: Crossref record, publisher page 403 challenge; 2026-10-07]
- Design input: the canonical source above.
- Implemented in: `pyntpot.ink.deposit.spend`

## `pigment-separation` pigment separation into the paper's pits

- Canonical source: Curtis, C. J.; Anderson, S. E.; Seims, J. E.; Fleischer, K. W.; Salesin, D. H. (1997). Computer-generated watercolor. *Proceedings of the 24th annual conference on Computer graphics and interactive techniques - SIGGRAPH '97*, 421-430. https://doi.org/10.1145/258734.258896 [verified-via-index: Crossref record, publisher page 403 Cloudflare block; 2026-10-07]
- Design input: the canonical source above.
- Implemented in: `pyntpot.ink.wash.separated`

## Read during design, no technique here

- Read during design: Stadia Maps (n.d.). Stamen Watercolor. https://docs.stadiamaps.com/map-styles/stamen-watercolor/ [verified: page 200 with its pinned words; 2026-10-07]
- Read during design: ICA Commission on Map Design (2014). MapCarte 95/365: Pictorial Guide to the Lakeland Fells by Alfred Wainwright, 1955-1966. https://mapdesign.icaci.org/2014/04/mapcarte-95365-pictorial-guide-to-the-lakeland-fells-by-alfred-wainwright-1955-1966/ [verified: page 200 with its pinned words, 2014 in the body; 2026-10-07]
- Read during design: Nelson, J. (Adventures in Mapping) (2024). Tolkien Style Maps in a GIS: part 3, Water. https://adventuresinmapping.com/2024/02/14/7595/ [verified: page 200 with its pinned words, published 2024-02-14; 2026-10-07]
- Read during design: Urban Sketching World (n.d.). Urban Sketching Examples: Line and Wash. https://urbansketchingworld.com/line-and-wash/ [verified: page 200 with its pinned words; 2026-10-07]
- Read during design: Bugbee, L. (2014). Illustrated Wedding Maps. https://thepostmansknock.com/illustrated-wedding-maps/ [maintainer-checked: run log 2026-10-07, Illustrated Wedding Maps, Lindsey Bugbee, 13 March 2014, title, author and year match, process section paywalled; own page 403 challenge; Wayback API 429 after backoff 5, 10, 20, 40 s; snapshot 20261007 connection reset after backoff 5, 10, 20, 40 s; 2026-10-07]
- Read during design: OpenStreetMap via the Overpass API, named in the design record. [named-only: osm-overpass; 2026-10-07]
- Read during design: OSM tagging (landuse, natural, waterway, highway, boundary, historic, tourism, natural=coastline), named in the design record. [named-only: osm-tagging; 2026-10-07]
- Read during design: OpenTopoData SRTM 30 m, named in the design record. [named-only: opentopodata-srtm; 2026-10-07]
- Read during design: Open-Elevation, named in the design record as a fallback. [named-only: open-elevation; 2026-10-07]
- Read during design: Google Fonts: Patrick Hand (vendored, SIL OFL 1.1), named in the design record. [named-only: patrick-hand; 2026-10-07]
- Read during design: Google Fonts: Caveat, considered and no longer used, named in the design record. [named-only: caveat; 2026-10-07]
- Read during design: SVG filter effects (feTurbulence, feDisplacementMap, feGaussianBlur, feDropShadow), named in the design record. [named-only: svg-filter-effects; 2026-10-07]
- Read during design: CSS mix-blend-mode, named in the design record. [named-only: css-mix-blend-mode; 2026-10-07]
- Read during design: WCAG AA contrast ratios, 3:1 for marks and 4.5:1 for text, named in the design record. [named-only: wcag-aa-contrast; 2026-10-07]
- Read during design: Walk-guide and notebook route maps, National Trust and Ramblers trail leaflets, travel-journal watercolour maps and the Ordnance Survey double-line road style, named only. [named-only: walk-guide-maps; 2026-10-07]
- Read during design: The search terms given to a researcher, named only. [named-only: researcher-search-terms; 2026-10-07]
- Read during design: MapTiler and Stadia notes on Stamen Watercolor, named only; only the Stadia page was read. [named-only: maptiler-stadia-notes; 2026-10-07]
