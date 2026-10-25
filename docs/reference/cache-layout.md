# Cache layout

The fetch cache is one directory the caller names, as `pyntpot.maps.Cache`. It holds the provider payloads for a track's bounding box under one key, and the plates painted from them. This page lists every file it holds, how the key is made and what the cache does not do.

## Tree

```text
<cache>/
  overpass-<key>.json
  landcover-<key>.json
  elevation-<key>.json
  plates/
    <key>/
      paper.webp
      wash.webp
      pen.webp
      plates.json
      labels-centreline.webp
      labels-centreline.json
      labels-outline.webp
      labels-outline.json
```

## Payload files

Each is written to its path as soon as its provider call returns.

| File | Holds | Ground covered | Written by |
| --- | --- | --- | --- |
| `overpass-<key>.json` | The feature payload. | The track's box plus `margin_m` (1500 m by default). | The features provider. |
| `landcover-<key>.json` | The land cover payload. | The track's box plus `landcover_margin_m` (2600 m by default). | The features provider. |
| `elevation-<key>.json` | The elevation grid, 80 samples a side. | The track's box plus `margin_m` (1500 m by default). | The elevation provider. |

`Cache.ensure` fetches in that order and calls a provider only for a file that is missing, unless forced. A failure part-way leaves every earlier payload on disk.

## The key

The key is the first 16 hex characters of the SHA-256 of the canonical JSON of these inputs.

| Input | Value |
| --- | --- |
| `box` | The track's bounding box with the margin, each number rounded to six decimal places. |
| `margin_m` | The margin in metres, 1500 by default. |
| `landcover_margin_m` | The land cover margin in metres. Left out of the JSON while it is 2600, its default, so the default key is unchanged. |
| `features` | The features provider's id. |
| `elevation` | The elevation provider's id. |

The key never comes from a caller's own id. Two tracks over the same ground with the same providers share their payloads; a different provider or margin fetches afresh. Both margins are one `FetchMargins`, which the `Cache` is made with: each is from 0 to 20 000 m, and the land cover margin is at least `margin_m`.

## The plates directory

`plates/<key>` holds the plates painted for that key, written by `paint`.

| File | Holds |
| --- | --- |
| `paper.webp` | The paper plate. |
| `wash.webp` | The wash plate: every pigment laid over the paper. |
| `pen.webp` | The route's alpha plate, tinted at compose time. Written only when the style's `route_pen` is on. |
| `plates.json` | The manifest. See [The manifest](manifest.md). |

## The label plate

The lettering stage writes a label plate beside the base plates when there is something to letter and a hand to letter it with. The file name carries the route the hand writes, `centreline` or `outline`.

| File | Holds |
| --- | --- |
| `labels-centreline.webp`, `labels-outline.webp` | The label plate for that route. |
| `labels-centreline.json`, `labels-outline.json` | A sidecar with the keys below. |

| Sidecar key | Holds |
| --- | --- |
| `key` | The label plate's key: the first 16 hex characters of the SHA-256 of the canonical JSON of the base hash, the style's lettering digest and every mark, with each float rounded to three decimals. |
| `face` | The name of the face the hand opened. |
| `route` | The route the hand wrote, `centreline` or `outline`. |

A plate whose sidecar `key` does not match is lettered again, never reused.

## Hashes

- The base hash in the manifest is the first 16 hex characters of the SHA-256 of the basemap's canonical text, a hyphen and the style's base digest.
- A style digest is the first 16 hex digits of the SHA-256 of its groups' digests. Changing a route ink moves the full digest only, so no plate is painted again.

## What the cache does not do

- It does not parse, validate or expire payloads.
- It does not lock the directory against a second process.
- It fetches only through the providers it is handed.
- `Cache.load_plates` reads a manifest and checks that its plates are on disk; it does not compare hashes. A manifest that cannot be read, or that names a missing plate, reads as no plates.
