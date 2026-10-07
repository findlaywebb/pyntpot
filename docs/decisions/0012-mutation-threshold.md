# 0012 — Mutation testing, manual and advisory

Status: accepted

## Context

The spec (D17) asked for mutation testing with mutmut: the changed functions on every
pull request, the whole scope nightly, golden tests excluded. P5.3a built both and
proposed a threshold from the first full nightly. mutmut 3.8 has no "mutate only the
diff" mode. It does restrict which mutants a run tests, by `fnmatch` patterns over
mutant names (`pyntpot.ink.polyline.x_simplify__mutmut_1`, and
`pyntpot.ink.sheet.xǁCanvasǁpx__mutmut_1` for a method). Every run still generates
every mutant in scope and collects which tests reach which function.

The measured CI costs: the nightly took about 12 h of runner time over its 4 shards for
`ink` and `letters`; the PR job took 26 min for one changed `polyline` function (one
edited line of `simplify`, 72 mutants), so a PR that changes several functions that slow
tests reach hits the 60-min timeout. How many shards a full run needs, and whether
`maps` fits at all, is measured below, not guessed.

## Decision

Maintainer decision, 2026-10-07: mutation testing runs manually through `mutation.yml`
(`workflow_dispatch` only; modes `changed`, `pattern`, `all`), and its score is
advisory: reported in the run summary with the survivor count, never compared with a
threshold. No nightly, no PR job, no `min_score`, no ratchet. When to run it: after
writing tests for a module, before a release, and when a test feels weak.

### Configuration

`[tool.mutmut]` in `pyproject.toml`:

- `only_mutate` is the one statement of the scope; the helper scripts read it.
- The test selection is `tests/unit` and `tests/property`, without golden tests. mutmut
  runs pytest inside `mutants/`, where `support.REPO_ROOT` is the mutated tree, so
  `tests/architecture` would scan trampolined source: the line budget fails on every
  mutated file, and the injected `mutmut` import and `# type: ignore` lines break other
  checks. `tests/golden` is too slow per mutant, `tests/mutation` tests the helper
  scripts rather than `src`, and benchmarks time code and assert nothing.
- `pytest_add_cli_args = ["--hypothesis-profile=ci"]`: Hypothesis's built-in `ci`
  profile is derandomised, with no example database and no deadline, so a mutant's
  verdict is the same on every run and a mutant that only slows code is not killed by a
  deadline.
- `process_isolation = "forkserver"`. Under the default `fork`, mutmut runs pytest more
  than once in its own process (stats, then the clean run) and forks every mutant from
  it. Hypothesis then sees a second instance of each property-test class and fails its
  `differing_executors` health check: the clean run fails, and a mutant forked after it
  would be "killed" by the health check, not by a test. `forkserver` runs each pytest
  call in a fresh process.
- No `also_copy`: mutmut copies every file under `source_paths`, so the font and the
  default theme reach `mutants/`.

`[tool.pyntpot.mutation]` holds only `shards`, the shard count of mode `all`.

### Mode `changed`

`tests/mutation/scope.py` reads `git diff --unified=0 origin/<base>...HEAD -- src/pyntpot`,
and maps each changed line range of an in-scope `.py` file to its top-level function or
top-level class's method (a nested function counts for its enclosing one). It writes one
pattern per changed function, and the workflow runs `mutmut run` on them, then reports
the score of the tested mutants. An empty pattern list ends the run green with no shard;
patterns that match no mutant end it green with nothing scored.

Its gaps, by design:

- a change outside any function or method (a module constant, a class attribute) tests
  nothing; mode `all` covers it;
- a function or method with any decorator other than a single `staticmethod` or
  `classmethod` has no mutants in mutmut 3.8, so it is never tested;
- the pattern `x_<name>*` also selects functions whose names extend `<name>`, so a run
  can test a little more than the diff.

### Mode `all`

`tests/mutation/shard.py` lists the in-scope modules that have a mutated function, costs
each by its source line count, and assigns them largest first (ties by name) to the shard
with the lowest running cost (ties to the lowest index). Each shard runs `mutmut run` on
its modules' patterns (`<module>.x_*` and `<module>.xǁ*`; not `<module>.*`, which would
also match a package's submodules), stops at 270 minutes, and uploads its
`mutmut-cicd-stats.json` and its tested mutants' results as one artifact. The `score` job
sums the shards' counts before dividing, and fails when any shard failed or timed out, so
a partial score is never read as a full one. Mode `pattern` runs the given patterns as
one shard.

### Score

