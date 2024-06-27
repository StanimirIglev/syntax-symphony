from syntax_symphony.grammar import Grammar
from syntax_symphony.fuzzer import SyntaxSymphony

grammar = Grammar(
    {
        "<start>": ["<expr>"],
        "<expr>": ["<term> + <expr>", "<term> - <expr>", "<term>"],
        "<term>": ["<factor> * <term>", "<factor> / <term>", "<factor>"],
        "<factor>": ["<number>", "( <expr> )"],
        "<number>": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
    }
)

# TODO: More tests!


def test_fuzz():
    symphony = SyntaxSymphony(grammar)
    result = symphony.fuzz()
    assert isinstance(result, str)
    assert len(result) > 0
