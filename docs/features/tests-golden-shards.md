# The macOS golden job could finish sooner

GitHub issue: [#91](https://github.com/findlaywebb/pyntpot/issues/91)

**What exists today.** The golden job runs on `ubuntu-latest` with four workers and on
`macos-15` with two, because a worker peaked near 3 GB and that runner has 7 GB
(`specs/002-parallel-gates/`). On 2026-10-27 the Linux job took about 8 minutes and the macOS
job about 16, so macOS sets how long a pull request waits.

**What the feature would add.** A macOS golden job that finishes near the Linux one: the
golden selection split across two or three macOS runners by a matrix, or the macOS job run
only when the code it reads changes.

**Why it is not a defect.** The job is correct and green; it is slow.

**Possible shape.** First re-measure: the painter's memory fell after
`specs/003-painter-hot-paths/` (a Lynmouth paint peaked at about 0.9 GB instead of 1.7 GB),
so three workers may now fit on macOS without any sharding. If not, a `shard` matrix key
with pytest's `-k` or a small collection hook splitting the golden tests into groups of
similar total time; the docs images are the largest group. A path filter needs a required
check that still reports when skipped.
