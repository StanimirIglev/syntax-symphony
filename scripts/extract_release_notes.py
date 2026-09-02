"""Extract a Keep a Changelog release section for GitHub Releases."""

from __future__ import annotations

import re
import sys
from pathlib import Path

SECTION_RE = re.compile(r"^## \[([^\]]+)\].*$", re.MULTILINE)


def tag_to_version(tag: str) -> str:
    """Strip a leading ``v`` from a git tag (``v0.4.2`` -> ``0.4.2``)."""
    if tag.startswith("v"):
        return tag[1:]
    return tag


def extract_release_notes(changelog: Path, version: str) -> str:
    """Return the body of the changelog section for ``version``.

    Args:
        changelog: Path to a Keep a Changelog formatted file.
        version: Semantic version without a leading ``v`` (e.g. ``0.4.2``).

    Returns:
        The section body (subsection headings and list items), without the
        ``## [version]`` header line.

    Raises:
        FileNotFoundError: If ``changelog`` does not exist.
        ValueError: If the version is missing, duplicated, or has an empty body.
    """
    text = changelog.read_text(encoding="utf-8")
    matches = list(SECTION_RE.finditer(text))

    section_starts: list[int] = []
    for match in matches:
        if match.group(1) != version:
            continue
        section_starts.append(match.end())

    if not section_starts:
        raise ValueError(f"No CHANGELOG section found for version {version!r}")

    if len(section_starts) > 1:
        raise ValueError(
            f"CHANGELOG contains multiple sections for version {version!r}"
        )

    start = section_starts[0]
    next_header = SECTION_RE.search(text, start)
    end = next_header.start() if next_header else len(text)
    body = text[start:end].strip()

    if not body:
        raise ValueError(f"CHANGELOG section for version {version!r} is empty")

    return body


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "usage: extract_release_notes.py TAG [CHANGELOG] [OUTPUT]",
            file=sys.stderr,
        )
        sys.exit(2)

    tag = sys.argv[1]
    changelog = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("CHANGELOG.md")
    output = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("release-notes.md")

    try:
        notes = extract_release_notes(changelog, tag_to_version(tag))
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    output.write_text(notes + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
