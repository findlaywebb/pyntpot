# Style fields

The style is every style group a map is painted, lettered and composed with, as one value: `pyntpot.maps.Style`. A theme is a TOML file with one table for each group, read by `Style.from_toml` and by the command line's `--style`. This page lists every field of every style group.

## Reading the tables

- The section heading is the group's table name in a theme. The line under it names the dataclass and the package it comes from.
- Type is the TOML type: boolean, integer, number, string, array or table.
- Default is the value in the packaged default theme, which `Style.default()` reads. It is the resolved default style, not the dataclass default; the two differ for some fields.
- A table or an array of tables is shown as `table`. Its keys and values are in `src/pyntpot/maps/themes/default.toml`.
- A theme names every group. A key a group does not have is rejected, at the top level, inside a group and inside a route ink, as is a missing group or a value of the wrong type.
- Sizes and widths in `_px` fields are in display pixels unless the description says render pixels. Fields ending `_m` are in metres.

## Which groups feed what

| Digest | Groups |
| --- | --- |
| `base_digest` (the base plates) | `paper`, `wash`, `brush`, `card`, `ribbon`, `cover`, `route`, `basemap` |
| `lettering_digest` (the lettering only) | `face`, `nib`, `hand`, `lettering` |
| `digest` (every group) | all thirteen, `route_inks` included |

A change to a group moves the digests it feeds, and only those plates are painted again. `route_inks` is read only when the route is placed and drawn, so changing a route ink moves `digest` alone.

## `paper`

`PaperStyle`, from `pyntpot.ink`. The paper, its encoder and the compositing of the pigment stack over it. Read by the painter for every plate and by the lettering.

| Field | Type | Default | Sets |
| --- | --- | --- | --- |
| `plate_lossless` | boolean | `true` | Write the plates as lossless WebP. Off writes lossy WebP at the two quality fields. |
| `webp_quality` | integer | `74` | Lossy WebP quality of the wash plate, used when `plate_lossless` is off. |
| `paper_quality` | integer | `80` | Lossy WebP quality of the paper plate, used when `plate_lossless` is off. |
| `grid` | boolean | `false` | Draw the notebook grid on the paper. |
| `grid_spacing_px` | number | `26.0` | Spacing of the notebook grid, in pixels. |
| `grid_opacity` | number | `0.34` | Opacity of the notebook grid. |
| `paper_hex` | string | `"#f3ead6"` | The paper's colour as `#rrggbb`. |
| `paper_tooth` | number | `0.085` | Strength of the paper's texture. |
| `paper_worn` | number | `0.2` | Strength of the worn border. |
| `paper_vignette` | number | `0.05` | Strength of the vignette. |
| `paper_foxing` | number | `0.09` | Strength of the foxing. |
| `sheet_seed` | integer | `11` | Seed of the paper's noise fields, so the same box paints the same paper. |
| `km_glazing` | boolean | `true` | Composite the pigment stack by Kubelka-Munk glazing instead of multiply. |
| `pigment_transparency` | table | table | Table of pigment key to transparency, as `TRANSPARENCY`. See [Pigments](pigments.md). |
| `km_transparency` | number | `0.06` | Transparency of ink and of any pigment the table does not name. |
| `paper_fibre` | boolean | `true` | Mix a second noise, stretched along one axis, into the paper's tooth, and take granulation from the paper's own height. |
| `paper_fibre_mix` | number | `0.35` | How much of the fibre noise is mixed into the tooth. |
| `paper_fibre_stretch` | number | `3.0` | How many times longer than wide a fibre is. |
| `paper_fibre_angle` | number | `0.42` | Angle of the fibre grain, in radians. |
| `paper_fibre_cell_px` | number | `4.2` | Size of the fibre's own cell, in render pixels. |
| `gran_gamma` | number | `1.7` | How sharply granulation follows the paper's pits. Above 1, pigment has to reach a real hollow before it settles. |

## `wash`

`WashStyle`, from `pyntpot.ink`. How a laid wash wets, bleeds, rims, blooms, separates and flows.

