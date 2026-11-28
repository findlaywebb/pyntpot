"""Tests for the output-hash tool's stem selection and comparison, on hand-written mappings."""

import pytest
from golden.output_hashes import compare, main, select

from support.docs_images import IMAGES

SAME = {"file": "a", "pixels": "b"}
OTHER = {"file": "c", "pixels": "d"}


class TestSelect:
    """Which registry entries a `--stem` selection measures."""

    def test_no_stems_selects_every_entry(self) -> None:
        """No stem named selects the whole registry, in registry order."""
        assert select(None) == list(IMAGES)

    def test_a_stem_selects_only_its_entries(self) -> None:
        """A named stem selects every entry of that stem and no other."""
        picked = select(["tutorial_grids"])
        assert picked
        assert {entry.stem for entry in picked} == {"tutorial_grids"}

    def test_an_unknown_stem_is_refused(self) -> None:
        """A stem the registry does not hold raises ValueError naming it."""
        with pytest.raises(ValueError, match="no_such_stem"):
            select(["no_such_stem"])

    def test_main_refuses_an_unknown_stem_before_painting(self) -> None:
        """An unknown `--stem` is an argparse error, exit status 2."""
        with pytest.raises(SystemExit) as raised:
            main(["check", "unused.json", "--stem", "no_such_stem"])
        assert raised.value.code == 2


class TestCompare:
    """What a check reports for recorded and measured hashes."""

    def test_a_narrowed_check_ignores_other_stems_recorded_entries(self) -> None:
        """A recorded entry outside the selection is neither measured nor reported."""
        expected = {"a.webp": SAME, "z.webp": OTHER}
        assert compare(expected, {"a.webp": SAME}, selected={"a.webp"}) == {"a.webp": "identical"}

    def test_a_missing_selected_entry_is_reported(self) -> None:
        """A selected entry absent from the record is reported as not recorded."""
        found = compare({"z.webp": OTHER}, {"a.webp": SAME}, selected={"a.webp"})
        assert found == {"a.webp": "not recorded"}

    def test_a_changed_selected_entry_is_reported(self) -> None:
        """A selected entry whose hashes differ is reported as different."""
        found = compare({"a.webp": OTHER}, {"a.webp": SAME}, selected={"a.webp"})
        assert found == {"a.webp": "DIFFERENT"}

    def test_a_full_check_reports_a_recorded_entry_that_is_gone(self) -> None:
        """Without a selection, a recorded entry nothing measures is reported."""
        found = compare({"a.webp": SAME, "gone.webp": OTHER}, {"a.webp": SAME}, selected=None)
        assert found == {"a.webp": "identical", "gone.webp": "recorded but no longer an entry"}

    def test_a_full_check_reports_an_unrecorded_entry(self) -> None:
        """Without a selection, a measured entry missing from the record is reported."""
        found = compare({}, {"a.webp": SAME}, selected=None)
        assert found == {"a.webp": "not recorded"}
