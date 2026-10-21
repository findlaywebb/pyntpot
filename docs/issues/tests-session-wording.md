# Three test lines still say "session"

Area: tests (`maps`).

pyntpot's prose says track, box and map, not sport or activity words. P10.14 and
P10.19 reworded `src` and the lettering tests, but three lines in other test
modules still say "session":

- `tests/unit/maps/test_layers.py:40`, a `#:` comment: "the session never met it."
- `tests/unit/maps/test_layers.py:92`, a test docstring: "whatever the session did."
- `tests/unit/maps/test_track_index.py:32`, a test docstring: "part of the session
  however short the contact."

Possible fix: say "track" in each ("the track never met it", "whatever the track
did", "part of the track however short the contact"). Docstrings and comments
only; no test changes behaviour.
