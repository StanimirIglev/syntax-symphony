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


def test_tag_to_version_strips_v_prefix() -> None:
    assert tag_to_version("v0.4.2") == "0.4.2"


def test_tag_to_version_without_prefix() -> None:
    assert tag_to_version("0.4.2") == "0.4.2"


def test_extracts_first_section(sample_changelog: Path) -> None:
    notes = extract_release_notes(sample_changelog, "0.4.2")

    assert notes == "### Added\n\n- First item"
    assert "0.4.1" not in notes


def test_extracts_middle_section(sample_changelog: Path) -> None:
    notes = extract_release_notes(sample_changelog, "0.4.1")

    assert notes == "### Fixed\n\n- Older item"
    assert "0.4.2" not in notes
    assert "0.4.0" not in notes


def test_extracts_last_section(sample_changelog: Path) -> None:
    notes = extract_release_notes(sample_changelog, "0.4.0")

    assert notes == "### Added\n\n- Oldest item"


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


def test_extracts_from_project_changelog() -> None:
    changelog = Path(__file__).resolve().parents[1] / "CHANGELOG.md"

    notes = extract_release_notes(changelog, "0.4.2")

    assert "### Added" in notes
    assert "pre-commit" in notes.lower()
    assert "[0.4.1]" not in notes