| Field | Type | Default | Sets |
| --- | --- | --- | --- |
| `wet_bleed` | boolean | `true` | Share one wet-area field across the land classes, so neighbouring washes bleed into each other and no class boundary inside carries its own rim. |
| `wet_bleed_px` | number | `20.0` | Reach of the wet bleed, in pixels. |
| `wet_bleed_mix` | number | `0.7` | How far the bleed goes inside the wet area. |
| `wet_rim_drop` | number | `1.0` | How much of the rim the bleed takes away inside the wet area. |
| `wet_bleed_edge_mult` | number | `2.2` | How far back from the land's outer edge the wet area starts, as a multiple of the cover's rim width. |
| `flow_rim` | boolean | `true` | Darken the edge of a wash from an outward flow term, so the rim is wider on a larger wash. |
| `flow_rim_exp` | number | `0.125` | Power of the wash's area by which the rim widens. |
| `flow_rim_ref_frac` | number | `0.02` | The reference area, as a share of the card, at which the rim has its base width. |
| `flow_rim_frac` | number | `0.38` | The distance the rim decays over at the reference area, as a share of the rim width. |
| `blooms` | boolean | `true` | Lay blooms: a second front of liquid that pushes pigment out into a crenellated ridge and leaves a lighter centre. |
| `bloom_density` | number | `1.0` | Blooms per wash, against the square root of its area. 0 turns them off. |
| `bloom_max` | integer | `5` | The most blooms in one wash. |
| `bloom_radius_frac` | number | `0.17` | A bloom's radius as a share of the root of the wash's area. |
| `bloom_lift` | number | `0.45` | How much pigment the front lifts out of the centre. |
| `bloom_warp` | number | `0.45` | How far noise warps the front off a circle. |
| `bloom_seed` | integer | `57` | Seed of the blooms. |
| `bloom_strength` | number | `0.65` | How hard a bloom works, as a multiple of `bloom_lift`. |
| `sea_variation` | boolean | `true` | Vary the sea's pigment strength in broad paler and deeper patches. |
| `sea_variation_cell_m` | number | `600.0` | Size of a patch, in metres. |
| `sea_variation_amount` | number | `0.5` | How far density swings across the patches, 0 to 1. |
| `sea_variation_streak` | number | `0.45` | Share of the swing that runs along the coast as streaks. |
| `sea_variation_elong` | number | `6.0` | How many times longer than wide a streak is. |
| `sea_variation_band_m` | number | `420.0` | How far out from the shore a streak still shows, in metres. |
| `sea_variation_seed` | integer | `73` | Seed of the sea variation. |
| `wet_close_px` | number | `5.0` | Width of a gap in the land cover the wet field closes over, in render pixels. 0 leaves the union as it stands. |
| `silhouette_deform` | boolean | `true` | Deform the land cover's outlines by recursive midpoint displacement before they are rasterised. The surveyed coast and the lakes are not deformed. |
| `silhouette_deform_amount` | number | `0.26` | One displacement as a share of the segment it sits on, in the first round. |
| `silhouette_deform_decay` | number | `0.55` | How much of a displacement each round hands its children. |
| `silhouette_deform_depth` | integer | `4` | Rounds of midpoint displacement. Each doubles the ring's point count. |
| `silhouette_deform_max_m` | array | `[16.0, 3.0]` | Ceiling on one displacement: a floor in metres and a multiple of the plate's metres per render pixel. |
| `silhouette_deform_min_px` | number | `1.6` | Segment length below which the recursion stops, in render pixels. |
| `silhouette_deform_seed` | integer | `73` | Seed of the deformation. |
| `pigment_separation` | boolean | `true` | Lay a second, heavier pigment over the classes named in `separation_pigments`, so the two separate as the wash dries. |
| `separation_pigments` | table | table | Table of class to the second pigment's colour over white. A class not named stays one wash. |
| `separation_share` | number | `0.05` | Share of the wash's density the heavy pigment carries. |
| `separation_gamma` | number | `2.2` | How sharply the heavy pigment follows the paper's pits. |
| `separation_transparency` | number | `0.07` | What the heavy pigment shows over black, as a share of over white. |
| `fluid_pass` | boolean | `true` | Run one bounded shallow-water pass over the canvas on a coarse grid, to vary drying and edge darkening around a shape. |
| `fluid_grid` | integer | `4` | How many times smaller than the plate the grid is. |
| `fluid_steps` | integer | `40` | Steps of the pass. |
| `fluid_relax` | integer | `4` | Relaxation iterations inside a step. |
| `fluid_amount` | number | `0.051429` | How far the deposit moves a density, either way. |
| `fluid_gran` | number | `0.6` | How much settling follows the paper's own height. |
| `fluid_seed` | integer | `41` | Seed of the pass. |

## `brush`

`BrushStyle`, from `pyntpot.ink`. Which brush each line class takes, how wide, and how the brush behaves.

