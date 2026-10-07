# Contributing

## The gate

Run this before every commit. It is what CI runs.

```bash
uv sync && uv run prek run --all-files && uv run pytest
```

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

## Commits

- Imperative, one line.
- No co-authorship trailers.

## Place names in tests and examples

Use real UK countryside names, spread across regions so no file clusters round one area.
A few landmark city names are fine. Never invent a name. Where a string is drawn,
measured or compared, pick a real name of the same length.

- **Towns and villages:** Abergavenny, Ambleside, Aviemore, Bakewell, Braemar,
  Brecon, Buxton, Castleton, Crickhowell, Glencoe, Grasmere, Hawes, Keswick,
  Malham, Monmouth, Pitlochry, Settle, St Ives, Zennor.
- **Rivers:** Dee, Derwent, Eden, Exe, Kennet, Medway, Severn, Tay, Tweed, Usk.
- **Roads:** A470, A5, A66, A591, A82, A9, B4521.
- **Parks and landmarks:** Regent's Park, Dovedale, Malham Cove, Cat Bells, Snowdon.

Coordinates always stay inside the Lynmouth fixture box. Names that belong to the
Lynmouth fixture (Lyn, Heddon, Brendon, Watersmeet) stay as they are.

## Security scanning

CodeQL runs through GitHub's default setup, not a workflow file in this repository.
Report vulnerabilities as described in `SECURITY.md`.
