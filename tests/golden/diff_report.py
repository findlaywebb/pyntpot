"""The golden diff summary: one JSON record of every changed image, and its Markdown.

Key types: `FileDiff`, one image's status, measurement and review-image paths; `Summary`,
what was compared and every `FileDiff`, in path order. `Summary.to_json` and
`Summary.from_json` are the machine-readable form `diff_images.py` writes as
`summary.json`; `markdown` renders a summary as the Markdown a PR body or `summary.md`
holds, with the image links a caller's `link` makes from each review image's path. Each
review image is an HTML `<img>` tag on its own line between blank lines, not Markdown image
syntax, which the GitHub MCP tools mangle when they post a PR body; the diff image is shown
`width` pixels wide, the crop image at its natural size, so its pixels stay whole.

Statuses: `changed` (both sides hold the image and some pixel differs), `added` (only the
later side holds it), `removed` (only the earlier side). An image whose pixels are equal is
not in a summary, whatever its bytes. Review-image paths are relative to the output
directory, with `/` separators.

It does not measure, draw, or read or write files.
"""

import html
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from golden.diff_measure import Measurement

from support.golden import MAX_CHANNEL_DELTA, MAX_DIFFERING_FRACTION

Status = Literal["changed", "added", "removed"]
_STATUSES: tuple[Status, ...] = ("changed", "added", "removed")

#: A PR body shows each image's review images open up to this many changed images.
OPEN_LIMIT = 6

#: A PR body shows each diff image this many pixels wide.
DIFF_WIDTH = 720


@dataclass(frozen=True)
class FileDiff:
    """One image's difference between the two sides.

    Attributes:
        path: The image's path relative to the compared roots, with `/` separators.
        status: `changed`, `added` or `removed`.
        measurement: How it changed; `None` unless `changed`.
        diff_image: The diff image's path under the output directory, if drawn.
        crop_image: The crop image's path under the output directory, if drawn.
    """

    path: str
    status: Status
    measurement: Measurement | None = None
    diff_image: str | None = None
    crop_image: str | None = None


@dataclass(frozen=True)
class Summary:
    """What was compared, and how each image that differs changed.

    Attributes:
        before: A label for the earlier side (a directory or a git ref).
        after: A label for the later side.
        files: Every image that differs, in path order.
    """

    before: str
    after: str
    files: tuple[FileDiff, ...]

    def to_json(self) -> str:
        """Return the summary as indented JSON, the bounds it was measured with included."""
        record = {
            "before": self.before,
            "after": self.after,
            "channel_delta": MAX_CHANNEL_DELTA,
            "max_differing_fraction": MAX_DIFFERING_FRACTION,
            "files": [_file_record(diff) for diff in self.files],
        }
        return json.dumps(record, indent=2) + "\n"

    @classmethod
    def from_json(cls, text: str) -> "Summary":
        """Return the summary `to_json` wrote."""
        record = json.loads(text)
        files = tuple(_file_diff(item) for item in record["files"])
        return cls(before=str(record["before"]), after=str(record["after"]), files=files)


def _file_record(diff: FileDiff) -> dict[str, object]:
    """Return one image's JSON record."""
    record: dict[str, object] = {"path": diff.path, "status": diff.status}
    found = diff.measurement
    if found is not None:
        record |= {
            "width": found.width,
            "height": found.height,
            "changed_fraction": found.changed_fraction,
            "over_bound": found.changed_fraction > MAX_DIFFERING_FRACTION,
            "max_delta": found.max_delta,
            "box": None if found.box is None else list(found.box),
            "extent": found.extent,
        }
    return record | {"diff_image": diff.diff_image, "crop_image": diff.crop_image}


def _file_diff(record: dict[str, object]) -> FileDiff:
    """Return the `FileDiff` a `_file_record` record holds."""
    measurement = None
    if "changed_fraction" in record:
        box = record["box"]
        max_delta = record["max_delta"]
        measurement = Measurement(
            width=int(str(record["width"])),
            height=int(str(record["height"])),
            changed_fraction=float(str(record["changed_fraction"])),
            max_delta=None if max_delta is None else int(str(max_delta)),
            box=None if not isinstance(box, list) else (box[0], box[1], box[2], box[3]),
            extent="local" if record["extent"] == "local" else "widespread",
        )
    status = next((known for known in _STATUSES if known == record["status"]), None)
    if status is None:
        raise ValueError(f"unknown status {record['status']!r} for {record['path']}")
    diff_image, crop_image = record["diff_image"], record["crop_image"]
    return FileDiff(
        path=str(record["path"]),
        status=status,
        measurement=measurement,
        diff_image=None if diff_image is None else str(diff_image),
        crop_image=None if crop_image is None else str(crop_image),
    )


