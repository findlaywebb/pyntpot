# 001-port: references inventory

The techniques the code implements, one row per technique, each with the
sites whose bodies carry it out. P6.2 fills the design-input column and P6.3
the status column; the canonical-source column is P6.3's candidate table.

- Commit: `5299ab1` (branch `p6-docs`); no `src/` or `tests/` file differs
  from `1154129`, where the seed was taken.
- Date: 2026-10-07.
- Sites are dotted paths under `pyntpot`; the number after each is its line
  at `5299ab1`, a hint only.
- The tally command, run from the repository root:

```sh
grep -rnoiE 'kubelka|munk|zhang|suen|marching|lanczos|brownian|fbm|value.noise|chamfer|hillshad|hachur|douglas|peucker|chaikin|catmull|midpoint|bloom|backrun|granulat|shallow.water|bristle|multiply|edge.darken|wet.?area|haversine|bilinear|even.odd|scanline|flood.fill|dither|supersampl|dilat|erosion|erode' src/pyntpot --include=*.py | awk -F: '{print tolower($NF), $1}' | sort | uniq -c
```

Its output: 132 lines, 479 matches.

```text
      2 backrun src/pyntpot/ink/style.py
      4 backrun src/pyntpot/ink/wash.py
      1 backrun src/pyntpot/maps/painter/job.py
      1 bilinear src/pyntpot/ink/brush_style.py
      2 bilinear src/pyntpot/ink/deposit.py
      2 bilinear src/pyntpot/ink/pad.py
      1 bilinear src/pyntpot/ink/stamp.py
      2 bilinear src/pyntpot/ink/wash.py
      2 bilinear src/pyntpot/maps/plates.py
      2 bilinear src/pyntpot/maps/relief.py
      1 bilinear src/pyntpot/maps/relief_strokes.py
     15 bloom src/pyntpot/ink/style.py
     23 bloom src/pyntpot/ink/wash.py
      5 bloom src/pyntpot/maps/painter/cover.py
     29 bloom src/pyntpot/maps/painter/job.py
      5 bloom src/pyntpot/maps/painter/water.py
      1 bloom src/pyntpot/maps/style.py
     25 bristle src/pyntpot/ink/brush.py
     17 bristle src/pyntpot/ink/brush_style.py
      2 bristle src/pyntpot/ink/deposit.py
      3 bristle src/pyntpot/ink/pad.py
     19 bristle src/pyntpot/ink/stamp.py
      4 bristle src/pyntpot/ink/stroke.py
     24 bristle src/pyntpot/ink/tip.py
      3 catmull src/pyntpot/ink/curves.py
      1 chaikin src/pyntpot/ink/polyline.py
      1 chaikin src/pyntpot/maps/basemap_strokes.py
      2 chaikin src/pyntpot/maps/generalise.py
      2 chaikin src/pyntpot/maps/osm_elements.py
      1 chaikin src/pyntpot/maps/style_groups.py
      2 chamfer src/pyntpot/ink/noise.py
      1 dilat src/pyntpot/ink/noise.py
      1 dilat src/pyntpot/maps/masks.py
      1 dilat src/pyntpot/maps/painter/cover.py
      1 dilat src/pyntpot/maps/painter/ribbon.py
      3 dither src/pyntpot/ink/io.py
      5 dither src/pyntpot/maps/painter/job.py
      3 dither src/pyntpot/maps/painter/plates.py
      4 dither src/pyntpot/maps/painter/wood.py
      2 dither src/pyntpot/maps/style_groups.py
      1 douglas src/pyntpot/ink/polyline.py
      1 douglas src/pyntpot/maps/generalise.py
      1 douglas src/pyntpot/maps/lettering/span_line.py
      3 edge darken src/pyntpot/ink/shallow_water.py
      3 edge darken src/pyntpot/ink/style.py
      2 edge darken src/pyntpot/ink/wash.py
      1 erode src/pyntpot/maps/masks.py
      1 erode src/pyntpot/maps/painter/cover.py
      2 even-odd src/pyntpot/letters/skeleton.py
      2 even-odd src/pyntpot/maps/rings.py
      6 fbm src/pyntpot/ink/noise.py
     10 fbm src/pyntpot/ink/sheet.py
      5 fbm src/pyntpot/ink/stamp.py
      1 fbm src/pyntpot/ink/style.py
      2 fbm src/pyntpot/ink/tip.py
      4 fbm src/pyntpot/ink/wash.py
      4 fbm src/pyntpot/maps/painter/water.py
      2 fbm src/pyntpot/maps/painter/wood.py
      1 granulat src/pyntpot/ink/brush_style.py
      1 granulat src/pyntpot/ink/sheet.py
      3 granulat src/pyntpot/ink/style.py
      2 granulat src/pyntpot/ink/wash.py
      3 granulat src/pyntpot/letters/nib.py
      1 granulat src/pyntpot/maps/attribution.py
      1 granulat src/pyntpot/maps/basemap.py
      1 granulat src/pyntpot/maps/lettering_marks.py
      2 granulat src/pyntpot/maps/painter/job.py
      1 granulat src/pyntpot/maps/plates.py
      4 hachur src/pyntpot/maps/layers.py
     15 hachur src/pyntpot/maps/relief_layers.py
     12 hachur src/pyntpot/maps/relief_strokes.py
      4 hachur src/pyntpot/maps/style_groups.py
      1 hachur src/pyntpot/maps/svg_path.py
      3 haversine src/pyntpot/maps/candidates/climbs.py
      2 haversine src/pyntpot/maps/candidates/places.py
      1 hillshad src/pyntpot/maps/candidates/export.py
      4 hillshad src/pyntpot/maps/relief.py
     18 hillshad src/pyntpot/maps/relief_layers.py
      4 hillshad src/pyntpot/maps/style_groups.py
      5 kubelka src/pyntpot/ink/pigment.py
      2 kubelka src/pyntpot/ink/style.py
      1 lanczos src/pyntpot/ink/brush_style.py
      4 lanczos src/pyntpot/ink/pad.py
      4 lanczos src/pyntpot/maps/compose.py
      1 marching src/pyntpot/ink/chains.py
      1 marching src/pyntpot/ink/polyline.py
      5 marching src/pyntpot/maps/contours.py
      2 marching src/pyntpot/maps/generalise.py
      2 marching src/pyntpot/maps/relief.py
      1 midpoint src/pyntpot/ink/polyline.py
      3 midpoint src/pyntpot/ink/raster.py
      2 midpoint src/pyntpot/ink/style.py
      1 midpoint src/pyntpot/letters/font.py
      1 multiply src/pyntpot/ink/io.py
      8 multiply src/pyntpot/ink/pigment.py
      2 multiply src/pyntpot/ink/style.py
      2 multiply src/pyntpot/ink/wash.py
      1 multiply src/pyntpot/letters/nib.py
      1 multiply src/pyntpot/maps/compose.py
      1 multiply src/pyntpot/maps/style_groups.py
      5 munk src/pyntpot/ink/pigment.py
      2 munk src/pyntpot/ink/style.py
      1 peucker src/pyntpot/ink/polyline.py
      1 peucker src/pyntpot/maps/generalise.py
      1 peucker src/pyntpot/maps/lettering/span_line.py
      1 scanline src/pyntpot/ink/raster.py
      2 scanline src/pyntpot/letters/skeleton.py
      3 scanline src/pyntpot/maps/masks.py
      2 shallow water src/pyntpot/ink/shallow_water.py
      1 shallow-water src/pyntpot/ink/style.py
      2 shallow-water src/pyntpot/ink/wash.py
      1 shallow-water src/pyntpot/maps/painter/__init__.py
      1 shallow-water src/pyntpot/maps/painter/fluid.py
      2 shallow_water src/pyntpot/ink/shallow_water.py
      4 shallow_water src/pyntpot/ink/wash.py
      3 suen src/pyntpot/letters/skeleton.py
      1 suen src/pyntpot/letters/trace.py
      1 supersampl src/pyntpot/ink/brush_style.py
      2 supersampl src/pyntpot/ink/pad.py
      2 supersampl src/pyntpot/ink/raster.py
      4 supersampl src/pyntpot/maps/card_geometry.py
      1 supersampl src/pyntpot/maps/style.py
      2 supersampl src/pyntpot/maps/style_groups.py
      2 value noise src/pyntpot/ink/noise.py
      6 value_noise src/pyntpot/ink/noise.py
      2 wet area src/pyntpot/ink/shallow_water.py
      2 wet area src/pyntpot/ink/style.py
      6 wet area src/pyntpot/ink/wash.py
      1 wet-area src/pyntpot/ink/style.py
      1 wet-area src/pyntpot/ink/wash.py
      3 zhang src/pyntpot/letters/skeleton.py
      1 zhang src/pyntpot/letters/trace.py
```

