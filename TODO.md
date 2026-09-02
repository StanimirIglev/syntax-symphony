# TODO

## CI

- [ ] Add a pytest step with `PYTHONOPTIMIZE=1` (or `python -O`) to CI and the publish workflow, so validation cannot regress to `assert`-based checks that are stripped in optimized mode.
