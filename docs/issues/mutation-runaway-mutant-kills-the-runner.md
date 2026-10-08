# A runaway mutant takes the mutation runner down

The Mutation workflow's first run on `main` (run 37689849941, `mode: pattern`,
`pyntpot.ink.polyline.x_simplify*`) died twice the same way: the shard's runner got
"The runner has received a shutdown signal" (exit 143), at 9 min and at 4 min 40 s, long
before the step's 270-minute timeout, so the score job had no stats.

The cause is `pyntpot.ink.polyline.x_simplify__mutmut_31`, which changes
`best, bi = -1.0, lo` to `best, bi = +1.0, lo` in `simplify`. When every point of a
segment lies within 1.0 of its chord, `bi` stays at `lo`, and with `eps < 1` the loop
pushes `(lo, lo)` and `(lo, hi)` and pops `(lo, hi)` again for ever, one tuple a turn:
about 90 to 100 MB a second, which fills the runner's 16 GB in about two minutes, well
inside mutmut's wall-clock bound. mutmut 3.8 limits CPU time only (`RLIMIT_CPU` and a
`SIGXCPU` timer) and has no memory option. The P5 log already records this mutant as
exit -9 under the out-of-memory killer.

To show it: run that one mutant under a cap, never uncapped,
`prlimit --as=3500000000 -- uv run mutmut run pyntpot.ink.polyline.x_simplify__mutmut_31`
in a scratch worktree; the mutant's process reaches the cap about 31 s in, gets
`MemoryError`, and mutmut records it killed. Uncapped, its memory grows until the machine
kills something.

Possible fix: run `mutmut run` in the workflow under `prlimit --as=3500000000 --`
(rlimits are inherited by every process mutmut forks; the largest normal process measured
2,308 MB of address space, and four capped children fit in a 16 GB runner), record the cap
in ADR 0012's decision, and pin it with a text test over the workflow step.
