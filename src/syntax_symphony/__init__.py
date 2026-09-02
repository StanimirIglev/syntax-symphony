"""Efficient grammar-based fuzzer with k-path coverage."""

from importlib.metadata import version

from .derivation_tree import DT
from .fuzzer import SyntaxSymphony
from .grammar import Grammar, load_grammar_from_file

__version__ = version("syntax_symphony")

__all__ = [
    "DT",
    "Grammar",
    "SyntaxSymphony",
    "__version__",
    "load_grammar_from_file",
]
