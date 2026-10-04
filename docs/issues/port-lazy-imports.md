# Lazy imports left between the port modules

The polyline and chain helpers now live in `pyntpot.ink.polyline`,
`pyntpot.ink.curves` and `pyntpot.ink.chains`, and the port modules import them
at module level. That removed the lazy `labels -> geo` import that borrowed
`simplify`, the `labels -> paint` ones that borrowed `chain_lines` and
`deform_line`, and the `paint -> geo` borrow of `simplify`.

These function-level imports between `_port` modules remain. Each is a cycle
the split has to break by moving the borrowed name, not by hoisting the import.

| Importer | Imports | Borrows |
|---|---|---|
| `labels.Hand.__init__` | `_port.outlinefont` | `load` |
| `labels.plate_key` | `_port.paint` | `labels_hash` |
| `labels.draw_plate` | `_port.paint` | `label_plate` (inside `try ... except ImportError`) |
| `outlinefont._centrelines` | `_port.paint` | `edt` |
| `paint.label_geom` | `_port.geo` | `journal_layers`, `parse_path` |

One function-level import reaches outside `_port`: `mapcard.compose` imports
`pyntpot.maps.card.Card`, which the import rule requires to stay inside the
function.
