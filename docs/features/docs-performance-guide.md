# The docs could say how long a map takes and how much memory it needs

GitHub issue: [#TBD](https://github.com/findlaywebb/pyntpot/issues/TBD)

**What exists today.** `docs/runbooks/performance.md` records benchmark measurements for
contributors: where the painter's time goes and what the gates cost. It is off the site.
No user-facing page tells a reader how long `pyntpot map` or `compose` takes for a
track, or how much memory a map at a given size needs, or what changes those numbers
(the card's display size, supersampling, the track's extent, a warm or cold cache).

**What the feature would add.** A how-to or reference page, from measurements and with the
machine and versions stated, giving time and peak memory for a few track sizes and display
widths, cold and warm cache, and which style fields move them most.

**Possible shape.** Measure with the existing benchmarks where they fit and a small timed
run of `pyntpot map` over the fixture tracks for the rest; state numbers as measurements,
not promises, as the runbook does.

**Related.** `docs/runbooks/performance.md`.