`(killed + timeout) / (killed + timeout + survived + suspicious + no_tests + segfault)`.
A timeout counts as caught. `no_tests` counts against the score: an untested mutant is an
untested line. `total` is never summed, because a pattern-restricted run counts every
generated mutant there. mutmut 3.8 classes a mutant ended by `SIGKILL` (exit -9) as
`segfault`; a mutant that loops while growing memory can end that way, and counts against
the score like any other uncaught mutant.

### Measured cost, scope and shard count

Measured on 2026-10-07 on a 4-core machine, as an ubuntu-latest runner has, with all three
subpackages temporarily in `only_mutate`. Counts come from mutmut's `.meta` files, each
exit code mapped by `mutmut.stats.status_by_exit_code`.

- The per-shard overhead `O` is 379 s: a cold run (no `mutants/`) of one mutant,
  `pyntpot.ink.polyline.x_simplify__mutmut_1`. That is generation of all 25409 mutants
  (26 s), stats over the whole test selection, the clean run and the one mutant.
- Each sample below is a warm run under `timeout 1200`. Its wall time includes that
  run's own test listing, clean run and forced-fail check, so `s` errs high. A sample
  the timeout stopped was narrowed to its module's function with the most mutants and
  run again; the narrowed run sets `s`.

| Sample | Wall (s) | Tested | Score |
| --- | --- | --- | --- |
| `pyntpot.ink.polyline*` | 1200, timed out | 179 | 0.5587 |
| `pyntpot.ink.polyline.x_deform_line*` | 651 | 130 | 0.7538 |
| `pyntpot.letters.hand*` | 1200, timed out | 76 | 0.7500 |
| `pyntpot.letters.hand.xǁHandǁ_flat*` | 516 | 95 | 0.7579 |
| `pyntpot.maps.rings*` | 574 | 98 | 0.8061 |
| `pyntpot.maps.painter.cover*` | 1200, timed out | 173 | 0.6879 |
| `pyntpot.maps.painter.cover.x__class_washes*` | 612 | 69 | 0.6522 |

`M` is the mutant count, `s` the wall-clock seconds per mutant (for `maps`, the two
samples' summed wall time over their summed tested mutants), and `H = M * s / 3600`:

| Subpackage | M | s | H (hours) |
| --- | --- | --- | --- |
| `ink` | 6151 | 5.01 (651 / 130) | 8.56 |
| `letters` | 2159 | 5.43 (516 / 95) | 3.26 |
| `maps` | 17099 | 7.10 (1186 / 167) | 33.73 |

The rule: `N_core = max(2, ceil((H_ink + H_letters) / 3.5))` and
`N_all = max(2, ceil((H_ink + H_letters + H_maps) / 3.5))`; if `N_all <= 8` the scope is
all three subpackages and `N = N_all`, otherwise the scope is `ink` and `letters` and
`N = N_core`. The 3.5-hour target leaves 1.5 hours of each shard's 300-minute timeout for
`O` and for imbalance from the line-count proxy.

Here `N_core = ceil(11.81 / 3.5) = 4` and `N_all = ceil(45.55 / 3.5) = 14`. So the scope is
`ink` and `letters`, and `shards = 4`. `maps` is out: its estimated 33.73 hours would
take mode `all` to 14 shards, past the 8 the rule allows. The 21 in-scope modules with a
mutated function (4942 lines) split 1296, 1240, 1198 and 1208 lines across the four
shards.

`s` was measured on this machine, not a runner, and the narrowed samples are single
functions: the timed-out `hand` sample ran at 15.8 s per mutant. The first full run's real
shard times correct `N`.

## Consequences

- No automatic CI signal for test strength. A run costs what the tables say, so mode
  `all` is for occasions, not every change; mode `changed` inherits the PR job's gaps.
- mutmut needs `fork`, so it runs on Linux and macOS only.
- A test that runs for a long time and reaches many functions sets the cost of every
  surviving mutant in them: `tests/unit/maps/test_cli.py::TestMap::test_a_full_cache_makes_no_request`
  takes 72 s and reaches most of `ink.polyline`. A mutant that makes a function loop
  runs to mutmut's wall bound, `(estimated test time + 1) * 15` seconds, about 20
  minutes for such a function. The figures above carry both costs. Excluding slow
  end-to-end tests from the mutation test selection is a possible later improvement, not
  done here.
- It amends ADR 0001's consequence "run mutation testing in CI"; ADR 0001 itself is not
  edited.

## History

Proposed at P5.3a with a PR job, a sharded nightly and a threshold to come; accepted at
P5.3c in this form instead.
