"""Small land-cover patches folded into the ground around them, on the label raster.

Key names: `patches`, the four-connected patches of one class on a label raster with their
sizes; `merge_small_patches`, which relabels every patch smaller than a floor with the class
of its largest labelled neighbour, and keeps one that nothing labelled touches.

A card seen small reads a scatter of little fields and copses in contrasting greens as
noise. Folding them in leaves the large shapes and their own outlines as they were. It
works on pixels, after the outlines are deformed and filled, so it takes no draw from the
deform generator and moves no basemap ring. It does not touch unlabelled pixels (paper and
water stay what they are), and a floor of zero changes nothing.
"""

import numpy as np


def _runs(label: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Every horizontal run of one class: its row, first column and end column (exclusive)."""
    h, w = label.shape
    change = np.ones((h, w), dtype=bool)
    change[:, 1:] = label[:, 1:] != label[:, :-1]
    rows, starts = np.nonzero(change)
    ends = np.empty_like(starts)
    ends[:-1] = starts[1:]
    last = np.r_[rows[1:] != rows[:-1], True]
    ends[last] = w
    return rows, starts, ends


def _find(parent: list[int], i: int) -> int:
    """The root of `i`, halving the path on the way."""
    node: int = i
    while parent[node] != node:
        parent[node] = parent[parent[node]]
        node = int(parent[node])
    return node


def patches(label: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The four-connected patches of a label raster and the size of each.

    Patches are found on the raster's horizontal runs: two runs of one class on adjacent
    rows that overlap by a column are one patch.

    Args:
        label: One class index per pixel, 0 where there is no cover.

    Returns:
        A patch id per pixel (the index of the patch's first run in row order, so ids are
        repeatable), and the pixel count and the class of each patch, indexed by id.
    """
    rows, starts, ends = _runs(label)
    classes = label[rows, starts].tolist()
    row_first = np.searchsorted(rows, np.arange(label.shape[0] + 1)).tolist()
    starts_l, ends_l = starts.tolist(), ends.tolist()
    parent = list(range(len(classes)))
    for r in range(label.shape[0] - 1):
        a, a_end = row_first[r], row_first[r + 1]
        b, b_end = a_end, row_first[r + 2]
        while a < a_end and b < b_end:
            if classes[a] == classes[b] and starts_l[a] < ends_l[b] and starts_l[b] < ends_l[a]:
                ra, rb = _find(parent, a), _find(parent, b)
                if ra != rb:
                    parent[max(ra, rb)] = min(ra, rb)
            if ends_l[a] <= ends_l[b]:
                a += 1
            else:
                b += 1
    roots = np.array([_find(parent, i) for i in range(len(parent))], dtype=np.int64)
    sizes = np.bincount(roots, weights=ends - starts, minlength=len(parent)).astype(np.int64)

    lengths = (ends - starts).astype(np.int64)
    ids = np.repeat(roots, lengths).reshape(label.shape)
    return ids, sizes, np.asarray(classes, dtype=label.dtype)


def merge_small_patches(label: np.ndarray, min_px: float) -> np.ndarray:
    """Relabel each labelled patch smaller than `min_px` pixels with its largest neighbour's class.

    A patch is four-connected pixels of one class. Its neighbours are the labelled patches it
    shares an edge with; it takes the class of the one with the most pixels, ties going to
    the lower class index. A patch that touches only unlabelled pixels is kept: an island's
    wood in a lake is the only ground there, and paper in its place would read as a hole. One
    pass: a small patch whose largest neighbour is another small patch takes that patch's
    class as it was before the pass.

    Args:
        label: One class index per pixel, 0 where there is no cover.
        min_px: The smallest patch kept as it is, in pixels. Zero or less keeps everything.

    Returns:
        A new label raster; `label` is not changed.
    """
    out = label.copy()
    if min_px <= 0 or not label.any():
        return out
    ids, sizes, classes = patches(label)
    is_small = (sizes < min_px) & (classes > 0)
    small = is_small[ids]
    if not small.any():
        return out
    pairs = (
        (ids[:, :-1], ids[:, 1:]),
        (ids[:, 1:], ids[:, :-1]),
        (ids[:-1, :], ids[1:, :]),
        (ids[1:, :], ids[:-1, :]),
    )
    patch = np.concatenate([a.ravel() for a, _ in pairs])
    other = np.concatenate([b.ravel() for _, b in pairs])
    keep = (patch != other) & is_small[patch] & (classes[other] > 0)
    patch, other = patch[keep], other[keep]
    target = classes.copy()
    if patch.size:
        # Sorted by patch, then neighbour size, then class falling: the last row of a patch
        # is its largest neighbour, the lower class on a tie.
        order = np.lexsort((-classes[other].astype(np.int64), sizes[other], patch))
        patch, other = patch[order], other[order]
        last = np.r_[patch[1:] != patch[:-1], True]
        target[patch[last]] = classes[other[last]]
    out[small] = target[ids[small]]
    return out
