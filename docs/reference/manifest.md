# The manifest

The manifest is the sidecar record of one map's painted plates, written as `plates.json` in the plates directory (see [Cache layout](cache-layout.md)). It is `pyntpot.maps.plates.Manifest`. The painter writes it; the lettering and the compose step read it. It does not decide whether it is current.

## Format

One line of compact JSON. The keys are written in the order below. `Manifest.from_json` reads every key and raises `KeyError` for a missing one, except `mpp_display`, which reads as 1.0 when absent. `to_json` of a manifest read with `from_json` gives back the same bytes.

## Keys

| Key | Type | Holds |
| --- | --- | --- |
| `hash` | string | The base hash of the card and layers the plates were painted from. |
| `files` | object | The file name of each plate, by plate name: `paper`, `wash` and, when the route pen is on, `pen`. |
| `sizes` | object | The bytes written for each plate, by plate name. |
| `bytes` | integer | The bytes written for every plate together. |
| `card` | array of four numbers | The card's box in card metres, as x0, y0, x1, y1. |
| `display` | array of two integers | The display pixel grid, width and height. |
| `render` | array of two integers | The render pixel grid the plates were painted on, width and height. |
| `mpp` | number | Metres per render pixel. |
| `mpp_display` | number | Metres per display pixel. |
| `ribbon_m` | integer | The ribbon radius, in card metres. |
| `span_m` | integer | The longer side of the track's own box, in whole metres. |
| `wet_px` | object | The painted width floor of each watercourse class, in display pixels, by class: `major`, `medium` and `minor`. |
| `gran_px` | number | The paper granulation's cell size, in render pixels. |
| `dark` | object | The dark grid: how dark the painted map is. Its keys are below. |
| `wood_px` | integer | Render pixels painted as wood. |
| `water_px` | integer | Render pixels painted as water. |

The keys `card`, `display`, `render`, `mpp` and `mpp_display` are the card's frame, read back with `Card.from_manifest`.

## Keys of `dark`

| Key | Type | Holds |
| --- | --- | --- |
| `w` | integer | Cells across. |
| `h` | integer | Cells down. |
| `v` | array of arrays of numbers | The darkness of each cell from 0, bare paper, to 1, row by row from the top left: `h` rows of `w` cells. |

## Not in the manifest

The route in display pixels and its strands are not recorded. Plates built from a manifest alone carry them empty. The manifest carries no lettering input; the places, candidates and named lines a label is set along are read from the basemap.