| Field | Type | Default | Sets |
| --- | --- | --- | --- |
| `ink_seed` | integer | `91` | Seed of the ink, so the same box paints the same plate. |
| `river_curve` | table | table | Table of watercourse class to four numbers: coefficient and exponent on the box in kilometres, then a floor and a ceiling, in display pixels. |
| `major_river_rel_frac` | number | `0.65` | Share of the box's longest named river a river's run has to reach to count as major. |
| `minor_roads_mppd` | number | `8.0` | Metres per display pixel above which lanes and tracks are dropped. |
| `blotch_m` | array | `[190.0, 26.0]` | The wood's blotch size, in metres: a floor and a multiple of the plate's metres per display pixel. |
| `dab_spacing_m` | array | `[620.0, 95.0]` | The wood's dab spacing, in metres: a floor and a multiple. |
| `gran_m` | array | `[70.0, 9.0]` | The granulation size, in metres: a floor and a multiple. |
| `river_mult` | number | `1.0` | Multiplier on every painted width. |
| `brushes` | table | table | Table of line class to brush id. See [Brushes](brushes.md). |
| `brush_width_px` | table | table | Table of class to painted width in display pixels, for the classes not on the river curve. |
| `coast_width_frac` | number | `0.8` | The coast's width as a share of a medium watercourse's. |
| `brush_jitter_px` | number | `0.55` | How far a bristle wanders sideways, in display pixels. |
| `brush_press_cell_px` | number | `110.0` | Length of one pressure cycle, in display pixels. |
| `brush_wobble_px` | number | `0.32` | Slow wander of the whole line, in display pixels. |
| `brush_step` | number | `0.4` | Spacing of the stamps along the path. |
| `brush_profile_px` | number | `0.55` | Spacing the tip's profile is sampled at, in render pixels. |
| `pen_load_px_frac` | number | `0.85` | How fast the set-down ink runs out, as a multiple of the brush width. |
| `pen_pool_radius_frac` | number | `0.5` | Radius of the blot a nib leaves where it touches down. |
| `pen_pool_gain` | number | `1.9` | Density of that blot. |
| `brush_overrides` | table | table | Table of class to a table of values that replace the shared geometry and a row's treatment for that class. |
| `ink_starve` | boolean | `true` | Spend a per-bristle ink load along a brush stroke, so a long stroke breaks into skips. |
| `ink_reservoir` | number | `150.0` | How far a full load carries, as a multiple of the brush's width. |
| `ink_res_floor` | number | `0.38` | What is left in a bristle when it is nominally empty. |
| `ink_dip_mult` | number | `3.2` | Distance between reloads, in reservoir lengths. |
| `ink_knee` | number | `0.62` | How much ink survives an empty brush before the paper gate is asked. |
| `dry_directional` | boolean | `true` | Stretch a dry brush's break texture along the stroke. |
| `dry_dir_elong` | number | `4.5` | How many times longer than wide a break is. |
| `dry_dir_cell_px` | number | `0.9` | Width of one break across the mark, in display pixels. |
| `dry_dir_gain` | number | `1.0` | How hard the directional tooth is, against the paper's own contrast. |
| `dry_dir_mix` | number | `0.8` | How far the gate moves from the paper's tooth toward the directional texture. |
| `pen_starve` | boolean | `true` | Let a nib run down: its line thins and lightens over a long run and returns at the reload. |
| `pen_reservoir` | number | `420.0` | A nib's run, as a multiple of its width. |
| `pen_thin` | number | `0.26` | How much of its width and ink an empty nib has lost. |
| `ink_ss` | integer | `3` | Paint the ink at this multiple of the plate's grid and reduce it back. 1 is the plate's own grid. |
| `brush_organic` | boolean | `true` | Draw drift and pressure from a fractal noise along the stroke instead of a sine, so a long mark does not repeat. |
| `organic_octaves` | integer | `4` | Octaves of that noise. |
| `organic_lacunarity` | number | `2.17` | Ratio between its octaves. |
| `organic_cell_mult` | number | `0.5` | Coarsest feature, as a share of the sine's wavelength. |
| `ink_joins` | boolean | `true` | Join polylines that meet end to end before stamping. |
| `ink_join_tol_px` | number | `2.5` | How close two ends have to be to count as one mark, in render pixels. |
| `stroke_smooth` | boolean | `true` | Round a corner before stamping. |
| `stroke_smooth_mult` | number | `0.7` | The corner radius, as a multiple of the brush's width. |
| `bristle_bandlimit_px` | number | `0.9` | Smoothing of the tip's weights across the tip, as a sigma in render pixels. 0 leaves the tip unsmoothed. |
| `bristle_contrast` | number | `1.0` | Multiplier on the variation of the bristle weights about their mean. |
| `bristle_drift_coherence` | number | `0.25` | How much of its sideways drift a bristle shares with its neighbours, as a share of the tip's width. 0 draws each independently. |

