# 0005 — Style groups

Status: accepted

## Context

The painter's settings live in two flat classes inside the interim `_port` code:
`PaintStyle`, 173 fields covering the paper, the washes, the brushes, the lettering, the
ribbon, the land cover and the route plate, and `GeoOptions`, 28 fields saying what the
basemap draws. Every reader takes the whole of `PaintStyle`, so nothing records which
layer a field belongs to, and changing a lettering-only field looks, to anything keyed on
the style, like a change that repaints every plate.

The target layering is `maps -> letters -> ink`. A field read by the ink engine cannot
live in `maps`, a field read by the hand cannot live in `maps` either, and `letters` has
no base plates of its own. The resolved default style, including one route ink per sport,
is a settled value: it is what the reference sheets were painted with.

## Decision

The fields are split into frozen stdlib dataclasses, one per group, each in the lowest
layer that reads it. They are plain dataclasses, not pydantic models, because `ink` and
`letters` may never import pydantic.

| Group | Module | Layer | Kind | Fields |
|---|---|---|---|---|
| `PaperStyle` | `pyntpot.ink.style` | ink | base | 21 |
| `WashStyle` | `pyntpot.ink.style` | ink | base | 44 |
| `BrushStyle` | `pyntpot.ink.brush_style` | ink | base | 45 |
| `FaceStyle` | `pyntpot.letters.style` | letters | lettering | 2 |
| `HandStyle` | `pyntpot.letters.style` | letters | lettering | 1 |
| `NibStyle` | `pyntpot.letters.style` | letters | lettering | 16 |
| `CardStyle` | `pyntpot.maps.style_groups` | maps | base | 3 |
| `RibbonStyle` | `pyntpot.maps.style_groups` | maps | base | 16 |
| `CoverStyle` | `pyntpot.maps.style_groups` | maps | base | 13 |
| `RouteStyle` | `pyntpot.maps.style_groups` | maps | base | 3 |
| `BasemapStyle` | `pyntpot.maps.style_groups` | maps | base | 27 |
| `LetteringPolicy` | `pyntpot.maps.style_groups` | maps | lettering | 5 |
| `RouteInks` | `pyntpot.maps.style_groups` | maps | compose only | 4 |
| `CONSUMER_ONLY` | `pyntpot.maps.style_groups` | none | not in the style | 4 |

`BrushStyle` sits in its own module beside `pyntpot.ink.style` only because the three ink
groups, with their field comments, are over the 400-line budget in one file.

Each field's dataclass default is its source class default (`PaintStyle` or
`GeoOptions`), copied verbatim; defaults that name a `_port.paint` constant (`PAPER`,
`PIGMENTS`, `TRANSPARENCY`, `COVER_CFG`) are literal copies, because `ink` and `letters`
never import `_port` and `maps.style_groups` imports only `_port.style`. The resolved and
effective values belong to the theme, not to these defaults. Each field keeps its `#:`
comment as its documentation.

### The assignment rule

The table below is final. This rule is how it was derived.

1. **Readers at their final homes.** A field's readers are the functions that read it,
   at the module the split gives them:

   | Reader today | Final home | Kind |
   |---|---|---|
   | `paint.brush_from_id`, `InkPad.__init__` | `ink/brush.py`, `ink/pad.py` | ink |
   | `paint.composite`; `separated`, `fluid_modulate` | `ink/pigment.py`; `ink/wash.py` | ink |
   | `paint.label_brushes`, `label_plate`, `_backing_wash`, `_pen_profile` | `letters/nib.py` | letters |
   | `labels.Hand.__init__` | `letters/hand.py` | letters |
   | `paint.paint` (and its nested `transp`, `bloom_arg`), `paper_plate`, `plate_brushes`, `sea_patches` | `maps/painter/*` | maps base |
   | `geo.journal_geometry`, `journal_layers`, and every `GeoOptions` reader | `maps/layers.py`, `maps/osm.py` | maps base |
   | `mapcard.compose`, `labels.home_labels`, `labels.named_lines` | `maps/lettering/*`, `maps/compose.py` | maps lettering |
   | `labels.hand()` (`labels`), `mapcard.alphabet_sheet` | deleted; `letter` takes over the `labels` check | maps lettering |

   `paint._dark_field` reads no style field and decides nothing. `label_geom_tol_px` is
   read today by `paint.paint`, but that read moves into `labels.named_lines`, so its
   final reader is maps lettering.
