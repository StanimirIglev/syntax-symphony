import subprocess
import sys


def test_validation_under_python_optimize_flag():
    """Validation must hold when asserts are stripped (python -O)."""
    script = """
from syntax_symphony.grammar import Grammar
from syntax_symphony.derivation_tree import DT
from syntax_symphony.fuzzer import SyntaxSymphony

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

grammar = Grammar({"<start>": ["<A>"], "<A>": ["<A>"]})
if grammar.is_valid():
    raise SystemExit("nonproductive grammar was reported as valid")
try:
    SyntaxSymphony(grammar)
except ValueError:
    pass
else:
    raise SystemExit("nonproductive grammar was not rejected by the fuzzer")

valid = Grammar({"<start>": ["<A>"], "<A>": ["<B>", ""], "<B>": ["<A>"]})
fuzzer = SyntaxSymphony(valid, max_depth=0)
if valid.validate() is not None or fuzzer.fuzz_tree().to_str() != "":
    raise SystemExit("productive recursive grammar failed in optimized mode")
"""
    result = subprocess.run(
        [sys.executable, "-O", "-c", script],
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr or result.stdout
