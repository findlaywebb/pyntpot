"""Benchmarks for the painting engine, the hand and the map pipeline.

CodSpeed times them in CI; locally `uv run pytest -m benchmark --benchmark-enable`
times them. A plain run calls each benchmark once, untimed, as a smoke test. They
time code and assert nothing.
"""