## `face`

`FaceStyle`, from `pyntpot.letters`. The face the hand opens and how a glyph becomes a pen path.

| Field | Type | Default | Sets |
| --- | --- | --- | --- |
| `label_route` | string | `"centreline"` | How a glyph becomes a pen path: `centreline` thins the face's outline to a written skeleton, `outline` draws round the contour. Neither falls back to the other. |
| `label_face` | string | `""` | Path of the `.ttf` to open. Empty opens the vendored face. |

## `nib`

`NibStyle`, from `pyntpot.letters`. The nib, its inks, widths and angle, and the backing wash under a name. Sizes and widths are in display pixels; the angle is in degrees.

| Field | Type | Default | Sets |
| --- | --- | --- | --- |
| `label_size_px` | number | `20.0` | Size the hand is written at, in display pixels. |
| `label_ink` | string | `"#241c14"` | Ink the lettering is written in, as `#rrggbb`. |
| `label_brush` | string | `"MAJ6-e"` | Brush id of the nib the lettering is written with. |
| `label_pen_width_px` | number | `1.05` | The nib's width, in display pixels. |
| `label_outline_width_frac` | number | `0.62` | Width of the finer nib the outline route writes with, as a share of `label_pen_width_px`. |
| `label_leader_brush` | string | `"MAJ6-e"` | Brush id for every mark that is not a glyph: a leader, a span line, a tick, an underline, a pin. |
| `label_leader_width_px` | number | `0.85` | Width of those marks, in display pixels. |
| `label_pen_angle_deg` | number | `-38.0` | The pen's angle in degrees from the page's horizontal, y down, so a negative angle turns anticlockwise on the page. |
| `label_pen_thin` | number | `0.52` | How much of its width the pen takes off a stroke drawn along its angle. |
| `label_wash` | boolean | `true` | Lay a paper-coloured backing wash under a name. It is absent where the ground is already pale. |
| `label_wash_alpha` | number | `0.5` | Opacity of the backing wash. |
| `label_wash_dark_floor` | number | `0.22` | Darkness of the ground below which no backing wash is laid. |
| `label_wash_spread` | number | `0.75` | How far the backing wash reaches round the ink, as a multiple of the label size. |
| `label_route_ink` | string | `"#c22050"` | Ink of a name in the route's own colour. |
| `label_water_ink` | string | `"#4a7691"` | Ink of a name written beside water. |
| `label_in_water_ink` | string | `"#f8f4e9"` | Ink of a name written on the water, reversed out in the paper's cream. |

## `hand`

`HandStyle`, from `pyntpot.letters`. The seed the hand draws every label's randomness from.

| Field | Type | Default | Sets |
| --- | --- | --- | --- |
| `label_seed` | integer | `17` | Seed every label's randomness starts from. One seed and one text write the same marks. |

## `card`

`CardStyle`, from `pyntpot.maps`. The card's display size, its supersampling and the dark grid's size.

| Field | Type | Default | Sets |
| --- | --- | --- | --- |
| `display_px` | integer | `900` | Display width of the card in pixels; the height follows its aspect. Below 900 the lanes and tracks are not drawn. |
| `supersample` | integer | `2` | The plates are painted at this multiple of the display size. |
| `dark_grid` | array | `[80, 60]` | Cells across and down of the dark grid the label placer scores against. |

## `ribbon`

`RibbonStyle`, from `pyntpot.maps`. The trimmed extent of the painted ground, and the card around it.

