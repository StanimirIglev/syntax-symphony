import json
from pathlib import Path

from syntax_symphony import DT, Grammar, SyntaxSymphony, load_grammar_from_file


def test_public_api_loads_grammar_and_generates_output(tmp_path: Path) -> None:
    grammar_path = tmp_path / "grammar.json"
    grammar_path.write_text(
        json.dumps({"<start>": ["<message>"], "<message>": ["hello"]}),
        encoding="utf-8",
    )
    grammar = Grammar(load_grammar_from_file(str(grammar_path)))
    fuzzer = SyntaxSymphony(grammar)

    assert fuzzer.fuzz() == "hello"
    tree = fuzzer.fuzz_tree()
    assert isinstance(tree, DT)
    assert tree.is_valid(grammar)
    assert tree.to_str() == "hello"
