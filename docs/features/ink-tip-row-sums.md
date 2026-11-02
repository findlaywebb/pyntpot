# The brush tip's running sums could be cheaper

GitHub issue: [#92](https://github.com/findlaywebb/pyntpot/issues/92)

**What exists today.** `src/pyntpot/ink/tip.py` smooths a tip's weights and its corners with
box passes built on `np.cumsum`, thousands of small calls per map paint (most of the 4,872
`cumsum` calls a Lynmouth paint made on 2026-10-27; the blur's share was 414).
`specs/003-painter-hot-paths/` made `blur` sum large planes by contiguous row adds down a
transposed buffer, bit for bit the same sums.

**What the feature would add.** The same treatment where it pays in `tip.py`: fewer, larger,
contiguous sums, or the padding written into a preallocated buffer instead of `np.pad`.

**Why it is not a defect.** The sums are right; they are made in many small calls.

**Possible shape.** Profile one stamp of the wet river brush, then measure wall time and
CodSpeed instruction counts: the tip's arrays are small, and on small arrays the row adds
cost more instructions than `cumsum` (the reason `blur` keeps `cumsum` below
`_ROW_SUM_MIN_CELLS`). Any change must keep every pixel exact.
