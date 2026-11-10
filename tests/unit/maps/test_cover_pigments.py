"""`CoverPigment`: the type, the default, Python-built values and the painter's transparency."""

import dataclasses
from pathlib import Path

import pydantic
import pytest

from pyntpot.ink import PIGMENT_REGISTRY, Colour
from pyntpot.maps import CoverPigment, Style
from pyntpot.maps.cover_pigment import built_in_transparency, default_pigments
from pyntpot.maps.style_groups import CoverStyle
from pyntpot.maps.theme_vocab import VOCABULARIES

from .painter.jobs import tiny_job, tiny_style
from support.theme_dump import dump_theme
from support.theme_files import write_theme

ROLES = ("farmland", "meadow", "orchard", "scrub", "heath", "sand", "rock", "wetland")

#: Each theme's transparency per cover class, in class order, measured on the tip before the
#: pigments carried their own (`paper.pigment_transparency`, else `km_transparency`).
CLASS_ORDER = [
    "farmland",
    "meadow",
    "orchard",
    "scrub",
    "heath",
    "sand",
    "rock",
    "wetland",
    "built",
    "works",
    "wood",
    "pale",
    "water",
    "relief",
    "rim",
]
OLD_TRANSPARENCIES = {
    "default": (
        0.1,
        0.09,
        0.09,
        0.08,
        0.14,
        0.16,
        0.22,
        0.08,
        0.26,
        0.28,
        0.05,
        0.12,
        0.04,
        0.3,
        0.18,
    ),
    "bold": (0.06, 0.05, 0.05, 0.05, 0.08, 0.1, 0.15, 0.05, 0.2, 0.2, 0.03, 0.07, 0.02, 0.2, 0.12),
    "pen-and-ink": (
        0.1,
        0.09,
        0.09,
        0.08,
        0.14,
        0.16,
        0.22,
        0.08,
        0.26,
        0.28,
        0.03,
        0.2,
        0.04,
        0.3,
        0.18,
    ),
    "sepia": (
        0.1,
        0.09,
        0.09,
        0.08,
        0.14,
        0.16,
        0.22,
        0.08,
        0.26,
        0.28,
        0.05,
        0.12,
        0.04,
        0.3,
        0.18,
    ),
    "winter": (
        0.1,
        0.09,
        0.09,
        0.08,
        0.14,
        0.16,
        0.22,
        0.08,
        0.26,
        0.28,
        0.05,
        0.12,
        0.04,
        0.3,
        0.18,
    ),
    "ambleside-hero": (
        0.1,
        0.09,
        0.09,
        0.08,
        0.14,
        0.16,
        0.22,
        0.08,
        0.26,
        0.28,
        0.05,
        0.12,
        0.04,
        0.3,
        0.18,
    ),
    "ambleside": (
        0.1,
        0.09,
        0.09,
        0.08,
        0.14,
        0.16,
        0.22,
        0.08,
        0.26,
        0.28,
        0.05,
        0.12,
        0.04,
        0.3,
        0.18,
    ),
    "oxford": (
        0.1,
        0.09,
        0.09,
        0.08,
        0.14,
        0.16,
        0.22,
        0.08,
        0.26,
        0.28,
        0.05,
        0.12,
        0.04,
        0.3,
        0.18,
    ),
    "skye": (
        0.1,
        0.09,
        0.09,
        0.08,
        0.14,
        0.16,
        0.22,
        0.08,
        0.26,
        0.28,
        0.05,
        0.12,
        0.04,
        0.3,
        0.18,
    ),
    "y-fenni": (
        0.1,
        0.09,
        0.09,
        0.08,
        0.14,
        0.16,
        0.22,
        0.08,
        0.26,
        0.28,
        0.05,
        0.12,
        0.04,
        0.3,
        0.18,
    ),
    "yr-wyddfa": (
        0.1,
        0.09,
        0.09,
        0.08,
        0.14,
        0.16,
        0.22,
        0.08,
        0.26,
        0.28,
        0.05,
        0.12,
        0.04,
        0.3,
        0.18,
    ),
}
EXAMPLES = Path(__file__).resolve().parents[3] / "examples" / "themes"


class TestTheDefault:
    """The default bindings are the registry's role pigments."""

    def test_every_cover_class_is_a_role_pigment_with_a_transparency(self) -> None:
        """Each of the 15 cover classes has a float built-in transparency, so a theme never reaches `None`."""
        classes = VOCABULARIES[("cover", "pigments")]
        assert len(classes) == 15
        for name in classes:
            assert isinstance(built_in_transparency(name), float), name

    def test_a_key_outside_the_cover_classes_has_no_built_in(self) -> None:
        """`built_in_transparency` is `None` for a name that is no cover class."""
        assert built_in_transparency("ultramarine") is None

    def test_the_default_bindings_are_the_registry_roles(self) -> None:
        """`default_pigments` is each role pigment's colour and transparency, in registry order."""
        roles = list(PIGMENT_REGISTRY.pigments)[:15]
        assert default_pigments() == {p.name: CoverPigment(p.colour, p.transparency) for p in roles}
        assert CoverStyle().pigments == default_pigments()

    def test_the_written_form_is_a_mapping_without_a_none_transparency(self) -> None:
        """`as_table` is `{pigment, transparency}`, the transparency left out when `None`."""
        assert CoverPigment(Colour("#112233"), 0.5).as_table() == {
            "pigment": "#112233",
            "transparency": 0.5,
        }
        assert CoverPigment(Colour("#112233"), None).as_table() == {"pigment": "#112233"}


