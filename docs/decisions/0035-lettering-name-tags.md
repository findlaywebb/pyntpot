# 0035 — Lettering name tags

Status: accepted

Amends 0005 (style groups): `BasemapStyle` gains one field.

## Context

The map read a feature's name from OpenStreetMap's `name` tag only. In Wales that tag often
holds the English name, with the Welsh one in `name:cy`, so a card of Y Fenni lettered
"Abergavenny". The maintainer's rule "Welsh names for Welsh places" (2026-10-23) covers the
repo's own strings, and the cards followed the data until a style could choose the tags.

## Decision

- **The field.** `BasemapStyle` gains `name_tags: tuple[str, ...] = ("name",)`. Every name
  `pyntpot.maps.osm_elements` reads, for a place, a landmark, a road, a river or a coastline,
  is the first of those tags the element carries with a value, else empty, as before. One
  helper, `_name(tags, name_tags)`, is used at every site.
- **Digests.** `pyntpot.maps.style` gains `DIGEST_OMITS_AT_DEFAULT = ("name_tags",)`. A group
  digest leaves out the fields it names while they equal their default, so the default
  style's three digests, the manifest hash and every golden stay byte-identical. A style that
  names other tags moves `base_digest` and `digest`, because the names are drawn on the base
  plates' data, and not `lettering_digest`.
- **The candidate export is unchanged.** `candidates/places.py` and `candidates/roads.py`
  keep reading `name`; the field is scoped to `osm_elements`.
- **Reached through a theme file.** An OSM tag key is data, not a token (0026), and
  `BasemapStyle` is in no `__all__`, so the public API does not change. The default theme
  states `name_tags = ["name"]`, so it stays a full theme. `examples/themes/y-fenni.toml`
  is the default theme with `name_tags = ["name:cy", "name"]`.

## Consequences

- A card can letter Welsh names for Welsh places, or another language's names elsewhere,
  with one theme line.
- The Y Fenni place card pins the Welsh labels under that theme.
- A later field that should not move the default digests joins `DIGEST_OMITS_AT_DEFAULT`.
