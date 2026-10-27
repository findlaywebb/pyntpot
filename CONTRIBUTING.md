# Contributing

## The gate

Run this before every commit. It is what CI runs.

```bash
uv sync && uv run prek run --all-files && uv run pytest
```

Plain `uv run pytest` runs one test at a time, so a failure reads in order and a debugger works. To run on every core, as CI does:

```bash
uv run pytest -n auto --dist loadgroup
```

`--dist loadgroup` keeps the tests of a module that paints a whole map once on one worker, so the map is painted once; such a test's ID prints with a `@<group>` suffix, which you drop to rerun it. To reproduce a parallel failure, rerun it serially (without `-n` and `--dist`) with the `--randomly-seed=N` the run printed.

A red gate means fix the code. Never loosen a contract or a budget to get green. Changing
a contract is an ADR in `docs/decisions/`.

`numpy`, `pillow` and `fonttools` carry floors, not pins, and Dependabot updates them. The golden parity test stays exact, so a bump that moves golden pixels is a regeneration decision, not a loosened tolerance.

Property tests live in `tests/property`. To reproduce a failure, use the `@reproduce_failure` blob Hypothesis prints, or pass `--hypothesis-seed=N`. `--randomly-seed` alone does not reproduce one, because pytest-randomly does not seed Hypothesis. CI runs derandomised through Hypothesis's built-in `ci` profile, so a CI failure repeats on every run of that commit.

Coverage is gated in CI only (ADR 0011); plain `uv run pytest` stays coverage-free. To check it locally, run a fresh coverage run, then the two gates:

```bash
CI=true uv run pytest -m "not golden and not benchmark" --cov
uv run coverage report --include="src/pyntpot/ink/*,src/pyntpot/letters/*" --fail-under=95 --precision=2
uv run coverage report --include="src/pyntpot/maps/*" --fail-under=92 --precision=2
```

Mutation testing (ADR 0012) is manual and advisory: no pull-request or scheduled job runs it, and its score has no threshold. Run it after writing tests for a module, before a release, or when a test feels weak. On GitHub, open Actions → Mutation → Run workflow, pick the branch, and choose a mode: `changed` (the default) tests the functions the branch changed against `base` (default `main`); `pattern` tests the space-separated mutmut patterns in `pattern`, such as `pyntpot.ink.polyline*`; `all` tests the whole scope in `[tool.pyntpot.mutation] shards` parallel shards, about 12 hours of runner time. The run's summary shows the score and the survivor count, and each shard's artifact holds its stats and surviving mutants. Locally, pass mutmut a pattern; it needs Linux or macOS, because it forks. Results land in `mutants/`, which git ignores, and `uv run mutmut results` lists them.

```bash
uv run mutmut run "pyntpot.ink.polyline*"
```

Benchmarks live in `tests/benchmarks`; a plain `uv run pytest` calls each once, untimed, as a smoke test. `docs/explanation/performance.md` says what they measure. To time them locally:

```bash
uv run pytest -m benchmark --benchmark-enable
```

## Spec flow

One feature is one spec dir under `specs/NNN-name/`, one branch and one pull request.
Write `spec.md`, then `plan.md`, and have the plan reviewed before any code. See
`specs/README.md`.

Three skills under `.claude/skills/` are copied from an MIT-licensed upstream; see
`.claude/skills/THIRD-PARTY-LICENSES.md`.

## Commits and pull request titles

- Commits on a branch: imperative, one line. They are squashed away on merge.
- The pull request title becomes the commit on `main`, so it is a Conventional Commit
  (ADR 0042): `type(scope): description`, for example
  `fix(maps): keep a river name inside the card`. Types: `feat`, `fix`, `perf`, `docs`,
  `refactor`, `test`, `build`, `ci`, `chore`. Scopes: `ink`, `letters`, `maps`, `cli`,
  `docs`, `tests`. Add `!` before the colon for a breaking change. A CI check enforces it.
- Any other change a user would notice goes one per line, in the same form, under
  "Changelog" in the pull request description. The release changelog is drafted from
  these with git-cliff.
- A commit made by an agent session ends with the attribution
  trailers its session gives (`Co-Authored-By:`, `Claude-Session:`); no
  other trailers.

## Place names in tests and examples

Use real UK places, the focus places first, spread across regions so no file clusters
round one area. A few landmark city names are fine. Never invent a name. Use Welsh names
for Welsh places. Where a string is drawn, measured or compared, pick a real name of the
same length.

- **Focus places:** the Lake District, Ambleside, Keswick, the Highlands, Skye, Eryri,
  Oxford, Y Fenni.
- **Towns and villages:** Aberhonddu, Ambleside, Aviemore, Bakewell, Braemar,
  Buxton, Castleton, Crucywel, Glencoe, Grasmere, Hawes, Keswick, Machynlleth, Malham,
  Pitlochry, Settle, St Ives, Trefynwy, Y Fenni, Zennor.
- **Rivers:** Dee, Derwent, Eden, Exe, Kennet, Medway, Severn, Tay, Tweed, Wysg. The Dee
  and the Severn cross into England and keep their English names; the Wysg is wholly
  Welsh and takes its Welsh name.
- **Roads:** A470, A5, A66, A591, A82, A9, B4521.
- **Parks and landmarks:** Regent's Park, Dovedale, Malham Cove, Cat Bells, Yr Wyddfa.

Coordinates always stay inside a fixture box. Lynmouth is the first box; the focus-place
fixtures add the others. Names that belong to the Lynmouth fixture (Lyn, Heddon,
Brendon, Watersmeet) stay as they are.

## Writing docs

These conventions apply to the README and everything under `docs/`. The pictures carry
the style; the words stay plain.

- **Voice:** second person, present tense, British English, sentence-case headings. Follow
  the Google developer documentation style guide, except its spelling. Use glossary terms
  only (`GLOSSARY.md`). Prefer studio verbs ("paints", "lays a wash", "letters") to
  "renders" and "generates". No hype words. No em or en dashes.
- **Traps:** "sheet" is the paper's noise fields, not paper. "Canvas" is the pixel grid.
  "Map" never appears in `ink` or `letters` pages. Never call what the engine does a
  "filter", an "effect" or a "shader".
- **Images by page type:** the README, tutorials and explanation pages show an image on
  every page. How-to guides show a result image where one exists. Reference pages show
  none, except the swatch sheets.
- **Every image** is registered in `tests/support/docs_images.py`. Its caption reads
  "Painted by `examples/<stem>.py`", with the seed where the script takes one. Its alt
  text says what the picture shows or what changed. Lettered text in an image is
  repeated as real text beside it.
- **Places:** use the focus places for new figures. Lynmouth names appear only for the
  Lynmouth card. Never invent a name.
- **Designed gaps** are stated as capability facts, never as roadmap numbers.

Before you commit docs, search the human-facing prose (everything except
`docs/decisions/`) for em and en dashes; the search finds none.

## Security scanning

CodeQL runs through GitHub's default setup, not a workflow file in this repository.
Report vulnerabilities as described in `SECURITY.md`.