class TestPythonBuilt:
    """What a caller building a `CoverStyle` in Python gets."""

    def test_a_python_str_takes_the_classes_built_in_transparency(self) -> None:
        """A `str` becomes a `CoverPigment` of the parsed colour and the class's own transparency."""
        style = dataclasses.replace(CoverStyle(), pigments={"relief": "#ABCDEF"})
        assert style.pigments["relief"] == CoverPigment(Colour("#abcdef"), 0.3)

    def test_a_python_colour_takes_the_classes_built_in_transparency(self) -> None:
        """A `Colour` takes the class's built-in transparency the same way."""
        style = dataclasses.replace(CoverStyle(), pigments={"rim": Colour("#abcdef")})
        assert style.pigments["rim"] == CoverPigment(Colour("#abcdef"), 0.18)

    def test_a_cover_pigment_keeps_its_transparency(self) -> None:
        """A `CoverPigment` keeps its transparency, its colour through `Colour.parse`."""
        upper = CoverPigment("#ABCDEF", 0.9)  # ty: ignore[invalid-argument-type]
        style = dataclasses.replace(CoverStyle(), pigments={"rim": upper})
        assert style.pigments["rim"] == CoverPigment(Colour("#abcdef"), 0.9)
        assert type(style.pigments["rim"].colour) is Colour

    def test_a_python_key_outside_the_cover_classes_takes_km_transparency(
        self, tmp_path: Path
    ) -> None:
        """A key that is no cover class has no built-in transparency, so `transp` reads `km_transparency`."""
        base = tiny_job(tmp_path).style
        style = base.model_copy(
            update={"cover": dataclasses.replace(base.cover, pigments={"ink": "#112233"})}
        )
        assert style.cover.pigments["ink"].transparency is None
        job = tiny_job(tmp_path, style)
        assert job.transp("ink") == style.paper.km_transparency

    def test_a_python_built_none_paints_at_km_transparency(self, tmp_path: Path) -> None:
        """`CoverPigment(colour, None)` is applied by `PaintJob.transp` at `paper.km_transparency`."""
        base = tiny_style()
        cover = dataclasses.replace(
            base.cover,
            pigments={**base.cover.pigments, "wood": CoverPigment(Colour("#112233"), None)},
        )
        style = base.model_copy(update={"cover": cover})
        job = tiny_job(tmp_path, style)
        assert job.transp("wood") == style.paper.km_transparency
        assert job.transp("water") == 0.04

    def test_transp_reads_the_entry_not_the_paper(self, tmp_path: Path) -> None:
        """`transp` is the entry's own transparency, whatever `km_transparency` is."""
        job = tiny_job(tmp_path, tiny_style())
        assert job.transp("relief") == 0.3

    def test_a_list_is_refused(self) -> None:
        """A list is no entry: it is refused rather than read as a pair."""
        with pytest.raises(ValueError, match="not a colour or a table"):
            CoverStyle(pigments={"rim": ["#abcdef", 0.1]})  # ty: ignore[invalid-argument-type]

    def test_model_validate_from_a_dict_builds_cover_pigments(self) -> None:
        """`Style.model_validate` accepts a mapping, a `CoverPigment` and a `str` for an entry."""
        style = Style.model_validate(
            {
                "cover": {
                    "pigments": {
                        "wood": {"pigment": "#112233", "transparency": 0.2},
                        "rim": CoverPigment(Colour("#445566"), 0.3),
                        "water": "#778899",
                        "relief": {"pigment": "#aabbcc"},
                    }
                }
            }
        )
        pigments = style.cover.pigments
        assert pigments["wood"] == CoverPigment(Colour("#112233"), 0.2)
        assert pigments["rim"] == CoverPigment(Colour("#445566"), 0.3)
        assert pigments["water"] == CoverPigment(Colour("#778899"), 0.04)
        assert pigments["relief"] == CoverPigment(Colour("#aabbcc"), None)

    def test_model_validate_refuses_a_list(self) -> None:
        """`Style.model_validate` refuses a list entry."""
        with pytest.raises(pydantic.ValidationError):
            Style.model_validate({"cover": {"pigments": {"wood": ["#112233", 0.2]}}})


class TestTheDumpedForm:
    """A style written by `theme_dump` loads back equal."""

    def test_the_dumped_form_loads_back(self, tmp_path: Path) -> None:
        """A `Style()` written as a theme table loads to an equal style, a `None` included."""
        import dataclasses as dc  # noqa: PLC0415

        style = Style()
        pigments = {**style.cover.pigments, "wood": CoverPigment(Colour("#112233"), None)}
        style = style.model_copy(update={"cover": dc.replace(style.cover, pigments=pigments)})
        table = {name: dc.asdict(getattr(style, name)) for name in Style.model_fields}
        for name, field in (("basemap", "line_effects"), ("route_ink", "effects")):
            del table[name][field]
        path = write_theme(tmp_path, "dumped.yaml", dump_theme(table))
        loaded = Style.from_yaml(path)
        assert loaded.cover.pigments["wood"] == CoverPigment(Colour("#112233"), 0.05)
        assert {k: v for k, v in loaded.cover.pigments.items() if k != "wood"} == {
            k: v for k, v in style.cover.pigments.items() if k != "wood"
        }


class TestEveryThemeKeepsItsLook:
    """Moving the transparency into the pigments moved no class's transparency."""

    @pytest.mark.parametrize("name", list(OLD_TRANSPARENCIES), ids=list(OLD_TRANSPARENCIES))
    def test_every_theme_keeps_its_old_class_transparencies(self, name: str) -> None:
        """Each theme's per-class transparency equals the table measured before the migration."""
        if name == "default":
            style = Style.default()
        elif (EXAMPLES / f"{name}.yaml").exists():
            style = Style.from_yaml(EXAMPLES / f"{name}.yaml")
        else:
            style = Style.named(name)
        got = tuple(style.cover.pigments[c].transparency for c in CLASS_ORDER)
        assert got == OLD_TRANSPARENCIES[name]