| Field | Type | Default | Sets |
| --- | --- | --- | --- |
| `ribbon_k` | number | `7.15` | Coefficient on the root of the box in the ribbon radius, `ribbon_k * sqrt(box) + ribbon_c`, in metres. |
| `ribbon_c` | number | `158.0` | Constant in that radius, in metres. |
| `ribbon_mult` | number | `1.0` | Multiplier on the fitted radius. 1.0 leaves it unchanged. |
| `ribbon_min_m` | number | `420.0` | Least ribbon radius, in metres. |
| `ribbon_max_m` | number | `1250.0` | Greatest ribbon radius, in metres. |
| `card_grow_mult` | number | `1.55` | The card is framed as though the ribbon were this many times wider, so the same box is composed whatever the multiplier. |
| `card_pad_frac` | number | `0.09` | Padding of the card, as a share of its longer side. The greater of this and `card_pad_ribbon_frac` is used. |
| `card_pad_ribbon_frac` | number | `0.55` | Padding of the card, as a share of the fitted ribbon radius. |
| `card_aspect_min` | number | `1.12` | Least aspect ratio of the card. |
| `card_aspect_max` | number | `1.62` | Greatest aspect ratio of the card. |
| `ribbon_fill` | boolean | `true` | Fill what the outside cannot reach, so the inside of a loop is painted. |
| `ribbon_tear_frac` | number | `0.004` | Torn edge, as a share of the render width. |
| `ribbon_tear_floor_px` | number | `5.0` | Least torn edge, in pixels. |
| `rim_strength` | number | `0.4` | Strength of the pooled edge just inside the tear. |
| `coast_hard_mask` | boolean | `true` | Treat the coast as a hard edge that nothing the ribbon carries crosses. |
| `sea_to_edge` | boolean | `true` | Paint the sea to the edge of the card without trimming it. |

## `cover`

`CoverStyle`, from `pyntpot.maps`. Land cover and the wood: the classes, their pigments, and the wood's texture and dabs.

| Field | Type | Default | Sets |
| --- | --- | --- | --- |
| `dither_seed` | integer | `23` | Seed of the wood dabs and the dither. |
| `land_cover` | boolean | `true` | Paint the cover classes. Off paints the pale single wash. |
| `relief` | boolean | `true` | Paint the relief from the elevation grid. |
| `cover_cfg` | table | table | Table of cover class to two numbers: how dark a wash of the class goes and how hard its edge pools. |
| `pigments` | table | table | Table of pigment key to the colour a full-strength wash transmits. See [Pigments](pigments.md). |
| `pale_base` | number | `0.5` | Density of the pale single wash. |
| `pale_pool` | number | `0.16` | How hard the pale wash's edge pools. |
| `wood_texture` | number | `0.75` | Slider for the wood's texture, a cross fade over three printed scales. |
| `wood_dabs` | number | `0.78` | Slider for the wood's dabs, a cross fade over three printed spacings. |
| `wood_tex_scales` | array | `[2.1, 1.0, 0.45]` | The three printed scales of the wood's texture. |
| `wood_tex_strengths` | array | `[0.3, 0.4, 0.48]` | The strength of each printed scale. |
| `dab_spacings` | array | `[1.7, 1.0, 0.6]` | The three printed spacings of the wood's dabs. |
| `dab_strengths` | array | `[0.34, 0.36, 0.38]` | The strength of each printed spacing. |

## `route`

`RouteStyle`, from `pyntpot.maps`. The route's own painted plate: whether it is drawn, with which nib, how wide. The plate is tinted at compose time by the route ink.

| Field | Type | Default | Sets |
| --- | --- | --- | --- |
| `route_pen` | boolean | `true` | Paint the route's own plate. |
| `route_pen_brush` | string | `"MAJ6-e"` | Brush id of the nib the route plate is painted with. |
| `route_pen_width_px` | number | `3.0` | Width of the route plate's stroke, in display pixels. |

## `route_inks`

`RouteInks`, from `pyntpot.maps`. One route ink for each sport. It is read only when the route is placed and drawn, so changing an ink paints no plate again. Each of the four is a table with the keys of a route ink, listed after this group.

| Field | Type | Default | Sets |
| --- | --- | --- | --- |
| `run` | table | table | The ink a run is drawn in: a table with the keys of a route ink. |
| `ride` | table | table | The ink a ride is drawn in. `route_ink()` reads this one. |
| `swim` | table | table | The ink a swim is drawn in. |
| `other` | table | table | The ink any other sport is drawn in. |

## `route_inks.<sport>`

`RouteInk`, from `pyntpot.maps`. One sport's route treatment. These keys sit in each of the tables `route_inks.run`, `route_inks.ride`, `route_inks.swim` and `route_inks.other`.

| Field | Type | Default | Sets |
| --- | --- | --- | --- |
| `style` | string | `"solid"` | The route's treatment, such as `solid` or `dotted`. |
| `px` | number | `5.4` | Width in display pixels. It also sets how far apart the strands of a doubled-back route are drawn. |
| `colour` | string | `"#c22050"` | Colour as `#rrggbb`. |
| `effect` | table | table | Table of the treatment's keys: casing, glow, shadow, blend and adaptive percentage. |

