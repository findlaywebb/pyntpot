# 002 — plan review

**Verdict: BLOCK** (approach is sound with fixes: xdist + `loadgroup` + per-module groups is right).
The one change that matters most: **take `--dist loadgroup` out of `addopts`.** It is not a no-op
without `-n`, and it breaks the documented local benchmark command.

Verified on this repo (pytest 9.1.1, xdist 3.8.0, pytest-benchmark 5.3.0, pytest-cov 7.1.0,
pytest-randomly 5.0.0, pytest-codspeed 5.0.3).

## BLOCKING

1. **`--dist loadgroup` in `addopts` breaks `--benchmark-enable` and `-p no:xdist`.**
   - xdist only resets `dist` to `"no"` when `-n` is given (`xdist/plugin.py` `pytest_cmdline_main`).
     Without `-n`, `dist` stays `"loadgroup"`.
   - pytest-benchmark checks `config.getoption('dist') != 'no'` (`pytest_benchmark/session.py:77`).
     It treats the serial run as xdist, silently turns timing off, and raises
     `PytestBenchmarkWarning` in `pytest_unconfigure`.
   - Measured: `uv run --with pytest-xdist pytest tests/benchmarks/test_letters.py --benchmark-enable --dist loadgroup`
     gives "4 passed in 0.59s" (nothing timed), then a traceback and **exit 1**.
   - That command is the documented one (`CONTRIBUTING.md:35`, `docs/explanation/performance.md:34`).
     003 depends on it.
   - `-p no:xdist` also fails: `error: unrecognized arguments: --dist`. That is the plan's own
     CONTRIBUTING repro advice.
   - The plan's benchmark check (`uv run pytest -m benchmark`) passes either way, so it cannot catch this.
   - **Fix:**
     - Leave `addopts` alone.
     - Write `-n auto --dist loadgroup` explicitly in `ci.yml` `checks` and in `golden.yml`.
     - Document `uv run pytest -n auto --dist loadgroup` in `CONTRIBUTING.md` and `CLAUDE.md`.
     - Add to the test plan: `uv run pytest -m benchmark --benchmark-enable` exits 0 and prints a timing table.
     - The prerelease install change and the mutmut check then stop being needed for the
       `--dist` reason; drop them, or keep the mutmut smoke as a cheap check.

2. **The `xdist_group` marker exists only while the xdist plugin is loaded, and `--strict-markers` is on.**
   - With xdist absent or disabled, the six marked modules fail collection:
     `'xdist_group' not found in markers configuration option` (verified in a scratch project).
   - This hits `-p no:xdist` and any environment without xdist, such as the hand-installed `prerelease` job.
   - **Fix:**
     - Register it in `[tool.pytest.ini_options] markers` as one line, e.g.
       `"xdist_group(name): tests that share one xdist worker (pytest-xdist --dist loadgroup)"`.
       Registering it twice is harmless.
     - Add a check: `uv run pytest -p no:xdist tests/golden/test_parity.py tests/unit/maps/test_route_ink.py --co`
       collects without error.

3. **The "paints once" check cannot show what it claims.**
   - `addopts` has `-q`, so `-v` gives verbosity 0: dots only, no `[gwN]` lines (verified).
     You need `-vv`.
   - "On one worker" also does not prove "painted once". `--setup-show` does not help either:
     worker terminal output is not relayed.
   - **Fix:** run the six grouped modules with
     `-m golden -n 4 --dist loadgroup -vv --durations=0 --durations-min=10`. Require:
     - each module's `[gwN]` is the same for all its tests;
     - exactly **one** `setup` duration of 40 s or more per module.

     Durations travel back in the reports, so this does prove one paint per run.

## SHOULD-FIX

4. **The "after" numbers must come from the final command.**
   - The parallel golden run now in progress (PID 2736) is `-n 4` with default `--dist load`.
     The 50 s fast figure is also `load`.
   - `loadgroup` uses the LoadScope scheduler instead: it hands out one unit at a time and
     orders units by group size. Its timing and memory differ.
   - **Fix:** re-measure fast, golden, and the RSS peak with `-n 4 --dist loadgroup`. Run
     nothing else alongside. (I ran one 13 s subset during that run; ignore any blip.)

5. **Exact vs tolerance mode is mixed.**
   - The serial baseline was `--golden-tolerance`. The plan's parallel local gate is exact.
   - If exact does not pass serially on this sandbox, the agent stalls. The before/after
     times also stop being comparable.
   - **Fix:**
     - Time "after" with the same flags as "before".
     - Run exact parallel as a separate pass/fail check.
     - If exact fails, re-run that test serially. A test that also fails serially goes to
       `docs/issues/` and does not block this change.

