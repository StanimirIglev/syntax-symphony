import json
import sys
from pathlib import Path

import pytest

from syntax_symphony.cli import ssfuzz
from syntax_symphony.grammar import Grammar, load_grammar_from_file

EXPR_GRAMMAR_PATH = (
    Path(__file__).resolve().parents[1] / "examples" / "expr_grammar.json"
)


def test_load_grammar_from_file_normalized_example():
    grammar_dict = load_grammar_from_file(str(EXPR_GRAMMAR_PATH))
    grammar = Grammar(grammar_dict)

    assert grammar.start_symbol == "<start>"
    assert "<expr>" in grammar


def test_load_grammar_from_file_simplified_format(tmp_path):
    path = tmp_path / "grammar.txt"
    path.write_text(json.dumps({"<start>": ["end"]}), encoding="utf-8")

    grammar_dict = load_grammar_from_file(str(path))
    grammar = Grammar(grammar_dict)

    assert grammar.data == {"<start>": [["end"]]}


def test_load_grammar_from_file_invalid_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{ not valid json", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        load_grammar_from_file(str(path))


def test_load_grammar_from_file_not_object(tmp_path):
    path = tmp_path / "array.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")

    with pytest.raises(TypeError, match="JSON object"):
        load_grammar_from_file(str(path))


def test_load_grammar_from_file_missing():
    with pytest.raises(FileNotFoundError):
        load_grammar_from_file("/nonexistent/path/grammar.json")


def test_load_grammar_from_file_rejects_executable_payload(tmp_path):
    path = tmp_path / "malicious.json"
    path.write_text(
        '(__import__("os").system("touch /tmp/pwned"), {"<start>": [["x"]]})[1]',
        encoding="utf-8",
    )

    with pytest.raises(json.JSONDecodeError):
        load_grammar_from_file(str(path))


def test_ssfuzz_reports_missing_grammar_file(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["ssfuzz", "-g", "does-not-exist.json", "-c", "1"],
    )

    with pytest.raises(SystemExit) as exc_info:
        ssfuzz()

    assert exc_info.value.code == 1
    assert "not found" in capsys.readouterr().err.lower()


def test_ssfuzz_reports_invalid_json(monkeypatch, capsys, tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{ invalid", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["ssfuzz", "-g", str(path), "-c", "1"])

    with pytest.raises(SystemExit) as exc_info:
        ssfuzz()

    assert exc_info.value.code == 1
    assert "invalid json" in capsys.readouterr().err.lower()


def test_ssfuzz_reports_invalid_grammar_schema(monkeypatch, capsys, tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps({"<start>": 123}), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["ssfuzz", "-g", str(path), "-c", "1"])

    with pytest.raises(SystemExit) as exc_info:
        ssfuzz()

    assert exc_info.value.code == 1
    assert "invalid grammar" in capsys.readouterr().err.lower()


def test_ssfuzz_reports_missing_start_symbol(monkeypatch, capsys, tmp_path):
    path = tmp_path / "grammar.json"
    path.write_text(json.dumps({"<start>": [["end"]]}), encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["ssfuzz", "-g", str(path), "-c", "1", "--start", "missing"],
    )

    with pytest.raises(SystemExit) as exc_info:
        ssfuzz()

    assert exc_info.value.code == 1
    assert "missing" in capsys.readouterr().err.lower()