## `lettering`

`LetteringPolicy`, from `pyntpot.maps`. Which names a map letters, and how many.

| Field | Type | Default | Sets |
| --- | --- | --- | --- |
| `label_max` | integer | `3` | The most landmark labels. |
| `labels` | boolean | `true` | Letter the map at all. Off opens no hand and draws no label plate. |
| `label_ground` | boolean | `true` | Letter the settlements, watercourses and roads the box holds. |
| `label_geom_tol_px` | number | `8.0` | How far a named road or watercourse is simplified before a label is set along it, in display pixels. |
| `home_glyph` | boolean | `true` | Letter the user's marked places, each under its own name. |

## `basemap`

`BasemapStyle`, from `pyntpot.maps`. What the basemap draws, and how much of it.

| Field | Type | Default | Sets |
| --- | --- | --- | --- |
| `hillshade_mode` | string | `"off"` | How relief is drawn: `bands`, `raster`, `contours`, `hachures` or `off`. |
| `hillshade_levels` | integer | `5` | Number of bands in `bands` mode. |
| `hillshade_opacity` | number | `0.5` | Has no reader; kept for the upstream consumer. |
| `hachure_spacing_m` | number | `75.0` | Seed spacing of hachures, in metres, stated for a 4 km box and scaled up. |
| `hachure_min_slope` | number | `0.035` | Gradient below which no hachure is drawn. |
| `hachure_max_length_m` | number | `90.0` | Longest hachure stroke, in metres, stated for a 4 km box. |
| `sea_style` | string | `"fill"` | How the sea is drawn: `fill` or `waves`. |
| `contour_interval` | number | `50.0` | Contour interval in metres, used when the mode is `contours`. |
| `roads` | string | `"key"` | Which roads are drawn: `all`, `key` (major plus interacted) or `major`. |
| `rivers` | string | `"key"` | Which watercourses are drawn: `all`, `key` (rivers plus interacted streams) or `rivers`. |
| `interaction_m` | number | `60.0` | Metres within which a minor road or a stream counts as touched by the track. |
| `interaction_run_m` | number | `100.0` | Metres of that contact needed before it counts, unless the track crosses. |
| `landmarks` | string | `"all"` | How landmarks are chosen: `heuristic`, `all` or `payload`. |
| `landmark_max` | integer | `40` | The most landmarks. |
| `landmark_radius_m` | number | `300.0` | Radius, in metres, the landmark heuristic works over, scaled to the box. |
| `pick_landmarks` | array | `[]` | Names the payload picked: replaces the landmark heuristic when given. |
| `pick_roads` | array | `[]` | Names of minor roads to keep. |
| `pick_places` | array | `[]` | Has no reader; kept for the upstream consumer. |
| `generalise` | boolean | `false` | Rasterise, close, open, declutter and trace the wood, the parkland and the sea back as a few smooth shapes. Off draws the raw outlines. |
| `cell_m` | number | `60.0` | Metres per cell of the working grid, stated for a 4 km box and scaled up. |
| `morph_cells` | integer | `2` | Radius of the close and open, in cells. |
| `min_area_ha` | number | `4.0` | Hectares below which a blob, or a hole in one, is dropped. |
| `smooth_passes` | integer | `3` | Chaikin passes on a traced outline, and on a road or a river. |
| `blob_jitter_m` | number | `22.0` | Metres of loose-edge wobble on a wash. 0 draws the measured edge. |
| `inset_cells` | integer | `2` | Cells pulled in for the second, darker pass of pigment inside a wash. |
| `tree_spacing_m` | number | `450.0` | Metres between tree glyphs inside a wood. 0 scatters none. |
| `all_variants` | boolean | `false` | Build every relief variant rather than the one the mode asks for. |

The defaults shown for `route_inks.<sport>` are the `ride` ink's. The other three differ: `run`, `swim` and `other` take `style = "dotted"` and `px = 4.8`, and `ride` takes `style = "solid"` and `px = 5.4`; all four take `colour = "#c22050"`.

## Painter fields in no group

These painter fields are read by no module. They belong to no group and a theme may not name them. They are kept for the upstream consumer.

- `cover_order`
- `label_font`
- `label_pin_colour`
- `label_glow_colour`

## Fields with no reader

`hillshade_opacity` and `pick_places`, in `basemap`, are fields of the group that no module reads. They are kept for the upstream consumer.

## Not style fields

The basemap's clip margin is derived from the card for each render and is not a style field.
