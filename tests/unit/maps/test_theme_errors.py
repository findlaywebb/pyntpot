"""A theme problem reads as one located line, and a theme error holds every problem in order."""

from pathlib import Path

import pytest

from pyntpot.maps.theme_errors import ThemeError, ThemeProblem


def _problem(*, path: str = "t.yaml", key: str = "", line: int | None = None) -> ThemeProblem:
    """Build a problem with the message `bad`."""
    return ThemeProblem(path=Path(path), key=key, line=line, message="bad")


class TestAProblemReadsAsOneLine:
    """`str(ThemeProblem)` names the file, then the line and the key when it has them."""

    def test_line_and_key(self) -> None:
        """A problem with a line and a key reads `path:line: key: message`."""
        assert str(_problem(key="wash.blooms", line=3)) == "t.yaml:3: wash.blooms: bad"

    def test_line_only(self) -> None:
        """A problem with a line and no key drops the key."""
        assert str(_problem(line=3)) == "t.yaml:3: bad"

    def test_key_only(self) -> None:
        """A problem with a key and no line drops the line."""
        assert str(_problem(key="wash.blooms")) == "t.yaml: wash.blooms: bad"

    def test_neither(self) -> None:
        """A problem with no key and no line names only the file."""
        assert str(_problem()) == "t.yaml: bad"


class TestAnErrorHoldsEveryProblem:
    """`ThemeError` sorts its problems by file, line and key, and says each on its own line."""

    def test_problems_come_back_sorted(self) -> None:
        """Problems given out of order come back sorted by file, then line, then key."""
        given = [
            _problem(path="u.yaml", line=1),
            _problem(key="wash.blooms", line=4),
            _problem(key="card", line=2),
            _problem(key="b", line=None),
            _problem(key="a", line=2),
        ]
        error = ThemeError(given)
        assert error.problems == (
            _problem(key="b", line=None),
            _problem(key="a", line=2),
            _problem(key="card", line=2),
            _problem(key="wash.blooms", line=4),
            _problem(path="u.yaml", line=1),
        )

    def test_message_is_one_line_per_problem_in_order(self) -> None:
        """The error's message is each problem's text, one per line, in sorted order."""
        error = ThemeError([_problem(key="wash", line=5), _problem(key="card", line=2)])
        assert str(error) == "t.yaml:2: card: bad\nt.yaml:5: wash: bad"

    def test_no_problems_is_a_programming_error(self) -> None:
        """An error with no problems is refused with a `ValueError` naming why."""
        with pytest.raises(ValueError, match=r"^a theme error needs a problem$"):
            ThemeError(())

    def test_is_a_value_error(self) -> None:
        """A theme error is caught by `except ValueError`."""
        assert isinstance(ThemeError([_problem()]), ValueError)