2. **Base or lettering.** A field with any ink or maps-base reader goes to a base group. A
   field whose readers are all `letters` or maps lettering goes to a lettering group, so no
   lettering-only field is in the base digest.
3. **Layer.** A base field with an ink or `letters` reader goes to an ink group (`letters`
   has no base group, and `letters` may import `ink`). A lettering field with a `letters`
   reader goes to a `letters` group: `FaceStyle` if `Hand` opens the face with it
   (`label_face`, `label_route`), `HandStyle` if `Hand` reads it otherwise (`label_seed`),
   else `NibStyle`. A lettering field read only in maps goes to `LetteringPolicy`.
4. **Section.** Within what rules 2 and 3 allow, the `PaintStyle` section comment picks
   the group: the ribbon to `RibbonStyle`; land cover and the wood to `CoverStyle`; the
   ink, phase 1 brush and phase 2 brush quality to `BrushStyle`; the route's own plate to
   `RouteStyle`; phase 2 tuning and sea and phase 2 wash to `WashStyle`. Three sections
   mix concerns and are assigned field by field: the card (frame, paper, encoder, seeds),
   phase 1 compositing and paper (paper and compositing to `PaperStyle`; wet bleed, flow
   rim and blooms to `WashStyle`, beside `bloom_strength`), and the crisp layer (rules 2
   and 3; `dark_grid`, read only by the painter, to `CardStyle`). A base field read only
   by the painter may sit in any base group, because the painter reads every base group;
   this is why, for example, `blotch_m` and `wet_bleed` are in ink groups.
5. **Consumer-only** (`PaintStyle` fields only). A `PaintStyle` field no module under
   `src/` reads, except through the key lists of `digest`, `paint_hash` or `labels_hash`,
   is left out of the style and named in `CONSUMER_ONLY`: `cover_order`, `label_font`,
   `label_pin_colour`, `label_glow_colour`. Rule 5 does not apply to `GeoOptions`.

Readers that cross groups, by design (each takes every group it reads as a parameter):
the nib code reads `NibStyle`, `FaceStyle` (`label_route`), `HandStyle` (`label_seed`),
`BrushStyle` and `PaperStyle`; `Hand` reads `FaceStyle` and `HandStyle`; the maps
lettering code reads `LetteringPolicy` and `NibStyle.label_size_px`; the painter reads
every base group.

### The basemap options are the effective ones

`BasemapStyle` carries all 27 `GeoOptions` fields other than `clip_margin_m`, read or not,
because the effective basemap options are one value of the resolved default style. The
values the painter actually uses are the `GeoOptions` class defaults plus the inline
overrides in `journal_layers`: `hillshade_mode="off"`, `roads="key"`, `rivers="key"`,
`generalise=False`, `landmarks="all"`, `landmark_max=40`; the theme carries those.
`clip_margin_m` is derived from the card per render and is not a style field.

Two `BasemapStyle` fields have no reader in `src/`: `hillshade_opacity` and
`pick_places`. They stay in `BasemapStyle`, and so in the base digest, kept for the
upstream consumer.

The resolved theme's `geo` section is not used. It differs from the effective values on
four fields, and those values belong to the upstream consumer's vector map:

| Field | Resolved theme `geo` | Effective (painter) |
|---|---|---|
| `interaction_m` | 80 | 60 |
| `landmark_radius_m` | 250 | 300 |
| `landmark_max` | 3 | 40 |
| `hillshade_levels` | 2 | 5 |

The candidate landmark export keeps its own option set with the candidates code; it is
not part of the style.

### Route ink

