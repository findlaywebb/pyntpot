# The gates could run in minutes, not half an hour

GitHub issue: [#81](https://github.com/findlaywebb/pyntpot/issues/81)

**What exists today.** The golden run takes about 20 minutes on the Linux runner and 26 on
macOS, and the exact local run about 27 minutes on four cores. A map `compose` takes
about 2.8 s on the CodSpeed benchmark, and mutation testing costs about 5 to 7 s a mutant
(`docs/issues/slow-tests-in-mutation-runs.md`). Every push to a pull request waits on the
slowest of these.

The test and golden steps now run on every core with `pytest -n auto --dist loadgroup`
(`specs/002-parallel-gates/`). Measured on a four-core machine, same flags before and
after (2026-10-27):

| Run | Serial | Parallel |
|---|---|---|
| Fast selection (`-m "not golden and not benchmark"`) | 2 min 25 s | 44 s |
| The same with `--cov` | 2 min 47 s | 54 s |
| Golden (`-m golden --golden-tolerance`) | 31 min 38 s | 8 min 6 s |

A golden worker peaks near 3 GB on the largest paints, so the macOS runner (3 cores,
7 GB) runs two workers. What remains is the painting itself: `specs/003-painter-hot-paths/`.

**What the feature would add.** A profiled, measured speed-up of the painting itself and of
the gates around it: the hot paths of `ink` (wash, granulation, nib plates, compositing)
and `maps` (lettering placement, plate building) made faster, and the golden suite split
so the docs images, the place cards and the Lynmouth parity run in parallel jobs or only
when the code they read changes.

**Why it is not a defect.** The run times are correct results reached slowly; nothing is
wrong in a picture. The gates were built for proof first.

**Possible shape.** Profile one place card and one docs image with `cProfile` and record
the top costs; set a time budget per gate (for example the golden job under 8 minutes) and
a CodSpeed budget per benchmark; vectorise or cache the hot paths; shard the golden job by
group with a matrix; keep every pin exact, since a speed-up must not move a pixel unless an
ADR says so.