def table_row(diff: FileDiff) -> str:
    """Return one image's Markdown table row; an added or removed image's status fills Changed."""
    found = diff.measurement
    if found is None:
        return f"| `{diff.path}` | | {diff.status} | | | |"
    if found.shape_differs:
        return f"| `{diff.path}` | {found.width}x{found.height} | 1.000000 (size differs) | | | widespread |"
    fraction = f"{found.changed_fraction:.6f}"
    if found.changed_fraction > MAX_DIFFERING_FRACTION:
        fraction += f" (over {MAX_DIFFERING_FRACTION})"
    left, top, right, bottom = found.box or (0, 0, 0, 0)
    return (
        f"| `{diff.path}` | {found.width}x{found.height} | {fraction} | {found.max_delta} "
        f"| {left},{top} to {right},{bottom} | {found.extent} |"
    )


def _counts(files: tuple[FileDiff, ...]) -> str:
    """Return how many images changed, were added and were removed, in words."""
    counted = {status: sum(diff.status == status for diff in files) for status in _STATUSES}
    return ", ".join(f"{n} {status}" for status, n in counted.items())


def image_tag(src: str, alt: str, width: int | None = None) -> str:
    """Return an HTML `<img>` tag; with `width` it is shown that many pixels wide.

    Both attributes are HTML-escaped, so a quote in a path cannot end one early.
    """
    sized = "" if width is None else f' width="{width}"'
    return f'<img src="{html.escape(src)}" alt="{html.escape(alt)}"{sized}>'


def _review_images(
    diff: FileDiff, link: Callable[[str], str], *, opened: bool, width: int
) -> list[str]:
    """Return one changed image's collapsible block of review images, each tag on its own line."""
    found = diff.measurement
    extent = "" if found is None else f": {found.extent}, {found.changed_fraction:.6f}"
    lines = [
        "<details open>" if opened else "<details>",
        f"<summary><code>{diff.path}</code>{extent}</summary>",
        "",
    ]
    if diff.diff_image is not None:
        alt = f"{diff.path}: before, after and difference"
        lines += [image_tag(link(diff.diff_image), alt, width), ""]
    if diff.crop_image is not None:
        alt = f"{diff.path}: the most-changed region, close up"
        lines += [image_tag(link(diff.crop_image), alt), ""]
    return [*lines, "</details>", ""]


def markdown(summary: Summary, link: Callable[[str], str], width: int = DIFF_WIDTH) -> str:
    """Return the summary as Markdown: a heading, a table, then each changed image's review images.

    Args:
        summary: The summary to render.
        link: Turns a review image's path under the output directory into the link the
            Markdown shows (a relative path for `summary.md`, a URL for a PR body).
        width: How many pixels wide each diff image is shown; crop images keep their size.

    Returns:
        The Markdown, ending in a newline.
    """
    lines = [
        "### Image changes",
        "",
        f"Before: `{summary.before}`. After: `{summary.after}`. {_counts(summary.files)}.",
        (
            f"Changed counts the pixels past channel delta {MAX_CHANNEL_DELTA}; the parity gate "
            f"bounds it at {MAX_DIFFERING_FRACTION} (ADR 0030). Local: the box covers at most a "
            "quarter of the image."
        ),
        "",
    ]
    if not summary.files:
        return "\n".join([*lines, "No image differs.", ""])
    lines += [
        "| File | Size | Changed | Max delta | Box | Extent |",
        "|---|---|---|---|---|---|",
        *(table_row(diff) for diff in summary.files),
        "",
    ]
    shown = [diff for diff in summary.files if diff.diff_image is not None]
    for diff in shown:
        lines += _review_images(diff, link, opened=len(shown) <= OPEN_LIMIT, width=width)
    return "\n".join(lines)