The resolved default style fixes one `RouteInk` per sport, so `RouteInks` carries all
four resolved inks (`run`, `ride`, `swim`, `other`), each a `RouteInk` imported by name
from `pyntpot._port.style`. It has no dataclass defaults, because no source class carries
one; the theme supplies them. The style's route ink is always `route_inks.ride`, the ink
the reference sheets were painted with. There is no sport selection: no sport on the
style, none on the track, no command-line flag. `route_inks` is read only when the card
is composed, so it is in the full digest but in neither the base nor the lettering
digest: changing an ink repaints no plate. The three `PaintStyle` route-plate fields,
which the painter does read, are `RouteStyle`, a base group. Choosing an ink by sport is
a later feature with its own ADR.

### The field-to-group table

All 173 `PaintStyle` fields and the 27 `GeoOptions` fields other than `clip_margin_m`,
one row each, in source order, with the readers that decided the row. A reader through a
digest's key list is not a reader.

| Field | Source | Group | Layer | Readers that decided it (kind at final home) |
|---|---|---|---|---|
| `display_px` | `PaintStyle` | `CardStyle` | maps | `geo.journal_geometry` (maps base), `paint.paper_plate` (maps base) |
| `supersample` | `PaintStyle` | `CardStyle` | maps | `geo.journal_geometry` (maps base) |
| `plate_lossless` | `PaintStyle` | `PaperStyle` | ink | `paint.label_plate` (letters), `paint.paint` (maps base) |
| `webp_quality` | `PaintStyle` | `PaperStyle` | ink | `paint.paint` (maps base) |
| `paper_quality` | `PaintStyle` | `PaperStyle` | ink | `paint.label_plate` (letters), `paint.paint` (maps base) |
| `grid` | `PaintStyle` | `PaperStyle` | ink | `paint.paper_plate` (maps base) |
| `grid_spacing_px` | `PaintStyle` | `PaperStyle` | ink | `paint.paper_plate` (maps base) |
| `grid_opacity` | `PaintStyle` | `PaperStyle` | ink | `paint.paper_plate` (maps base) |
| `paper_hex` | `PaintStyle` | `PaperStyle` | ink | `mapcard.alphabet_sheet` (deleted), `paint._backing_wash` (letters), `paint.paper_plate` (maps base) |
| `paper_tooth` | `PaintStyle` | `PaperStyle` | ink | `paint.paper_plate` (maps base) |
| `paper_worn` | `PaintStyle` | `PaperStyle` | ink | `paint.paper_plate` (maps base) |
| `paper_vignette` | `PaintStyle` | `PaperStyle` | ink | `paint.paper_plate` (maps base) |
| `paper_foxing` | `PaintStyle` | `PaperStyle` | ink | `paint.paper_plate` (maps base) |
| `sheet_seed` | `PaintStyle` | `PaperStyle` | ink | `paint.label_plate` (letters), `paint.paint` (maps base) |
| `ink_seed` | `PaintStyle` | `BrushStyle` | ink | `paint.paint` (maps base) |
| `dither_seed` | `PaintStyle` | `CoverStyle` | maps | `paint.paint` (maps base) |
| `ribbon_k` | `PaintStyle` | `RibbonStyle` | maps | `geo.journal_geometry` (maps base) |
| `ribbon_c` | `PaintStyle` | `RibbonStyle` | maps | `geo.journal_geometry` (maps base) |
| `ribbon_mult` | `PaintStyle` | `RibbonStyle` | maps | `geo.journal_geometry` (maps base) |
| `ribbon_min_m` | `PaintStyle` | `RibbonStyle` | maps | `geo.journal_geometry` (maps base) |
| `ribbon_max_m` | `PaintStyle` | `RibbonStyle` | maps | `geo.journal_geometry` (maps base) |
| `card_grow_mult` | `PaintStyle` | `RibbonStyle` | maps | `geo.journal_geometry` (maps base) |
| `card_pad_frac` | `PaintStyle` | `RibbonStyle` | maps | `geo.journal_geometry` (maps base) |
| `card_pad_ribbon_frac` | `PaintStyle` | `RibbonStyle` | maps | `geo.journal_geometry` (maps base) |
| `card_aspect_min` | `PaintStyle` | `RibbonStyle` | maps | `geo.journal_geometry` (maps base) |
| `card_aspect_max` | `PaintStyle` | `RibbonStyle` | maps | `geo.journal_geometry` (maps base) |
| `ribbon_fill` | `PaintStyle` | `RibbonStyle` | maps | `paint.paint` (maps base) |
| `ribbon_tear_frac` | `PaintStyle` | `RibbonStyle` | maps | `paint.paint` (maps base) |
| `ribbon_tear_floor_px` | `PaintStyle` | `RibbonStyle` | maps | `paint.paint` (maps base) |
| `rim_strength` | `PaintStyle` | `RibbonStyle` | maps | `paint.paint` (maps base) |
| `coast_hard_mask` | `PaintStyle` | `RibbonStyle` | maps | `paint.paint` (maps base) |
| `sea_to_edge` | `PaintStyle` | `RibbonStyle` | maps | `paint.paint` (maps base) |
| `land_cover` | `PaintStyle` | `CoverStyle` | maps | `paint.paint` (maps base) |
| `relief` | `PaintStyle` | `CoverStyle` | maps | `paint.paint` (maps base) |
| `cover_order` | `PaintStyle` | `CONSUMER_ONLY` | none | none in `src/` |
| `cover_cfg` | `PaintStyle` | `CoverStyle` | maps | `paint.paint` (maps base) |
| `pigments` | `PaintStyle` | `CoverStyle` | maps | `paint.paint` (maps base) |
| `pale_base` | `PaintStyle` | `CoverStyle` | maps | `paint.paint` (maps base) |
| `pale_pool` | `PaintStyle` | `CoverStyle` | maps | `paint.paint` (maps base) |
| `wood_texture` | `PaintStyle` | `CoverStyle` | maps | `paint.paint` (maps base) |
| `wood_dabs` | `PaintStyle` | `CoverStyle` | maps | `paint.paint` (maps base) |
| `wood_tex_scales` | `PaintStyle` | `CoverStyle` | maps | `paint.paint` (maps base) |
| `wood_tex_strengths` | `PaintStyle` | `CoverStyle` | maps | `paint.paint` (maps base) |
| `dab_spacings` | `PaintStyle` | `CoverStyle` | maps | `paint.paint` (maps base) |
| `dab_strengths` | `PaintStyle` | `CoverStyle` | maps | `paint.paint` (maps base) |
| `river_curve` | `PaintStyle` | `BrushStyle` | ink | `geo.journal_geometry` (maps base) |
| `major_river_rel_frac` | `PaintStyle` | `BrushStyle` | ink | `geo.journal_layers` (maps base) |
| `minor_roads_mppd` | `PaintStyle` | `BrushStyle` | ink | `geo.journal_geometry` (maps base) |
| `blotch_m` | `PaintStyle` | `BrushStyle` | ink | `geo.journal_geometry` (maps base) |
| `dab_spacing_m` | `PaintStyle` | `BrushStyle` | ink | `geo.journal_geometry` (maps base) |
| `gran_m` | `PaintStyle` | `BrushStyle` | ink | `geo.journal_geometry` (maps base) |
| `river_mult` | `PaintStyle` | `BrushStyle` | ink | `paint.paint` (maps base), `paint.plate_brushes` (maps base) |
| `brushes` | `PaintStyle` | `BrushStyle` | ink | `paint.paint` (maps base), `paint.plate_brushes` (maps base) |
| `brush_width_px` | `PaintStyle` | `BrushStyle` | ink | `geo.journal_layers` (maps base), `paint.plate_brushes` (maps base) |
| `coast_width_frac` | `PaintStyle` | `BrushStyle` | ink | `paint.plate_brushes` (maps base) |
| `brush_jitter_px` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `brush_press_cell_px` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `brush_wobble_px` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `brush_step` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `brush_profile_px` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `pen_load_px_frac` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `pen_pool_radius_frac` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `pen_pool_gain` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `brush_overrides` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `route_pen` | `PaintStyle` | `RouteStyle` | maps | `paint.paint` (maps base) |
| `route_pen_brush` | `PaintStyle` | `RouteStyle` | maps | `paint.paint` (maps base) |
| `route_pen_width_px` | `PaintStyle` | `RouteStyle` | maps | `paint.paint` (maps base) |
| `label_font` | `PaintStyle` | `CONSUMER_ONLY` | none | none in `src/` |
| `label_size_px` | `PaintStyle` | `NibStyle` | letters | `labels.home_labels` (maps lettering), `mapcard.alphabet_sheet` (deleted), `mapcard.compose` (maps lettering), `paint._backing_wash` (letters), `paint.label_brushes.brush` (letters) |
| `label_max` | `PaintStyle` | `LetteringPolicy` | maps | `mapcard.compose` (maps lettering) |
| `label_pin_colour` | `PaintStyle` | `CONSUMER_ONLY` | none | none in `src/` |
| `label_ink` | `PaintStyle` | `NibStyle` | letters | `paint.label_plate` (letters) |
| `label_glow_colour` | `PaintStyle` | `CONSUMER_ONLY` | none | none in `src/` |
| `labels` | `PaintStyle` | `LetteringPolicy` | maps | `labels.hand` (deleted) |
| `label_ground` | `PaintStyle` | `LetteringPolicy` | maps | `mapcard.compose` (maps lettering) |
| `label_seed` | `PaintStyle` | `HandStyle` | letters | `labels.Hand.__init__` (letters), `paint.label_plate` (letters) |
| `label_geom_tol_px` | `PaintStyle` | `LetteringPolicy` | maps | `labels.named_lines` (maps lettering, after the read moves there) |
| `label_route` | `PaintStyle` | `FaceStyle` | letters | `labels.Hand.__init__` (letters), `paint.label_brushes.brush` (letters) |
| `label_face` | `PaintStyle` | `FaceStyle` | letters | `labels.Hand.__init__` (letters) |
| `label_brush` | `PaintStyle` | `NibStyle` | letters | `paint.label_brushes.brush` (letters) |
| `label_pen_width_px` | `PaintStyle` | `NibStyle` | letters | `paint.label_brushes.brush` (letters) |
| `label_outline_width_frac` | `PaintStyle` | `NibStyle` | letters | `paint.label_brushes.brush` (letters) |
| `label_leader_brush` | `PaintStyle` | `NibStyle` | letters | `paint.label_brushes.brush` (letters) |
| `label_leader_width_px` | `PaintStyle` | `NibStyle` | letters | `paint.label_brushes.brush` (letters) |
| `label_pen_angle_deg` | `PaintStyle` | `NibStyle` | letters | `paint.label_plate` (letters) |
| `label_pen_thin` | `PaintStyle` | `NibStyle` | letters | `paint.label_plate` (letters) |
| `label_wash` | `PaintStyle` | `NibStyle` | letters | `paint.label_plate` (letters) |
| `label_wash_alpha` | `PaintStyle` | `NibStyle` | letters | `paint._backing_wash` (letters) |
| `label_wash_dark_floor` | `PaintStyle` | `NibStyle` | letters | `paint._backing_wash` (letters) |
| `label_wash_spread` | `PaintStyle` | `NibStyle` | letters | `paint._backing_wash` (letters) |
| `label_route_ink` | `PaintStyle` | `NibStyle` | letters | `paint.label_plate` (letters) |
| `label_water_ink` | `PaintStyle` | `NibStyle` | letters | `paint.label_plate` (letters) |
| `label_in_water_ink` | `PaintStyle` | `NibStyle` | letters | `paint.label_plate` (letters) |
| `home_glyph` | `PaintStyle` | `LetteringPolicy` | maps | `labels.home_labels` (maps lettering) |
| `dark_grid` | `PaintStyle` | `CardStyle` | maps | `paint.paint` (maps base) |
| `ink_starve` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `ink_reservoir` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `ink_res_floor` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `ink_dip_mult` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `ink_knee` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `dry_directional` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `dry_dir_elong` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `dry_dir_cell_px` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `dry_dir_gain` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `dry_dir_mix` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `pen_starve` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `pen_reservoir` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `pen_thin` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `km_glazing` | `PaintStyle` | `PaperStyle` | ink | `paint.composite` (ink) |
| `pigment_transparency` | `PaintStyle` | `PaperStyle` | ink | `paint.paint.transp` (maps base) |
| `km_transparency` | `PaintStyle` | `PaperStyle` | ink | `paint.composite` (ink), `paint.paint.transp` (maps base) |
| `paper_fibre` | `PaintStyle` | `PaperStyle` | ink | `paint._backing_wash` (letters), `paint.label_plate` (letters), `paint.paint` (maps base) |
| `paper_fibre_mix` | `PaintStyle` | `PaperStyle` | ink | `paint.label_plate` (letters), `paint.paint` (maps base) |
| `paper_fibre_stretch` | `PaintStyle` | `PaperStyle` | ink | `paint.label_plate` (letters), `paint.paint` (maps base) |
| `paper_fibre_angle` | `PaintStyle` | `PaperStyle` | ink | `paint.label_plate` (letters), `paint.paint` (maps base) |
| `paper_fibre_cell_px` | `PaintStyle` | `PaperStyle` | ink | `paint.label_plate` (letters), `paint.paint` (maps base) |
| `gran_gamma` | `PaintStyle` | `PaperStyle` | ink | `paint._backing_wash` (letters), `paint.paint` (maps base) |
| `wet_bleed` | `PaintStyle` | `WashStyle` | ink | `paint.paint` (maps base) |
| `wet_bleed_px` | `PaintStyle` | `WashStyle` | ink | `paint.paint` (maps base) |
| `wet_bleed_mix` | `PaintStyle` | `WashStyle` | ink | `paint.paint` (maps base) |
| `wet_rim_drop` | `PaintStyle` | `WashStyle` | ink | `paint.paint` (maps base) |
| `wet_bleed_edge_mult` | `PaintStyle` | `WashStyle` | ink | `paint.paint` (maps base) |
| `flow_rim` | `PaintStyle` | `WashStyle` | ink | `paint.paint` (maps base) |
| `flow_rim_exp` | `PaintStyle` | `WashStyle` | ink | `paint.paint` (maps base) |
| `flow_rim_ref_frac` | `PaintStyle` | `WashStyle` | ink | `paint.paint` (maps base) |
| `flow_rim_frac` | `PaintStyle` | `WashStyle` | ink | `paint.paint` (maps base) |
| `blooms` | `PaintStyle` | `WashStyle` | ink | `paint.paint` (maps base) |
| `bloom_density` | `PaintStyle` | `WashStyle` | ink | `paint.paint.bloom_arg` (maps base) |
| `bloom_max` | `PaintStyle` | `WashStyle` | ink | `paint.paint.bloom_arg` (maps base) |
| `bloom_radius_frac` | `PaintStyle` | `WashStyle` | ink | `paint.paint.bloom_arg` (maps base) |
| `bloom_lift` | `PaintStyle` | `WashStyle` | ink | `paint.paint.bloom_arg` (maps base) |
| `bloom_warp` | `PaintStyle` | `WashStyle` | ink | `paint.paint.bloom_arg` (maps base) |
| `bloom_seed` | `PaintStyle` | `WashStyle` | ink | `paint.paint` (maps base) |
| `bloom_strength` | `PaintStyle` | `WashStyle` | ink | `paint.paint.bloom_arg` (maps base) |
| `sea_variation` | `PaintStyle` | `WashStyle` | ink | `paint.paint` (maps base) |
| `sea_variation_cell_m` | `PaintStyle` | `WashStyle` | ink | `paint.sea_patches` (maps base) |
| `sea_variation_amount` | `PaintStyle` | `WashStyle` | ink | `paint.sea_patches` (maps base) |
| `sea_variation_streak` | `PaintStyle` | `WashStyle` | ink | `paint.sea_patches` (maps base) |
| `sea_variation_elong` | `PaintStyle` | `WashStyle` | ink | `paint.sea_patches` (maps base) |
| `sea_variation_band_m` | `PaintStyle` | `WashStyle` | ink | `paint.sea_patches` (maps base) |
| `sea_variation_seed` | `PaintStyle` | `WashStyle` | ink | `paint.sea_patches` (maps base) |
| `wet_close_px` | `PaintStyle` | `WashStyle` | ink | `paint.paint` (maps base) |
| `silhouette_deform` | `PaintStyle` | `WashStyle` | ink | `paint.paint` (maps base) |
| `silhouette_deform_amount` | `PaintStyle` | `WashStyle` | ink | `paint.paint` (maps base) |
| `silhouette_deform_decay` | `PaintStyle` | `WashStyle` | ink | `paint.paint` (maps base) |
| `silhouette_deform_depth` | `PaintStyle` | `WashStyle` | ink | `paint.paint` (maps base) |
| `silhouette_deform_max_m` | `PaintStyle` | `WashStyle` | ink | `paint.paint` (maps base) |
| `silhouette_deform_min_px` | `PaintStyle` | `WashStyle` | ink | `paint.paint` (maps base) |
| `silhouette_deform_seed` | `PaintStyle` | `WashStyle` | ink | `paint.paint` (maps base) |
| `pigment_separation` | `PaintStyle` | `WashStyle` | ink | `paint.separated` (ink) |
| `separation_pigments` | `PaintStyle` | `WashStyle` | ink | `paint.separated` (ink) |
| `separation_share` | `PaintStyle` | `WashStyle` | ink | `paint.separated` (ink) |
| `separation_gamma` | `PaintStyle` | `WashStyle` | ink | `paint.separated` (ink) |
| `separation_transparency` | `PaintStyle` | `WashStyle` | ink | `paint.separated` (ink) |
| `fluid_pass` | `PaintStyle` | `WashStyle` | ink | `paint.paint` (maps base) |
| `fluid_grid` | `PaintStyle` | `WashStyle` | ink | `paint.fluid_modulate` (ink) |
| `fluid_steps` | `PaintStyle` | `WashStyle` | ink | `paint.fluid_modulate` (ink) |
| `fluid_relax` | `PaintStyle` | `WashStyle` | ink | `paint.fluid_modulate` (ink) |
| `fluid_amount` | `PaintStyle` | `WashStyle` | ink | `paint.fluid_modulate` (ink) |
| `fluid_gran` | `PaintStyle` | `WashStyle` | ink | `paint.fluid_modulate` (ink) |
| `fluid_seed` | `PaintStyle` | `WashStyle` | ink | `paint.fluid_modulate` (ink) |
| `ink_ss` | `PaintStyle` | `BrushStyle` | ink | `paint.InkPad.__init__` (ink) |
| `brush_organic` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `organic_octaves` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `organic_lacunarity` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `organic_cell_mult` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `ink_joins` | `PaintStyle` | `BrushStyle` | ink | `paint.InkPad.__init__` (ink) |
| `ink_join_tol_px` | `PaintStyle` | `BrushStyle` | ink | `paint.InkPad.__init__` (ink) |
| `stroke_smooth` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `stroke_smooth_mult` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `bristle_bandlimit_px` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `bristle_contrast` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `bristle_drift_coherence` | `PaintStyle` | `BrushStyle` | ink | `paint.brush_from_id` (ink) |
| `hillshade_mode` | `GeoOptions` | `BasemapStyle` | maps | `geo._relief_layers` (maps base) |
| `hillshade_levels` | `GeoOptions` | `BasemapStyle` | maps | `geo._relief_layers` (maps base) |
| `hillshade_opacity` | `GeoOptions` | `BasemapStyle` | maps | none in `src/` |
| `hachure_spacing_m` | `GeoOptions` | `BasemapStyle` | maps | `geo._derived` (maps base) |
| `hachure_min_slope` | `GeoOptions` | `BasemapStyle` | maps | `geo._relief_layers` (maps base) |
| `hachure_max_length_m` | `GeoOptions` | `BasemapStyle` | maps | `geo._derived` (maps base) |
| `sea_style` | `GeoOptions` | `BasemapStyle` | maps | `geo._relief_layers` (maps base) |
| `contour_interval` | `GeoOptions` | `BasemapStyle` | maps | `geo._relief_layers` (maps base) |
| `roads` | `GeoOptions` | `BasemapStyle` | maps | `geo._osm_layers` (maps base) |
| `rivers` | `GeoOptions` | `BasemapStyle` | maps | `geo._osm_layers` (maps base) |
| `interaction_m` | `GeoOptions` | `BasemapStyle` | maps | `geo._derived` (maps base) |
| `interaction_run_m` | `GeoOptions` | `BasemapStyle` | maps | `geo._derived` (maps base) |
| `landmarks` | `GeoOptions` | `BasemapStyle` | maps | `geo.basemap` (maps base), `labels.journal_picks` (maps base) |
| `landmark_max` | `GeoOptions` | `BasemapStyle` | maps | `geo._derived` (maps base) |
| `landmark_radius_m` | `GeoOptions` | `BasemapStyle` | maps | `geo._derived` (maps base) |
| `pick_landmarks` | `GeoOptions` | `BasemapStyle` | maps | `geo.basemap` (maps base) |
| `pick_roads` | `GeoOptions` | `BasemapStyle` | maps | `geo._osm_layers` (maps base) |
| `pick_places` | `GeoOptions` | `BasemapStyle` | maps | none in `src/` |
| `generalise` | `GeoOptions` | `BasemapStyle` | maps | `geo._osm_layers` (maps base), `geo._relief_layers` (maps base), `geo._sea_path` (maps base), `geo._soften` (maps base) |
| `cell_m` | `GeoOptions` | `BasemapStyle` | maps | `geo._derived` (maps base) |
| `morph_cells` | `GeoOptions` | `BasemapStyle` | maps | `geo._osm_layers` (maps base), `geo._sea_path` (maps base) |
| `min_area_ha` | `GeoOptions` | `BasemapStyle` | maps | `geo._derived` (maps base) |
| `smooth_passes` | `GeoOptions` | `BasemapStyle` | maps | `geo._osm_layers` (maps base), `geo._sea_path` (maps base), `geo._soften` (maps base) |
| `blob_jitter_m` | `GeoOptions` | `BasemapStyle` | maps | `geo._derived` (maps base) |
| `inset_cells` | `GeoOptions` | `BasemapStyle` | maps | `geo._osm_layers` (maps base), `geo._sea_path` (maps base) |
| `tree_spacing_m` | `GeoOptions` | `BasemapStyle` | maps | `geo._derived` (maps base) |
| `all_variants` | `GeoOptions` | `BasemapStyle` | maps | `geo._relief_layers` (maps base) |

