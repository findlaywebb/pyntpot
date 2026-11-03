# Four public functions shadow their own modules, so module paths in the docs fail

GitHub issue: [#164](https://github.com/findlaywebb/pyntpot/issues/164)

Area: maps and ink (package exports).

`src/pyntpot/ink/__init__.py` imports the functions `stamp` and `wash` from the modules
`pyntpot.ink.stamp` and `pyntpot.ink.wash`; `src/pyntpot/maps/__init__.py` imports
`compose` from `pyntpot.maps.pipeline` and `vector_layers` from
`pyntpot.maps.vector_layers`, and a module `pyntpot.maps.compose` also exists. Binding the
function on the package replaces the submodule attribute, so:

- `pyntpot.maps.compose` is `pipeline.compose`, a function, and
  `pyntpot.maps.compose.painted_map` raises `AttributeError`.
- `import pyntpot.ink.wash as w` binds the function, so `w.WashOptions` raises
  `AttributeError`. The same holds for `stamp` and `vector_layers`.

`from pyntpot.maps.compose import painted_map` still works, because it goes through
`sys.modules`; only the dotted attribute path fails.

`docs/explanation/references.md` gives the dotted paths as "Implemented in" pointers:
`pyntpot.maps.compose.painted_map` (twice), `pyntpot.maps.compose.route` and
`pyntpot.maps.compose.paste_labels`. A reader who follows one in a REPL gets the error.
The API reference shows the other side: `docs/reference/ink.md` has to name
`pyntpot.ink.stamp.stamp` and `pyntpot.ink.wash.wash`, because griffe resolves the short
names to the modules, so the rendered headings show module paths.

Possible fix: rename the colliding modules (for example `ink/stamping.py`,
`ink/washing.py`, `maps/compose_steps.py`, `maps/vector_layer_build.py`) so no exported
name shares a name with a sibling module, update the references, and add an architecture
test that fails on such a collision.
