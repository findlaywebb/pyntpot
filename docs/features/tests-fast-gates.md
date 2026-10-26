# The gates could run in minutes, not half an hour

**What exists today.** The golden run takes about 20 minutes on the Linux runner and 26 on
macOS, and the exact local run about 27 minutes on four cores. A map `compose` takes
about 2.8 s on the CodSpeed benchmark, and mutation testing costs about 5 to 7 s a mutant
(`docs/issues/slow-tests-in-mutation-runs.md`). Every push to a pull request waits on the
slowest of these.

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
