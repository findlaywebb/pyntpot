"""The stages of one stroke: the plain records `stamp` passes between its steps.

Key types: `Trace`, the path resampled evenly with its normals; `Mark`, the pressure and
width along it and how far a nib has run down; `Tip`, the logical bristles and the fields
drawn per bristle; `Sampled`, the tip sampled across at sub-pixel spacing; `Lay`, all of
those with each sample's sideways offset, which is everything the weights and the deposit
read.

They hold arrays and compute nothing. They are frozen, so a step that moves the path
returns a new `Trace` instead of changing the one it was given.
"""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Trace:
    """A path resampled evenly: positions, unit normals and arc length."""

    x: np.ndarray
    y: np.ndarray
    nx: np.ndarray
    ny: np.ndarray
    t: np.ndarray
    total: float


@dataclass(frozen=True)
class Mark:
    """Pressure and width along a stroke, and how far a nib has run down."""

    press: np.ndarray
    width: np.ndarray
    spent: np.ndarray | None


@dataclass(frozen=True)
class Tip:
    """The logical bristles: weights, phases and the fields drawn per bristle."""

    m: int
    u_log: np.ndarray
    bw_log: np.ndarray
    drift_log: np.ndarray
    fp_log: np.ndarray
    fq_log: np.ndarray
    res_log: np.ndarray | None
    dir_ph: np.ndarray | None
    jit_log: np.ndarray | None
    along_log: np.ndarray | None


@dataclass(frozen=True)
class Sampled:
    """The tip sampled across at sub-pixel spacing."""

    m_hi: int
    u: np.ndarray
    bw: np.ndarray
    dc: np.ndarray
    ds: np.ndarray
    fp: np.ndarray
    fq: np.ndarray
    res0: np.ndarray | None
    prof: np.ndarray
    mean_w: float


@dataclass(frozen=True)
class Lay:
    """Everything one stroke's weights and deposits are read from."""

    tr: Trace
    ink: Mark
    tip: Tip
    smp: Sampled
    off: np.ndarray