6. **The macOS fallback is underspecified.**
   - **No decision rule.** Suggested rule: projected peak = controller + 3 × the largest
     worker RSS measured locally (macos-15 = 3 cores, 7 GB; `auto` gives 3 workers). If that
     is over 5 GB, use `workers: 2`.
   - **No Ubuntu value.** As written, `-n ${{ matrix.workers }}` is empty on Ubuntu and pytest
     fails to parse it. Use `${{ matrix.workers || 'auto' }}`, or give both `include` entries
     a value.
   - **Sampling.** A 2 s `ps` sample can miss spikes. If cgroup v2 is available, also read its
     `memory.peak`.
   - Spot sample during the in-progress run: about 0.49–0.75 GB per worker.

7. **`publish.yml` is not decided.**
   - It runs the same fast suite and the ~25-minute serial golden run.
   - The plan neither touches it nor lists it under "leave alone", so the agent will guess.
   - **Fix:** state it either way. Leaving it alone is defensible, since tag-only paths are
     not exercised by the PR's CI.

8. **The CONTRIBUTING repro paragraph needs two corrections.**
   - Under loadgroup, a grouped test's reported nodeid carries an `@<group>` suffix, e.g.
     `...::test_each_output_matches_the_golden[map.png]@test_parity`. Strip it to rerun.
   - Once fix 1 is in, serial is just "drop `-n`". Do not advise `-p no:xdist`.

## Checked and fine (no action)

- **`xdist_group` on classes:** the worker reads `item.iter_markers` (`xdist/remote.py:245`),
  so class marks apply. One group arrives as a single contiguous unit, so the module fixture
  is not torn down mid-group.
- **pytest-cov + `-n`:** combines into `.coverage`. A `--cov -n 2` subset run passed and
  printed the combined report, with no warnings-as-errors trip.
- **Benchmarks in an `-n` run:** stay quiet, because `--benchmark-disable` keeps
  `xdist_warning` false. CodSpeed runs fine.
- **Hypothesis:** deadlines are off (`tests/support/properties.py` `UNTIMED`).
- **No shared writes outside `tmp_path`:** checked `tests/golden`, `tests/unit/maps`, `tests/examples`.
- **Artifacts:** `--basetemp` becomes `…/pytest/popen-gwN/…`, which the artifact glob `**` still matches.
- **Grouping is worth it:** about 306 s of setup, repeated on up to 3 extra workers.

---

# Round 2

**Verdict: BLOCK.** One finding, and the fix is mechanical. `plan.md` now takes all eight
round-1 findings correctly. `tasks.md` was not updated to match, and it still tells the
agent to do the exact thing that finding 1 removed.

Checked again this round:

- With the `xdist_group` marker registered in the ini and xdist loaded, `--strict-markers`
  and `--strict-config` raise no error. With `-p no:xdist` the module collects and passes.
  With `-n 2 --dist loadgroup` the test runs as `…::test_one@g` on one worker.
- With xdist installed and no `--dist`, `--benchmark-enable` exits 0 and prints the timing
  table.
- `--durations` setup and call lines are passed back from workers, so test-plan step 5 can
  show a single paint per module.
- In `golden.yml`, `include: [{os: macos-15, workers: 2}]` adds a key to the existing
  macos-15 entry. `matrix.workers || 'auto'` then gives `auto` on Ubuntu.

## BLOCKING

1. **`specs/002-parallel-gates/tasks.md` contradicts the revised plan.** The workflow says
   to implement while ticking off `tasks.md`, so the agent will follow it line by line.
   As it stands it says:
   - "`pytest-xdist` in the dev group, `uv lock`, **`--dist loadgroup` in `addopts`**". This
     brings back round-1 finding 1.
   - "`ci.yml` (`checks -n auto`, **prerelease install**)". The plan now leaves `prerelease`
     alone, and `-n auto` lacks `--dist loadgroup`.
   - Local checks include a "**mutmut clean run**". The plan dropped it.
   - It also leaves things out: registering the marker, `publish.yml`, the
     `--benchmark-enable` check, the `-p no:xdist` collection check, the `-vv --durations`
     paint-once check, and separate tolerance-timing and exact runs.

   **Fix:** rewrite the unticked lines so they follow plan §Files to touch and test-plan
   steps 1 to 10, in the plan's order:
   1. dependency and marker registration;
   2. group marks;
   3. local checks 1 to 9;
   4. `ci.yml` checks, `golden.yml` and `publish.yml`;
   5. docs;
   6. review;
   7. PR.

## Non-blocking note

- Test-plan step 3 records only the RSS **sum** and `memory.peak`. The macOS rule needs the
  controller's RSS and the **largest single worker** peak. Have the `ps` sampler log RSS for
  each PID so that the rule's inputs are recorded rather than inferred.