| Key | Technique | Sites | Candidate canonical source | Design inputs | Status |
|---|---|---|---|---|---|
| `kubelka-munk` | Kubelka-Munk glazing | `pyntpot.ink.pigment.km_rt` (85), `pyntpot.ink.pigment.km_plate` (124) | Kubelka, Munk (1931), *Zeitschrift für technische Physik* 12, first page 593 (the title and last page are in no record P6.3 fetches, so the citation carries neither; no DOI: route 6, cited by Kubelka 1948 `10.1364/JOSA.38.000448` with a title-less reference; expected status `verified-via-index`, as in the format example) | | |
| `multiply-compositing` | multiply compositing | `pyntpot.ink.pigment.multiply_plate` (74), `pyntpot.ink.pigment.composite` (150), `pyntpot.maps.compose._plates` (42) | W3C, *Compositing and Blending Level 1*, https://www.w3.org/TR/compositing-1/ (route 1; Candidate Recommendation Draft, 21 March 2024) | | |
| `zhang-suen` | Zhang-Suen thinning | `pyntpot.letters.skeleton.thin` (88) | `10.1145/357994.358023` | | |
| `douglas-peucker` | Douglas-Peucker simplification | `pyntpot.ink.polyline.simplify` (44) | `10.3138/FM57-6770-U75U-7727` | | |
| `chaikin` | Chaikin corner cutting | `pyntpot.ink.polyline.smooth` (83) | `10.1016/0146-664X(74)90028-8` | | |
| `catmull-rom` | Catmull-Rom spline | `pyntpot.ink.curves.spline` (26) | `10.1016/B978-0-12-079050-0.50020-5` | | |
| `marching-squares` | marching squares contours | `pyntpot.maps.contours.marching_squares` (33) | `10.1145/37402.37422`, the 2-D case | | |
| `lanczos` | Lanczos reduction | `pyntpot.ink.pad._reduce` (118), `pyntpot.maps.compose._plates` (42), `pyntpot.maps.compose._route` (52), `pyntpot.maps.compose._paste_labels` (88) | `10.1175/1520-0450(1979)018<1016:LFIOAT>2.0.CO;2` (Duchon 1979 defines the Lanczos-windowed filter by that name; Lanczos's own σ-factor work is a 1956 book with no DOI; `Note:` the filter is applied through Pillow) | | |
| `value-noise` | value noise | `pyntpot.ink.noise.value_noise` (26), `pyntpot.ink.noise._value_noise_at` (61), `pyntpot.ink.tip._fbm1` (125) | `10.1145/74334.74360` (Lewis 1989, which describes lattice value noise; Perlin 1985 `10.1145/325165.325247` is gradient noise, which the body of `value_noise`, a smoothstep-interpolated lattice of random values, is not) | | |
| `fbm` | fractional Brownian motion | `pyntpot.ink.noise.fbm` (48), `pyntpot.ink.noise.fbm_aniso` (101), `pyntpot.ink.tip._fbm1` (125) | `10.1137/1010093` | | |
| `chamfer-distance` | chamfer distance transform | `pyntpot.ink.noise.edt` (168) | `10.1016/S0734-189X(86)80047-0` (`Note:` the code's two-pass mask uses weights 1 and 1.41421356, `pyntpot.ink.noise.edt`; the paper was checked from its Crossref record only, so the note states the code's weights and makes no claim about the paper's) | | |
| `box-blur` | Gaussian by three box passes | `pyntpot.ink.noise.blur` (156) | `10.1109/TPAMI.1986.4767776` | | |
| `hillshade` | hillshade from slope and aspect | `pyntpot.maps.relief._shade` (128) | `10.1109/PROC.1981.11918` | | |
| `hachures` | hachures down the slope | `pyntpot.maps.relief_strokes.hachures` (171) | Imhof, *Cartographic Relief Presentation*, ESRI Press 2007, ISBN 9781589480261 (route 4) | | |
| `midpoint-displacement` | recursive midpoint displacement | `pyntpot.ink.raster.deform_ring` (61), `pyntpot.ink.polyline.deform_line` (302) | `10.1145/358523.358553` | | |
| `edge-darkening` | edge darkening as outward flow | `pyntpot.ink.wash.flow_edge` (57) | `10.1145/258734.258896` | | |
| `backruns` | backruns (blooms) | `pyntpot.ink.wash.bloom` (90) | `10.1145/258734.258896` | | |
| `granulation` | granulation following the paper | `pyntpot.ink.sheet.Sheet.pits` (98), `pyntpot.ink.wash.wash` (177) | `10.1145/258734.258896` | | |
| `shallow-water` | the shallow-water pass | `pyntpot.ink.shallow_water.shallow_water` (24) | `10.1145/258734.258896` | | |
| `wet-area-bleed` | bleed inside a shared wet-area map | `pyntpot.ink.wash.wash` (177), `pyntpot.maps.painter.cover.wet_field` (32) | `10.1145/1124728.1124732` (Luft, Deussen 2006; rule 2, no eponym: the design record reads it for "the shared wet-area map so adjacent washes bleed", which is what `wet_field` and `wash` carry out; the design record names Curtis 1997's "wet-area mask" among the parts of a fluid simulation, not as a bleed between washes, so Curtis is this row's design input, not its canonical source) | | |
| `bristle-brush` | bristle brush tip and stamp | `pyntpot.ink.stamp.stamp` (248) | `10.1145/15886.15911` | | |
| `nib` | pen nib stroke | `pyntpot.letters.nib.plate` (273) | nearest published work, rule 5: `10.1145/15886.15911` | | |
| `label-placement` | label placement (clearance, set along a line, one name a place) | `pyntpot.maps.lettering.placement.place` (70) | `10.1559/152304075784313304` | | |


Sites added to seed rows at P6.1, each by the site rule (the body carries
the technique out; a library call's site is the function that chooses and
applies it):

- `multiply-compositing`: `pyntpot.ink.pigment.composite`, whose multiply
  branch multiplies the stacked plate over the backing itself; and
  `pyntpot.maps.compose._plates`, which multiplies the wash over the paper
  with `ImageChops.multiply`.
- `lanczos`: `pyntpot.maps.compose._plates`, `_route` and `_paste_labels`,
  each of which resizes a plate to the card with
  `Image.Resampling.LANCZOS` (`_route` reduces a line drawn `ROUTE_SS` times
  finer).
- `value-noise`: `pyntpot.ink.noise._value_noise_at`, a smoothstep-interpolated
  lattice of random values sampled at given coordinates (what `fbm_aniso`
  sums); and `pyntpot.ink.tip._fbm1`, whose octave loop builds the same
  lattice along a stroke inline.
- `granulation`: `pyntpot.ink.wash.wash`, which lays the granulation: it
  scales the density by `Sheet.pits` (or by the `gran` field when the gamma
  is 0).

No seed row is dropped. Functions the tally places a seed term in that are
not sites (they pass arguments to a site, name a technique in prose, or hold
settings with no body):

- Callers: `pyntpot.maps.generalise.trace_mask`,
  `pyntpot.maps.osm_elements._soften`, `pyntpot.maps.basemap_strokes.drawn`,
  `pyntpot.maps.lettering.span_line.shape_curve` (call `simplify`, `smooth`,
  `spline`, `marching_squares`); `pyntpot.maps.contours.contour_lines` and
  `sea_rings`, `pyntpot.maps.relief.shade_bands` and `hillshade_png` (call
  `marching_squares` and `_shade`); `pyntpot.maps.relief_layers._shading`,
  `_hachure_strokes` and `_relief_layers` (call `shade_bands`, `hillshade_png`,
  `hachures`); `pyntpot.ink.sheet.Sheet.__post_init__` and `Sheet.noise`,
  `pyntpot.maps.painter.water.sea_patches`, `pyntpot.maps.painter.wood._texture`
  (call `fbm`, `fbm_aniso`); `pyntpot.ink.stamp._pressure`, `_wobble` and
  `_organic_fields` (call `_fbm1`); `pyntpot.maps.painter.job.PaintJob.bloom`,
  `PaintJob.begin`, `pyntpot.maps.painter.cover._class_washes` and
  `_pale_wash`, `pyntpot.maps.painter.water.paint_lakes` and `sea_layer` (size
  or pass the `bloom` argument); `pyntpot.ink.wash.fluid_modulate` and
  `pyntpot.maps.painter.fluid.paint_fluid` (seed table, `shallow-water` row);
  `pyntpot.letters.nib._backing_wash` (calls `wash`, `edt`, `blur`).
- Parts of the `bristle-brush` site `pyntpot.ink.stamp.stamp`, which composes
  them: `pyntpot.ink.stamp._draw_tip`, `_sample_tip`, `_offsets`, `_lanes`;
  `pyntpot.ink.tip._tip_band`, `_tip_drift`, `_unfold`, `_spread`;
  `pyntpot.ink.deposit.weights`; `pyntpot.ink.pad._bleed`, `InkPad`,
  `InkPad.lay`. Parts of the `hachures` site: `pyntpot.maps.relief_strokes._stroke_at`
  and `_jitter`.
- Prose only: `pyntpot.ink.chains.join_chains` (marching squares' saddle
  cells), `pyntpot.letters.trace._dots` (what Zhang-Suen deletes),
  `pyntpot.letters.font._Flatten.qCurveTo` (TrueType's implied midpoint),
  `pyntpot.ink.io.save_rgba` and `pyntpot.ink.wash.separated` (why a plate is
  not multiplied), `pyntpot.maps.svg_path.stroke_d` (why hachures are written
  relative); and a setting's name only: `pyntpot.maps.layers._derived`,
  `pyntpot.maps.painter.job.PaintJob.gran_gamma`.
- Settings with no body: `pyntpot.ink.style.WashStyle`, `PaperStyle`,
  `pyntpot.ink.brush_style.BrushStyle`, `pyntpot.ink.brush.Brush`,
  `pyntpot.ink.stroke.Tip`, `pyntpot.ink.wash.WashOptions`,
  `pyntpot.letters.nib.NibSurface`, `pyntpot.maps.style.Style`,
  `pyntpot.maps.style_groups.BasemapStyle` and `CoverStyle`,
  `pyntpot.maps.basemap.Layers`, `pyntpot.maps.plates.Manifest`,
  `pyntpot.maps.generalise.Generalisation`, `pyntpot.maps.relief_strokes.Hatching`
  and `Field`; and the module docstrings the tally counts.

The decided terms, each `considered, excluded: elementary` (plan, P6.1):

- haversine: `maps/candidates/climbs.py`, `maps/candidates/places.py`.
- bilinear: `ink/brush_style.py`, `ink/deposit.py`, `ink/pad.py`,
  `ink/stamp.py`, `ink/wash.py`, `maps/plates.py`, `maps/relief.py`,
  `maps/relief_strokes.py`.
- even-odd: `letters/skeleton.py`, `maps/rings.py`.
- scanline fill: `ink/raster.py`, `letters/skeleton.py`, `maps/masks.py`.
- flood fill: no hit.
- dither: `ink/io.py`, `maps/painter/job.py`, `maps/painter/plates.py`,
  `maps/painter/wood.py`, `maps/style_groups.py`.
- supersampling: `ink/brush_style.py`, `ink/pad.py`, `ink/raster.py`,
  `maps/card_geometry.py`, `maps/style.py`, `maps/style_groups.py`.
- dilation and erosion: `ink/noise.py`, `maps/masks.py`,
  `maps/painter/cover.py`, `maps/painter/ribbon.py`.
- `smoothstep`, linear interpolation, a clamp, a mitre limit: elementary
  formula.

WCAG contrast is not a row: no code computes a luminance or a contrast
ratio, so its `design-sources.md` entry goes to the closing section as
`named-only`.

Techniques met that are in neither the seed nor the decided terms, filed
and not added: pigment separation
(`docs/issues/unlisted-technique-pigment-separation.md`), the per-bristle
ink reservoir (`docs/issues/unlisted-technique-ink-reservoir.md`) and the
blurred-mask rim (`docs/issues/unlisted-technique-blurred-mask-rim.md`). The
name mismatch of the `chamfer-distance` site is
`docs/issues/edt-is-a-chamfer-distance.md`.
