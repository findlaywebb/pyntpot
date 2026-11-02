# The prerelease job fails in pytest-benchmark under the newest pytest

GitHub issue: [#94](https://github.com/findlaywebb/pyntpot/issues/94)

Area: tests (CI).

The `prerelease` job in `.github/workflows/ci.yml` runs the suite on Python 3.15 with its test
plugins installed unpinned (`uv pip install pytest hypothesis pytest-randomly
pytest-benchmark`), and is `continue-on-error`. It passed on `main` at `5904c44` on
2026-10-27 at 19:47 UTC and failed on the same commit at 22:19 UTC
(run 40593933929): every test passed, and all 18 benchmarks errored in set-up with

```
pytest_benchmark/fixture.py:88: self.fullname = node._nodeid
AttributeError: 'Function' object has no attribute '_nodeid'
```

So a pytest release between the two runs dropped the private `_nodeid` that pytest-benchmark
reads. The locked dev group (`uv.lock`) is not affected; only the job that tracks the newest
releases is.

Possible fix: wait for a pytest-benchmark release that reads `nodeid`, or have the job
deselect benchmarks (`-m "not golden and not benchmark"`) until one exists. Pinning pytest
there would defeat the job's purpose.
