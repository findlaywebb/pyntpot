# Boundaries

One page: who owns what, who may import whom. The machine-readable version is
`[tool.importlinter]` in `pyproject.toml` plus `tests/architecture/`. **Those checks are
the contract**; this page is the orientation read. Changing a boundary is an ADR
(`docs/decisions/`).

The layering is `maps -> letters -> ink`: dependencies point towards `ink`. import-linter
enforces it as a layers contract, and a second contract keeps `httpx`, `pydantic` and
`ruamel.yaml` out of `ink` and `letters` (ADRs 0010, 0069).

| Layer | Owns | May import |
|---|---|---|
| `pyntpot.ink` | The painting engine: sheet, noise, brush, stamp, wash, pigment, raster I/O | nothing outside `ink` |
| `pyntpot.letters` | Hand lettering: the font, tracing glyphs to strokes, the hand | `ink` |
| `pyntpot.maps` | Route maps: providers, cache, projection, layers, plates, placement, compose, style, CLI | `letters`, `ink` |

Hard rules the checks enforce:

- `pyntpot` imports no `matplotlib`, `pandas`, `jinja2` or `yaml` (PyYAML).
- `ink` and `letters` import neither `httpx`, `pydantic` nor `ruamel.yaml`; `maps` reads
  theme files with `ruamel.yaml` (ADR 0069).
- No `maps/theme_*` module but `theme_schema` imports `pyntpot.maps.style` or the
  `pyntpot.maps` package: `style.py` imports the loader, so the loader must not import
  `style.py` (enforced by `tests/architecture/test_theme_imports.py`).
- The package never touches `os.environ` / `os.getenv`: config is injected.
- No clock reads, no module-level randomness, no `uuid` imports.
- No `print()` anywhere in `src/`; logging only.
- Soft file budget of 400 lines. A spike signals a god module; split it.
- Public data only (D16). Every coordinate pair in `src/`, `tests/`, `docs/`, `examples/`
  and the root docs lies inside a fixture's box (`tests/architecture/test_coordinates.py`).

Public surface discipline: each package `__init__.py` exports only what is public, and
its module docstring states purpose, non-goals and invariants. Keep both current; they are
the first thing an agent reads. Every name a public signature reaches is public (ADR 0068,
`tests/architecture/test_public_signatures.py`).
