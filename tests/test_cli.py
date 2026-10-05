import hashlib
import json
import sys
from unittest.mock import Mock

import pytest

from syntax_symphony import cli as cli_module
from syntax_symphony.cli import ssfuzz
from syntax_symphony.grammar import Grammar


@pytest.mark.parametrize(
    ("contents", "extra_args", "message"),
    [
        (None, [], "not found"),
        ("{ invalid", [], "invalid json"),
        (json.dumps({"<start>": 123}), [], "invalid grammar"),
        ("[1, 2, 3]", [], "json object"),
        (json.dumps({"<start>": [["end"]]}), ["--start", "missing"], "missing"),
        (
            json.dumps({"<start>": ["<A>"], "<A>": ["<A>"]}),
            [],
            "cannot finish",
        ),
        (
            json.dumps({"<start>": ["<A>"], "<A>": ["x", "<B>"], "<B>": ["<B>"]}),
            [],
            "cannot finish",
        ),
    ],
    ids=[
        "missing-file",
        "invalid-json",
        "invalid-schema",
        "non-object",
        "missing-start",
        "empty-language",
        "dead-branch",
    ],
)
def test_ssfuzz_reports_initialization_errors_without_creating_output(
    contents, extra_args, message, monkeypatch, capsys, tmp_path
):
    path = tmp_path / "grammar.json"
    if contents is not None:
        path.write_text(contents, encoding="utf-8")
    out = tmp_path / "out"
    monkeypatch.setattr(
        sys,
        "argv",
        ["ssfuzz", "-g", str(path), "-c", "1", "-d", str(out), *extra_args],
    )

    with pytest.raises(SystemExit) as error:
        ssfuzz()

    assert error.value.code == 1
    captured = capsys.readouterr()
    assert message in captured.err.lower()
    assert "Traceback" not in captured.err
    assert not captured.out
    assert not out.exists()


@pytest.mark.parametrize("exit_text", ["x", ""], ids=["text", "epsilon"])
def test_ssfuzz_generates_with_recursive_custom_start(
    exit_text, monkeypatch, capsys, tmp_path
):
    path = tmp_path / "grammar.json"
    path.write_text(
        json.dumps({"<entry>": ["<A>"], "<A>": ["<A>", exit_text]}), encoding="utf-8"
    )
    out = tmp_path / "out"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ssfuzz",
            "-g",
            str(path),
            "-c",
            "1",
            "-d",
            str(out),
            "--start",
            "entry",
            "--max-depth",
            "0",
        ],
    )
    ssfuzz()

    digest = hashlib.sha256(exit_text.encode()).hexdigest()
    assert list(out.iterdir()) == [out / f"{digest}.txt"]
    assert (out / f"{digest}.txt").read_text(encoding="utf-8") == exit_text
    assert not capsys.readouterr().err


def test_ssfuzz_writes_unique_outputs_to_existing_directory(
    monkeypatch, capsys, tmp_path
):
    productions = {"<start>": ["<message>"], "<message>": ["hello", "world"]}
    path = tmp_path / "grammar.json"
    path.write_text(json.dumps(productions), encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    existing = out / "existing.txt"
    existing.write_text("keep", encoding="utf-8")
    samples = Mock(side_effect=["hello", "world", "hello"])
    monkeypatch.setattr(cli_module.SyntaxSymphony, "fuzz", lambda _self: samples())
    factory = Mock(wraps=cli_module.SyntaxSymphony)
    monkeypatch.setattr(cli_module, "SyntaxSymphony", factory)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ssfuzz",
            "-g",
            str(path),
            "-c",
            "3",
            "-d",
            str(out),
            "-e",
            "sql",
            "-k",
            "2",
            "--min-depth",
            "1",
            "--max-depth",
            "3",
            "--seed",
            "0",
        ],
    )

    ssfuzz()

    factory.assert_called_once_with(Grammar(productions), 2, 1, 3, seed=0)
    assert samples.call_count == 3
    expected = {
        hashlib.sha256(text.encode()).hexdigest() + ".sql": text
        for text in ("hello", "world")
    }
    assert {
        file.name: file.read_text(encoding="utf-8") for file in out.glob("*.sql")
    } == expected
    assert set(out.iterdir()) == {existing, *(out / name for name in expected)}
    assert existing.read_text(encoding="utf-8") == "keep"
    assert not capsys.readouterr().err
