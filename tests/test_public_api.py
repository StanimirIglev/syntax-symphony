import syntax_symphony
from syntax_symphony import DT, Grammar, SyntaxSymphony, load_grammar_from_file


def test_public_api_exports() -> None:
    assert syntax_symphony.DT is DT
    assert syntax_symphony.Grammar is Grammar
    assert syntax_symphony.SyntaxSymphony is SyntaxSymphony
    assert syntax_symphony.load_grammar_from_file is load_grammar_from_file
