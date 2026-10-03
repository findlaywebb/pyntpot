# pyntpot

A Python library that paints hand-drawn watercolour and pen-and-ink raster images:
paper, washes, brushes, nibs, pigment compositing and hand lettering, with route maps
from vector OpenStreetMap data and elevation as its first application. Built
**agentically**: the deterministic gate stack, not human approval gates, is the source of
truth (see `docs/decisions/0001-agentic-gates.md`).

## Where the thinking lives

- `docs/README.md` — index and reading order
- `docs/architecture.md` — package layout and the boundary
- `GLOSSARY.md` — canonical terms; no synonyms
- `docs/decisions/` — ADRs; add one for any boundary or public-API change
- `specs/` — one dir per feature

## Toolchain

uv (Python 3.13+, one `src/pyntpot` package) · **ty is the sole type gate** (no
pyright/mypy) · ruff · import-linter · prek hooks · vulture (warn-only sweeps, not a
commit gate).

```bash
uv sync                  # one venv
uv run pytest            # all tests (tests/)
uv run ruff check .      # lint        (ruff format . to format)
uv run ty check          # types
uv run lint-imports      # boundary contract
prek run --all-files     # everything the commit hook runs
```

The gates are wired into prek + CI. **A red gate is the architecture speaking: fix the
code, never loosen a contract or budget to get green.** Contract changes are ADRs. The
one sanctioned relaxation is the exemptions directory
(`tests/architecture/exemptions/`), which lists the interim `_port` code until it is
split.

## The boundary rule

Target layering, a P4 outcome: `maps -> letters -> ink`, each importing only the layers
to its right. Until the split, all code lives in the private `pyntpot._port` subpackage
with no layer contract. See `BOUNDARIES.md`; enforced by import-linter and
`tests/architecture/`.

## Conventions (the non-inferable ones)

- **No ABC/Protocol until the 3rd real implementation** (rule of three), except the
  provider protocols `Features` and `Elevation`, which are settled design.
- **Soft budget 400 lines/file** (enforced by test). Over budget: **split into multiple
  files** along responsibility lines; never trim, squeeze, or thin docstrings to fit.
  Files in `exemptions/line_budget.txt` are exempt until they are split.
- **Module and public-API docstrings are the agent contract**: purpose, key types, what it
  does *not* do, invariants. State designed gaps as capability facts, never spec or
  roadmap numbers (enforced by an architecture test).
- **No `os.environ` / `os.getenv`**: config is injected (enforced by test).
- **Place names** in tests and examples are predominantly real UK countryside names across regions (a few landmark city names allowed), never invented; coordinates stay in the Lynmouth fixture box. See `CONTRIBUTING.md`.
- Logging only, never `print` (enforced). `raise ... from exc`. `pathlib` over `os.path`.
- One canonical name per concept: check `GLOSSARY.md` before introducing a term.
- Names say what a thing is. Shallow nesting (3 to 4 levels at most).

## Testing discipline

- **Every test has a docstring stating what it proves** (ruff `D` enforces presence in
  tests deliberately). Summary line only: no Args/Returns/Raises in test docstrings.
- **No mocking.** Real objects only. `unittest.mock` and `pytest-mock` are banned by an
  architecture test; a genuine third-party boundary earns an explicit allowlist entry
  there, nothing else does.
- **Never test third-party code.** A test fails only when our code changes.
- **Fixtures**: function-scoped by default, no `autouse`, shallow; prefer factory builders
  over fixture chains. One exception: a module-scoped fixture for an immutable object
  (a built sheet, a loaded font, a parsed fixture file). Group behaviour families in
  plain classes.
- **Warnings are errors** (`filterwarnings = ["error"]`), `xfail_strict`, and test order is
  randomised (`pytest-randomly`): an order-dependent failure means coupled state, so fix
  the coupling, never the order. Reproduce with the printed seed.
- **Golden values are pinned literals**, never recomputed by the code under test on both
  sides. Golden parity is exact locally; CI uses `--golden-tolerance`. Hypothesis
  properties cover algorithmic invariants. `parametrize` carries `ids=`.

## Workflow

One feature = one spec dir = one branch = one PR (`specs/README.md`).

1. Scope into `specs/NNN-name/spec.md`: what and acceptance criteria.
2. Plan into `plan.md` (files to touch *and* to leave alone). A **plan-reviewer agent**
   (fresh context, sceptical staff engineer) reviews it and **blocks** until it passes; no
   human checkpoint.
3. Implement autonomously against the plan, test-first; tick off `tasks.md`.
4. Review the diff against the plan. **Done = green CI + matches spec.**

Commit working checkpoints before stopping. Out-of-scope discoveries go to the backlog or
`docs/issues/`, not into the current diff.
