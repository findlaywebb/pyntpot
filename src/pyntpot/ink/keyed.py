"""Keyed generators: a random stream per item, derived from a seed and the item itself.

Key functions: `keyed_rng`, the generator for one item, from a seed and the words that
name the item; `line_key`, those words for a polyline, read from its own points;
`uniform_at`, one uniform draw per index of a field, a pure function of the seed and the
index.

A painting lays many independent items: rings deformed one after another, strokes
stamped one after another, blooms seeded across a wash. Drawn from one shared generator,
an item that consumes one draw more or less (a median test or a `round()` that flips under
a sub-pixel change) shifts every draw after it, so a change to one item repaints all the
items after it. Each item here gets its own stream instead, named by what the item is
rather than by where it falls in a sequence, so an item's draws depend only on the seed
and the item.

It draws nothing itself beyond `uniform_at`, and it reads no style.

Invariants: the same seed and the same words give the same stream on every run and every
platform (the words are hashed with BLAKE2b, not Python's salted `hash`); `line_key` reads a
line only through its points rounded to the grid it is given, so two lines that round the
same are the same key, however finely it is sampled; `uniform_at` is in the open interval
0 to 1.
"""

import hashlib

import numpy as np
import numpy.typing as npt

#: Seed words are taken as unsigned 64-bit integers.
_WORD = (1 << 64) - 1
#: The splitmix64 constants (Steele, Lea and Flood): a step, then two multipliers.
_GOLDEN = np.uint64(0x9E3779B97F4A7C15)
_MIX_1 = np.uint64(0xBF58476D1CE4E5B9)
_MIX_2 = np.uint64(0x94D049BB133111EB)
#: The top 53 bits of a word make a double; this is one step of them.
_ULP = 2.0**-53


def _word(part: int | str) -> int:
    """One seed word: an integer as itself, a string through its BLAKE2b digest."""
    if isinstance(part, str):
        return int.from_bytes(hashlib.blake2b(part.encode(), digest_size=8).digest(), "little")
    return int(part) & _WORD


def keyed_rng(seed: int, *parts: int | str) -> np.random.Generator:
    """The generator for one item: a stream of its own, from the seed and the item's words.

    Args:
        seed: The consumer's seed, from the style.
        parts: The words that name the item: integers (negative ones are taken modulo
            2**64) or strings.

    Returns:
        A generator no other item's words reach.
    """
    return np.random.default_rng(np.random.SeedSequence([_word(seed), *map(_word, parts)]))


def line_key(pts: npt.ArrayLike, grid: float) -> tuple[int, int]:
    """The words that name a polyline, from its own points.

    A line is named by its first point, its last point and the point halfway along its
    length, each rounded to `grid`. Rounding keeps a last-bit difference in the arithmetic
    that made the line from renaming it; the halfway point tells apart two lines that
    share their ends. Measured along the length, it is the same point however the line
    is sampled, so ways chained into one line with their joints repeated are named as
    the line drawn whole.

    Args:
        pts: The line, `(n, 2)`.
        grid: The cell the points are rounded to, in the line's own units.

    Returns:
        Two 64-bit words.
    """
    p = np.asarray(pts, dtype=np.float64).reshape(-1, 2)
    if not len(p):
        return (0, 0)
    run = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(p, axis=0).T))])
    half = [np.interp(run[-1] / 2, run, p[:, k]) for k in (0, 1)]
    words = np.rint(np.concatenate([p[0], p[-1], half]) / max(grid, 1e-12)).astype("<i8")
    digest = hashlib.blake2b(words.tobytes(), digest_size=16).digest()
    return (int.from_bytes(digest[:8], "little"), int.from_bytes(digest[8:], "little"))


def uniform_at(seed: int, index: npt.ArrayLike) -> np.ndarray:
    """One uniform draw per index, each a pure function of the seed and its own index.

    Splitmix64 of the seed and the index, so a field's draw at one place does not depend
    on how many other places were drawn, or in what order.

    Args:
        seed: The consumer's seed.
        index: Non-negative integer indices, any shape.

    Returns:
        Float64 draws in the open interval 0 to 1, the shape of `index`.
    """
    with np.errstate(over="ignore"):
        z = np.asarray(index).astype(np.uint64) * _GOLDEN + np.uint64(_word(seed))
        z = (z ^ (z >> np.uint64(30))) * _MIX_1
        z = (z ^ (z >> np.uint64(27))) * _MIX_2
        z ^= z >> np.uint64(31)
    return ((z >> np.uint64(11)).astype(np.float64) + 0.5) * _ULP
