# 0051 — The classic paper lock is tolerant too

Status: accepted

## Context

`tests/unit/ink/test_paper.py::TestClassicEdge::test_the_classic_plate_is_the_pinned_one`
pins the first 16 hex digits of the sha-256 of the classic paper plate's float32 bytes
(`CLASSIC_PLATE_SHA`). Unlike the smoke lock of ADR 0030 it has no tolerance mode, so it
fails on a machine whose numpy rounds the plate's float32 maths differently, with or
without `--golden-tolerance`. Issue #86 found it failing on macOS 26.6 arm64.

It reproduces on an x86 machine with AVX-512 by running numpy on baseline instructions
only: `NPY_DISABLE_CPU_FEATURES="X86_V4 X86_V3"` gives `a8a4677aa5d15574`. The two
plates differ by one float32 ulp (6e-8) in about 4% of their values, and not one value
rounds to a different 8-bit level. With only AVX-512 turned off the plate is unchanged.

The two smoke tests of #86 fail exact and pass under `--golden-tolerance`, which is what
ADR 0030 designed: only the wash plate moves. The report that the smoke paper plate moved
too came from pytest eliding the hash dict in its assertion message.

## Decision

This applies ADR 0030 to the classic paper lock.

- The classic plate is committed as `tests/golden/paper/classic.npy`, the float32 array
  `_paper(_classic())` returns on the machine that pinned `CLASSIC_PLATE_SHA`.
- The lock stays byte-exact by default.
- Under `--golden-tolerance` the plate is compared with the committed array, and no value
  may differ by more than `CLASSIC_PLATE_ATOL = 1e-5`. That is about 170 times the drift
  measured, to cover another platform's `exp`, and 1/400 of an 8-bit level.
- A test pins the committed array to `CLASSIC_PLATE_SHA`, so the two cannot drift apart.
- The local gate is stated as exact on the pinning machine and `--golden-tolerance`
  anywhere else (`CLAUDE.md`, `CONTRIBUTING.md`), which ADR 0030's consequences already
  implied.

## Alternatives rejected

- Hashing the plate rounded to 8 bits. A one-ulp difference can still cross a rounding
  boundary, as ADR 0030 found for the wash.
- Reusing the golden pixel bound. The plate is a float array, not an image, and the
  fractional bound is coarse on 5400 pixels.

## Consequences

- A change that moves the classic plate updates `CLASSIC_PLATE_SHA` and the committed
  array in the same commit.
- CI's `checks` job, which already passes the flag, now covers this lock on any runner CPU.
