# Docs image feedback: causes and smallest fixes (investigation agent, saved by orchestrator)

Checkout wt-crit @ bf0b726; PNGs in investigate/out/.

1. Oxford blob = River Cherwell rel 1046961 (14 inner rings, 41.1 of 49.2 ha). osm_elements._area
   (276-279) drops inner rings; rivers.channel measures to the envelope -> 160-190 px "major".
   Fix (src): keep lake_holes in Harvest, rings_path(lakes, holes) at osm.py:178 (nonzero fill
   already in ink/raster.py:128; check ring winding through layers.py:295-298 clip/simplify);
   river width to nearest bank incl. holes. Prototype q1_oxford_water_holes_banks.png. Moves
   Oxford golden. "Holywell Mill Stream" also runs off the right edge.
2. Oxford roads: query overpass.py:59-62 (no footway/path/pedestrian/cycleway/living_street);
   keep/drop _road osm_elements.py:223-226; minor painted when m/px < 8 (painter/pen.py:79-96).
   roads="all" works by theme but brings 1203 service ways. Smallest src: basemap field listing
   minor classes "all" keeps. Prototype q2_oxford_roads_streets_only.png. Footways need query
   change + re-record.
3. Keswick kink: leader of "Lake Road Chapel" crosses the flat "Keswick" box (K leg+underline).
   _place_flat (placement_flat.py:150-180) does not cost leader-vs-placed-box; _uncross_leaders
   (placement.py:332) only leader-vs-leader. Fix: leader-crosses-box cost ~ROAD_CROSS_COST + test.
   Also: tutorials/route-map letters Greta as "Geta" (not investigated). NOTE: reference critique
   separately found the skeleton doubling k stems / breaking K (letters/trace.py) - both real.
4. Pixelation: examples paint NibSurface at scale 1.0 (lettering.py:79, word.py:115). ink_ss only
   supersamples the pad. Scale 2 + downsize fixes (0.35->0.77 s). Cards: supersample 3 is theme
   value, 39->84 s, all goldens move.
5. Route: route_ink() reads only route_inks.ride; compose.route (55-90) reads colour/px/style;
   "pen" tints painted plate; else opaque Pillow line (digital look); effect + dotted unread;
   "start" uses nib.label_route_ink. Candidates A solid #7b2335 4.4px; B pen MAJ1-e #7b2335 4px;
   C pen MAJ3-e #6e2a2f 3.4px. Src needed: opacity/multiply from effect; pen plate along
   separated strands (doubled legs merge in pen mode).
6. Landscape: theme fields ribbon_mult 2.2, card_grow_mult 1.9, card_pad_frac 0.06, relief
   #a8987c t0.12 fill frame (q6_keswick_landscape_900_display.png). Relief strength hard-coded
   painter/paper.relief_density 0.30*(1-shade) cap 0.40 (src). hillshade/contours/hachures only
   reach vector basemap (relief_layers.py:101). Data limit: track box +1500 m features, +2600 m
   landcover; avoid rivers="all".
7. Skye: fetch = track box + MARGIN_M 1500 / LANDCOVER_MARGIN_M 2600 (cache.py:54-58, ensure
   240-251); no public way to widen. Options: (a) coastal route, no src; (b) margin/frame option
   on fetch/Cache.ensure, ADR, cache key; (c) overview scale. Whole Skye counts (a box round
   Skye, Raasay and the facing mainland): coastline 96,809 nodes ~7.5 MB raw; landcover 293,641 ~23 MB;
   feature core 615,948 ~48 MB. Whole island = (b) + coastline-only outer fetch (simplified).
