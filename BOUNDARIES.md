# Boundaries

One page: who owns what, who may import whom. The machine-readable version is
`[tool.importlinter]` in `pyproject.toml` plus `tests/architecture/`. **Those checks are
the contract**; this page is the orientation read. Changing a boundary is an ADR
(`docs/decisions/`).

The layering is `maps -> letters -> ink`: dependencies point towards `ink`. import-linter
enforces it as a layers contract, and a second contract keeps `httpx` and `pydantic` out of
`ink` and `letters` (ADR 0010).

| Layer | Owns | May import |
|---|---|---|
| `pyntpot.ink` | The painting engine: sheet, noise, brush, stamp, wash, pigment, raster I/O | nothing outside `ink` |
| `pyntpot.letters` | Hand lettering: the font, tracing glyphs to strokes, the hand | `ink` |
| `pyntpot.maps` | Route maps: providers, cache, projection, layers, plates, placement, compose, style, CLI | `letters`, `ink` |

Hard rules the checks enforce:

- `pyntpot` imports no `matplotlib`, `pandas`, `jinja2` or `yaml`.
- `ink` and `letters` import neither `httpx` nor `pydantic`.
- The package never touches `os.environ` / `os.getenv`: config is injected.
- No clock reads, no module-level randomness, no `uuid` imports. The exemptions
  directory (`tests/architecture/exemptions/`) is empty.
- No `print()` anywhere in `src/`; logging only.
- Soft file budget of 400 lines. A spike signals a god module; split it.
- No personal content: banned terms and the coordinate allowlist apply to `src/`,
  `tests/`, `docs/` and the root docs.

Public surface discipline: each package `__init__.py` exports only what is public, and
its module docstring states purpose, non-goals and invariants. Keep both current; they are
the first thing an agent reads.
