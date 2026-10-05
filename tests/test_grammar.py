import json

import pytest

from syntax_symphony.grammar import Grammar, load_grammar_from_file


@pytest.mark.parametrize(
    "productions",
    [
        {"<start>": ["prefix<A>suffix"], "<A>": ["x", ""]},
        {"<start>": [["prefix", "<A>", "suffix"]], "<A>": [["x"], [""]]},
    ],
    ids=["strings", "tokens"],
)
def test_grammar_creation_normalizes_input(productions):
    grammar = Grammar(productions)
    assert grammar.start_symbol == "<start>"
    assert grammar.data == {
        "<start>": [["prefix", "<A>", "suffix"]],
        "<A>": [["x"], [""]],
    }
    assert len(grammar) == 2


@pytest.mark.parametrize(
    ("productions", "message"),
    [
        ({"<other>": [["x"]]}, "not found in grammar"),
        ({"<start>": [["a"], ["b"]]}, "exactly one expansion"),
    ],
    ids=["missing-start", "multiple-start-expansions"],
)
def test_grammar_rejects_invalid_start_rule(productions, message):
    with pytest.raises(ValueError, match=message):
        Grammar(productions)


def test_reachable_and_unreachable_nonterminals():
    grammar = Grammar({"<start>": ["<A>"], "<A>": ["<A>", "x"], "<unused>": ["y"]})
    assert grammar.reachable_nonterminals() == {"<start>", "<A>"}
    assert grammar.unreachable_nonterminals() == {"<unused>"}


def test_grammar_dictionary_conversion_preserves_normalizable_rules():
    productions = {"<start>": ["prefix<A>suffix"], "<A>": ["x", ""]}
    grammar = Grammar.from_dict(productions)
    assert grammar.data == {
        "<start>": [["prefix", "<A>", "suffix"]],
        "<A>": [["x"], [""]],
    }
    assert grammar.to_dict() == productions


@pytest.mark.parametrize(
    "productions",
    [{"<start>": ["end"]}, {"<start>": [["end"]]}],
    ids=["strings", "tokens"],
)
def test_load_grammar_from_file_preserves_representation(tmp_path, productions):
    path = tmp_path / "grammar.json"
    path.write_text(json.dumps(productions), encoding="utf-8")

    assert load_grammar_from_file(str(path)) == productions


@pytest.mark.parametrize(
    "payload",
    [
        "{ not valid json",
        "(__import__('pathlib').Path(SENTINEL).write_text('executed'), {})[1]",
    ],
    ids=["malformed-json", "executable-payload"],
)
def test_load_grammar_from_file_rejects_non_json_without_execution(tmp_path, payload):
    path = tmp_path / "grammar.json"
    sentinel = tmp_path / "executed"
    path.write_text(payload.replace("SENTINEL", repr(str(sentinel))), encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        load_grammar_from_file(str(path))
    assert not sentinel.exists()


def test_load_grammar_from_file_rejects_non_object(tmp_path):
    path = tmp_path / "array.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")

    with pytest.raises(TypeError, match="JSON object"):
        load_grammar_from_file(str(path))


def test_load_grammar_from_file_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_grammar_from_file(str(tmp_path / "missing.json"))
