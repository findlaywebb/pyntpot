"""Every image caption on the site says what its registered script run paints.

A caption is the `*Painted by `examples/<stem>.py`...*` paragraph that follows an image
after one blank line, on any site page; it runs to its next blank line, past the closing
`*`. Each caption names the script the image registry gives for its image, the figure and
theme the registry passes, label lists the script holds as one tuple literal, and a name
the script writes. Facts come from `support.docs_images.IMAGES` and the scripts' ASTs, so
a new page, caption or registry entry is covered with no test edit.
"""

import ast
import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from support import REPO_ROOT
from support.docs_images import IMAGES, DocsImage
from support.site_pages import DOCS, prose, resolve, site_pages

_IMAGE = re.compile(r"^!\[[^\]]*\]\(\s*<?(?P<href>[^)\s>]+)>?\s*\)\s*$")
_PAINTED_BY = re.compile(r"^\*Painted by `examples/(?P<stem>[\w-]+)\.py`")
_LABELS = re.compile(r"The labels read (?P<sentence>.*?)(?:\.(?=\s|\*|$)|$)", re.DOTALL)
_NAME = re.compile(r"The name is (?P<name>[^.;*]+)")
_CLAUSE_END = re.compile(r"\b(?:across|down)\b")
_RANGE = re.compile(r"\bto\b")
_NUMBER = re.compile(r"(?<![\w.-])-?\d+(?:\.\d+)?(?![\w-])")


@dataclass(frozen=True)
class Caption:
    """One captioned image: its page, its path under `docs/images/`, the caption's script stem and its whole paragraph."""

    page: Path
    image: str
    stem: str
    text: str

    def where(self) -> str:
        """Return the page and image, for a failure message."""
        return f"{self.page.relative_to(DOCS)}: {self.image}"


def _captions_of(page: Path) -> list[Caption]:
    """Return every captioned image on one page, in page order."""
    lines = prose(page.read_text()).splitlines()
    images = DOCS / "images"
    found: list[Caption] = []
    for index, line in enumerate(lines[:-2]):
        image = _IMAGE.match(line.strip())
        painted = _PAINTED_BY.match(lines[index + 2].strip())
        if image is None or painted is None or lines[index + 1].strip():
            continue
        target = resolve(page, image["href"])
        if target is None or not target.is_relative_to(images):
            continue
        paragraph: list[str] = []
        for following in lines[index + 2 :]:
            if not following.strip():
                break
            paragraph.append(following.strip())
        found.append(
            Caption(
                page, target.relative_to(images).as_posix(), painted["stem"], " ".join(paragraph)
            )
        )
    return found


@cache
def _captions() -> tuple[Caption, ...]:
    """Return every captioned image on every site page."""
    return tuple(caption for page in site_pages() for caption in _captions_of(page))


def _entries(image: str) -> list[DocsImage]:
    """Return the registry entries that paint `image`."""
    return [entry for entry in IMAGES if entry.image == image]


@cache
def _script(stem: str) -> ast.Module:
    """Return the parsed source of `examples/<stem>.py`."""
    return ast.parse((REPO_ROOT / "examples" / f"{stem}.py").read_text())


def _number(node: ast.expr) -> float | None:
    """Return a numeric constant's value, unary minus included; `None` for anything else."""
    sign = 1.0
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        sign, node = -1.0, node.operand
    if isinstance(node, ast.Constant):
        value = node.value
        if isinstance(value, int | float) and not isinstance(value, bool):
            return sign * float(value)
    return None


@cache
def _numeric_literals(stem: str) -> tuple[tuple[float, ...], ...]:
    """Return every tuple or list literal of a script whose elements are all numeric constants."""
    found: list[tuple[float, ...]] = []
    for node in ast.walk(_script(stem)):
        if isinstance(node, ast.Tuple | ast.List) and node.elts:
            values = [_number(element) for element in node.elts]
            if all(value is not None for value in values):
                found.append(tuple(value for value in values if value is not None))
    return tuple(found)