`labels` is read today only by `labels.hand()`, which is deleted; `letter` takes over the
check, so its final reader is maps lettering.

### Digests

`pyntpot.maps.style.Style`, a frozen pydantic model, composes the groups as the fields
`paper, wash, brush, face, nib, hand, card, ribbon, cover, route, route_inks, lettering,
basemap`. It is read from a TOML theme; the packaged `maps/themes/default.toml` is the
resolved default style (the resolved `paint` and `route_ink` values and the effective
basemap options), not the dataclass defaults. A theme naming an unknown key is rejected
at every level: at the top by pydantic, inside a group by checking the table's keys
against the group's dataclass fields.

Each group digest is the first 16 hex digits of
`sha256(json.dumps(asdict(group), sort_keys=True, default=str))`. A combined digest is
the first 16 hex digits of the SHA-256 of its group digests joined, in field order:

| Digest | Groups | Default style |
|---|---|---|
| `digest()` | all thirteen | `25ae6fee082ebff5` |
| `base_digest()` | paper, wash, brush, card, ribbon, cover, route, basemap | `e5a5f1b4b3ca2177` |
| `lettering_digest()` | face, nib, hand, lettering | `d15ae2f30e9ca5ce` |

The three default digests are pinned literals in the unit tests. `route_inks` is in
`digest()` only, so changing an ink moves neither of the other two.

## Consequences

- The table is final. Changing a field's group would move a pinned digest and, for a base
  group, the frozen manifest hash. Code that finds a field it cannot reach takes the
  group as a further parameter; it never moves the field, and stops if neither works.
- No lettering-only field feeds a base plate, so changing one re-letters a map without
  repainting it; changing a route ink repaints and re-letters nothing.
- The groups are not wired in yet: the painter still reads `PaintStyle` and
  `GeoOptions`. A unit test pins every group's field names in order, the
  `CONSUMER_ONLY` names, and every default against its source class.
- The literal copies of the `_port.paint` constants are replaced by imports of the
  moved constants when those constants move into `ink` and `maps`.
- `maps.style_groups` is a pinned adapter of the interim code: it imports `RouteInk` by
  name from `_port.style`, the one `_port` module that may be imported by name.
