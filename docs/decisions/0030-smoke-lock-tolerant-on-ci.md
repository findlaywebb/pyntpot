# 0030 — The smoke lock is tolerant on CI

Status: accepted

## Context

The painter's smoke test (`tests/unit/maps/painter/test_smoke.py`) pins the SHA-256 of
the three plates the smoke box paints in `SMOKE_SHA`, and two tests,
`test_the_flags_off_still_paint_the_plates_that_were_approved` and
`test_the_wash_flags_off_still_paint_the_plates_that_were_approved`, compare a fresh
painting with it byte for byte.

After the half-pixel fix of ADR 0025, CI's `checks (3.13)` and `checks (3.14)` jobs on
PR #26 fail both tests at `assert got == SMOKE_SHA`, for the wash plate only. CI writes
`8f90ea05b1bc4742c8ffc645efb569137e6bfb94a534bae1c95285a61ec9a197`; the pinned value is
`c1617293c916b15a3d86d54cbd7d5c83ba1c2b18261db07b8b9ba7f973a67272`.

numpy dispatches the float32 wash maths to AVX-512 code where the CPU has it and to
other code where it does not. The two round the last bit differently at about 1000 to
1300 pixels, and `to_img` (`src/pyntpot/ink/io.py`) rounds to 8 bits. Before the fix no
such difference crossed a rounding boundary; after it one does, and pixel (row 90,
column 97) of the 148 by 240 wash plate moves by one level. Paper and pen are equal in
both modes. So the exact smoke hash is a property of the CPU, as ADR 0006 found for the
goldens, and the fix itself is correct.

The difference reproduces on the pinning machine with
`NPY_DISABLE_CPU_FEATURES=X86_V4 uv run pytest tests/unit/maps/painter/test_smoke.py -k approved`:
the same two tests fail with CI's wash hash, and paper and pen keep their pinned bytes.

The same two tests fail the stats pass of the mutation workflow (`mutation.yml`), which
runs `tests/unit tests/property -m "not golden"` in exact mode (`[tool.mutmut]` in
`pyproject.toml`). mutmut exits 1 when its stats pass fails ("failed to collect
stats"), so on a runner without AVX-512 that workflow tests no mutant.

The golden pixel bound (`MAX_DIFFERING_FRACTION = 0.005`, `MAX_CHANNEL_DELTA = 2`) is
coarse on a plate this size: 0.005 of 148 by 240 is 177 pixels, about 11% of the pen's
1592 inked pixels. The difference measured is 1 pixel at 1 level, on the wash only, with
paper and pen byte-equal.

The pinning machine: `Linux vm 6.18.44-fc-v140 #1 SMP PREEMPT_DYNAMIC @0 x86_64 x86_64
x86_64 GNU/Linux`, Python 3.13.16, numpy 2.5.2, Pillow 13.0.0, `avx512f` present in
`/proc/cpuinfo`.

## Decision

This ADR supersedes nothing. It applies ADR 0006's "exact parity is per platform" to the
smoke lock.

- The smoke box's wash plate is committed as `tests/golden/smoke/wash.webp`, beside the
  Lynmouth goldens, painted by the painter call the two tests make:

  ```
  PYTHONPATH=tests uv run python -c "import sys; from pathlib import Path; from pyntpot.maps.painter.plates import paint_plates; from unit.maps.painter.test_smoke import smoke_box; style, basemap = smoke_box(); paint_plates(basemap, style, Path(sys.argv[1]))" "$OUT"
  ```

- The smoke lock stays byte-exact by default, so G-here holds it exactly on the machine
  that pinned it.
- Under `--golden-tolerance`, `paper` and `pen` stay byte-exact against `SMOKE_SHA`, and
  only `wash` is compared with its committed copy within the golden bound
  (`MAX_DIFFERING_FRACTION` and `MAX_CHANNEL_DELTA`, unchanged, imported from
  `tests/golden/test_parity.py`). The coarse bound covers only the plate the CPU moves.
- CI's `checks` and `prerelease` Tests steps and the mutation runs (`[tool.mutmut]`
  `pytest_add_cli_args`) pass the flag.
- A test pins the committed wash plate to `SMOKE_SHA["wash"]`, so the two cannot drift
  apart.

## Alternatives rejected

- Two pinned hashes, one per CPU. That lists CPUs one by one, so a third platform (ARM,
  or a numpy for a later Python) breaks the lock again.
- Quantising the wash before `to_img`. That changes `src`, moves golden pixels and
  reopens the ADR 0025 window, and any quantisation step still has a boundary a one-ulp
  difference can cross.
- Pinning the hash under baseline-only numpy dispatch. That needs the variable set
  before numpy is imported, against the `os.environ` ban, and works only on x86.

## Consequences

- A change that moves the smoke plates updates `SMOKE_SHA` and the committed wash plate
  in the same commit, painted by the command above.
- On another machine the local suite passes `--golden-tolerance`, as the golden suite
  does.
- A CPU difference that ever reaches paper or pen fails tolerance mode as well, and
  needs its own ADR.
- The coverage run of ADR 0011 gains the flag and measures the same lines.
- The mutation workflow passes the flag too, so its stats pass no longer depends on the
  runner's CPU, and the mutants are killed by the same tests as before.
