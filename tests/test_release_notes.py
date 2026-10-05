from pathlib import Path

import pytest
from extract_release_notes import extract_release_notes, tag_to_version

SAMPLE_CHANGELOG = """\
# Changelog

## [0.4.2] - 2026-09-02

### Added

- First item

## [0.4.1] - 2026-09-02

### Fixed

- Older item

## [0.4.0] - 2026-09-02

### Added

- Oldest item
"""


@pytest.fixture
def sample_changelog(tmp_path: Path) -> Path:
    path = tmp_path / "CHANGELOG.md"
    path.write_text(SAMPLE_CHANGELOG, encoding="utf-8")
    return path


@pytest.mark.parametrize("tag", ["v0.4.2", "0.4.2"], ids=["prefixed", "unprefixed"])
def test_tag_to_version(tag: str) -> None:
    assert tag_to_version(tag) == "0.4.2"


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("0.4.2", "### Added\n\n- First item"),
        ("0.4.1", "### Fixed\n\n- Older item"),
        ("0.4.0", "### Added\n\n- Oldest item"),
    ],
    ids=["first", "middle", "last"],
)
def test_extracts_section(sample_changelog: Path, version: str, expected: str) -> None:
    assert extract_release_notes(sample_changelog, version) == expected


def test_missing_version_raises(sample_changelog: Path) -> None:
    with pytest.raises(ValueError, match="No CHANGELOG section found"):
        extract_release_notes(sample_changelog, "9.9.9")


def test_empty_section_raises(tmp_path: Path) -> None:
    path = tmp_path / "CHANGELOG.md"
    path.write_text(
        "## [0.1.0] - 2026-01-01\n\n## [0.0.1] - 2025-12-01\n\n### Added\n\n- x\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="is empty"):
        extract_release_notes(path, "0.1.0")


def test_duplicate_version_raises(tmp_path: Path) -> None:
    path = tmp_path / "CHANGELOG.md"
    path.write_text(
        "## [0.1.0] - 2026-01-01\n\n### Added\n\n- one\n\n"
        "## [0.1.0] - 2026-01-02\n\n### Fixed\n\n- two\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="multiple sections"):
        extract_release_notes(path, "0.1.0")
