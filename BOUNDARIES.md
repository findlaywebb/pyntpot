# Boundaries

One page: who owns what, who may import whom. The machine-readable version is
`[tool.importlinter]` in `pyproject.toml` plus `tests/architecture/`. **Those checks are
the contract**; this page is the orientation read. Changing a boundary is an ADR
(`docs/decisions/`).

The target layering is `maps -> letters -> ink`: dependencies point towards `ink`. The
layers contract is added when the port is split. Until then everything lives in the
private `pyntpot._port` subpackage, which has no layer contract.

| Layer | Owns | May import |
|---|---|---|
| `pyntpot.ink` | The painting engine: sheet, noise, brush, stamp, wash, pigment, raster I/O | nothing outside `ink` |
| `pyntpot.letters` | Hand lettering: the font, tracing glyphs to strokes, the hand | `ink` |
| `pyntpot.maps` | Route maps: providers, cache, projection, layers, plates, placement, compose, style, CLI | `letters`, `ink` |
| `pyntpot._port` | Interim home of the ported code, until the split | anything in the package |

Hard rules the checks enforce:

- `pyntpot` imports no `matplotlib`, `pandas`, `jinja2` or `yaml`.
- The package never touches `os.environ` / `os.getenv`: config is injected.
- No clock reads, no module-level randomness, no `uuid` imports. Files listed in
  `tests/architecture/exemptions/line_budget.txt` are exempt from the clock and random
  bans until they are split.
- No `print()` anywhere in `src/`; logging only.
- Soft file budget of 400 lines. A spike signals a god module; split it. Listed files are
  exempt until they are split.
- No personal content: banned terms and the coordinate allowlist apply to `src/`,
  `tests/`, `docs/` and the root docs.

Public surface discipline: each package `__init__.py` exports only what is public, and
its module docstring states purpose, non-goals and invariants. Keep both current; they are
the first thing an agent reads.