def _strings(stem: str) -> set[str]:
    """Return every string literal of a script."""
    return {
        node.value
        for node in ast.walk(_script(stem))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }


def _label_clauses(text: str) -> list[str]:
    """Return the clauses of a caption's label sentence, each ending in `across` or `down`."""
    sentence = _LABELS.search(text)
    if sentence is None:
        return []
    clauses: list[str] = []
    start = 0
    body = sentence["sentence"]
    for end in _CLAUSE_END.finditer(body):
        clauses.append(body[start : end.end()])
        start = end.end()
    return clauses


def test_the_caption_reader_finds_captions_on_the_site() -> None:
    """The caption reader finds the gallery's captions, so the checks below are not vacuous."""
    assert any(caption.page.name == "gallery.md" for caption in _captions())


def test_label_clauses_split_at_across_and_down_and_skip_decimal_points() -> None:
    """A label sentence splits into its across and down clauses, and the point of 0.52 does not end it."""
    text = "*Painted by x. The labels read -38, 0 and 90 across, and 0, 0.52 and 0.85 down, y.*"
    assert _label_clauses(text) == ["-38, 0 and 90 across", ", and 0, 0.52 and 0.85 down"]


def test_a_number_inside_a_word_is_not_a_label_number() -> None:
    """Brush keys such as RIV1-a hold no label numbers; free-standing and negative numbers count."""
    assert _NUMBER.findall("RIV1-a, MAJ3-b and 3 px, -38 and 0.5") == ["3", "-38", "0.5"]


def test_every_caption_names_the_script_that_paints_its_image() -> None:
    """Each captioned image is registered, and its caption names the script a registry entry runs."""
    wrong = [
        f"{caption.where()}: caption names {caption.stem}, registry has "
        f"{sorted({entry.stem for entry in _entries(caption.image)}) or 'no entry'}"
        for caption in _captions()
        if caption.stem not in {entry.stem for entry in _entries(caption.image)}
    ]
    assert not wrong, "\n".join(wrong)


def _names_figure_and_theme(caption: Caption, entry: DocsImage) -> bool:
    """Return whether a caption names the figure and theme one registry entry passes its script."""
    options = dict(entry.options)
    figure, theme = options.get("figure"), options.get("theme")
    if figure is not None and not (
        f"figure {figure}" in caption.text or f'figure="{figure}"' in caption.text
    ):
        return False
    return theme is None or str(theme) in caption.text


def test_every_caption_names_its_figure_and_theme() -> None:
    """A caption names the figure and the theme its image's registry entry passes, when it passes them."""
    wrong = [
        f"{caption.where()}: caption does not name the figure or theme of "
        f"{[dict(entry.options) for entry in _entries(caption.image)]}"
        for caption in _captions()
        if _entries(caption.image)
        and not any(_names_figure_and_theme(caption, entry) for entry in _entries(caption.image))
    ]
    assert not wrong, "\n".join(wrong)


def test_every_label_list_in_a_caption_is_a_tuple_of_its_script() -> None:
    """Each across or down list of two or more numbers equals, in order, one numeric tuple literal of the caption's script."""
    wrong: list[str] = []
    for caption in _captions():
        for clause in _label_clauses(caption.text):
            numbers = tuple(float(number) for number in _NUMBER.findall(clause))
            if len(numbers) < 2 or _RANGE.search(clause):
                continue
            if numbers not in _numeric_literals(caption.stem):
                wrong.append(
                    f"{caption.where()}: {list(numbers)} is no tuple of examples/{caption.stem}.py"
                )
    assert not wrong, "\n".join(wrong)


def test_every_name_in_a_caption_is_written_by_its_script() -> None:
    """The name after "The name is" is a string literal of the caption's script."""
    wrong = [
        f"{caption.where()}: {found['name'].strip()!r} is not a string of examples/{caption.stem}.py"
        for caption in _captions()
        if (found := _NAME.search(caption.text)) is not None
        and found["name"].strip() not in _strings(caption.stem)
    ]
    assert not wrong, "\n".join(wrong)
