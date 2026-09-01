# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.5] - 2026-09-01

### Security

- Replace `eval()` with JSON parsing in the CLI to prevent arbitrary code execution from grammar files.

### Added

- `load_grammar_from_file()` helper in `grammar.py` for safe JSON grammar loading.
- CLI error handling with clear stderr messages for missing files, invalid JSON, schema errors, and invalid start symbols.
- CLI and grammar-loading tests in `tests/test_cli.py`.

### Changed

- Grammar files must be valid JSON; Python expression syntax in grammar files is no longer supported.
