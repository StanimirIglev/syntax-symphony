# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.1] - 2026-09-02

### Added

- `pytest-cov` dev dependency with branch coverage reporting enabled for all test runs.
- Minimum coverage gate (`fail_under = 85`) in `[tool.coverage.report]`; pytest `addopts` run coverage on `syntax_symphony` by default.

## [0.4.0] - 2026-09-02

### Added

- `__version__` on the top-level `syntax_symphony` package, sourced from package metadata via `importlib.metadata.version`.

### Fixed

- CLI `--min-depth` default aligned with the API (`0`); previously the CLI defaulted to `1`.
- Typo in `DT.__getitem__` error message (`Unexpanded`).

### Changed

- `SyntaxSymphony.remaining_k_paths()` now uses an O(1) counter instead of materializing all paths on each call.

### Removed

- Legacy `convert_paths_to_trees` method (unused).

## [0.3.0] - 2026-09-02

### Added

- `seed` parameter on `SyntaxSymphony` for reproducible fuzzing runs via a private `random.Random` instance (does not affect global random state).
- `--seed` CLI flag for reproducible `ssfuzz` output.
- Comprehensive fuzzer unit tests: k-path computation (k=1,2,3), cost/biased-grammar logic, coverage tracking, min/max depth behaviour, seed reproducibility, and edge cases (terminal-only and recursive grammars).
- Shared grammar fixtures in `tests/conftest.py`.

## [0.2.1] - 2026-09-02

### Fixed

- Replace `assert`-based constructor validation in `Grammar` and `DT.from_dict` with explicit `ValueError` / `TypeError` raises, so invariants are enforced under `python -O` / `PYTHONOPTIMIZE`.
- Replace internal `assert` in `SyntaxSymphony._k_path_to_tree` with an explicit `RuntimeError`.

### Changed

- Remove redundant `AssertionError` handler from the CLI; grammar validation errors are now raised as `ValueError` or `TypeError`.

## [0.2.0] - 2026-09-02

### Added

- Stable public API via top-level re-exports in `syntax_symphony.__init__`: `Grammar`, `SyntaxSymphony`, `DT`, and `load_grammar_from_file`.
- `py.typed` marker (PEP 561) so type checkers recognize the package as typed.
- Public API surface tests in `tests/test_public_api.py`.

### Changed

- README and `examples/example_api.py` now use top-level imports (`from syntax_symphony import ...`). Submodule imports remain supported.

## [0.1.6] - 2026-09-02

### Added

- CI workflow (`.github/workflows/ci.yml`) running ruff, mypy, and pytest on push via uv.
- Dev dependency group with pytest, ruff, mypy, build, and twine (`pyproject.toml`, `uv.lock`).
- Ruff and mypy configuration in `pyproject.toml`.

### Changed

- Publish workflow now runs only on version tags (`v*`), gates build on quality checks, and validates artifacts with `twine check`.
- Migrated local development and CI to uv.
- Minimum supported Python version raised to 3.12.
- Removed redundant `setup.py`; `pyproject.toml` is the single packaging source of truth.
- Stricter ruff and mypy (`strict = true`) configuration.

### Removed

- `setup.py` and `[project.optional-dependencies]` in favor of uv `[dependency-groups]`.
- `requirements.txt`; runtime dependencies are declared in `pyproject.toml`.

## [0.1.5] - 2026-09-01

### Security

- Replace `eval()` with JSON parsing in the CLI to prevent arbitrary code execution from grammar files.

### Added

- `load_grammar_from_file()` helper in `grammar.py` for safe JSON grammar loading.
- CLI error handling with clear stderr messages for missing files, invalid JSON, schema errors, and invalid start symbols.
- CLI and grammar-loading tests in `tests/test_cli.py`.

### Changed

- Grammar files must be valid JSON; Python expression syntax in grammar files is no longer supported.
