import subprocess
import sys

import pytest

from syntax_symphony.derivation_tree import DT
from syntax_symphony.fuzzer import SyntaxSymphony
from syntax_symphony.grammar import Grammar


def test_grammar_rejects_missing_start_symbol():
    with pytest.raises(ValueError, match="not found in grammar"):
        Grammar({"<other>": [["x"]]}, start_symbol="<start>")


def test_grammar_rejects_multiple_start_expansions():
    with pytest.raises(ValueError, match="exactly one expansion"):
        Grammar({"<start>": [["a"], ["b"]]})


def test_grammar_accepts_valid_start_symbol():
    grammar = Grammar({"<start>": [["end"]]})
    assert grammar.start_symbol == "<start>"
    assert grammar["<start>"] == [["end"]]


def test_dt_from_dict_rejects_non_string_symbol():
    with pytest.raises(TypeError, match="must be a string"):
        DT.from_dict({"symbol": 123, "children": None})


def test_dt_from_dict_accepts_valid_data():
    dt = DT.from_dict({"symbol": "S", "children": None})
    assert dt.symbol == "S"
    assert dt.children is None


def test_k_path_to_tree_rejects_expanded_node():
    grammar = Grammar({"<start>": [["x"]]})
    fuzzer = SyntaxSymphony(grammar)
    with pytest.raises(RuntimeError, match="unexpanded derivation tree node"):
        fuzzer._k_path_to_tree(DT("<start>", []), [["x"]])


def test_validation_under_python_optimize_flag():
    """Validation must hold when asserts are stripped (python -O)."""
    script = """
from syntax_symphony.grammar import Grammar
from syntax_symphony.derivation_tree import DT

try:
    Grammar({"<other>": [["x"]]}, start_symbol="<start>")
except ValueError:
    pass
else:
    raise SystemExit("missing start symbol was not rejected")

try:
    Grammar({"<start>": [["a"], ["b"]]})
except ValueError:
    pass
else:
    raise SystemExit("multiple start expansions were not rejected")

try:
    DT.from_dict({"symbol": 123, "children": None})
except TypeError:
    pass
else:
    raise SystemExit("non-string symbol was not rejected")
"""
    result = subprocess.run(
        [sys.executable, "-O", "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
