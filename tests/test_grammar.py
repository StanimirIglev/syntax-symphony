from syntax_symphony.grammar import Grammar

expr_grammar = Grammar(
    {
        "<start>": [["<expr>"]],
        "<expr>": [["<term>", "+", "<expr>"], ["<term>"]],
        "<term>": [["<factor>", "*", "<term>"], ["<factor>"]],
        "<factor>": [["(", "<expr>", ")"], ["<number>"]],
        "<number>": [
            ["0"],
            ["1"],
            ["2"],
            ["3"],
            ["4"],
            ["5"],
            ["6"],
            ["7"],
            ["8"],
            ["9"],
        ],
    }
)


def test_grammar_creation():
    grammar = Grammar({"<start>": ["end"]})
    assert grammar.start_symbol == "<start>"
    assert grammar.data == {"<start>": [["end"]]}
    assert len(grammar) == 1


def test_extract_nonterminals():
    expansion = ["<term>", "+", "<expr>"]
    nonterminals = Grammar.extract_nonterminals(expansion)
    assert nonterminals == ["<term>", "<expr>"]


def test_reachable_nonterminals():
    reachable = Grammar.reachable_nonterminals(expr_grammar)
    assert reachable == {"<start>", "<expr>", "<term>", "<factor>", "<number>"}


def test_unreachable_nonterminals():
    unreachable = Grammar.unreachable_nonterminals(expr_grammar)
    assert unreachable == set()


def test_is_valid():
    assert Grammar.is_valid(expr_grammar) == True

    invalid_grammar = Grammar(
        {
            "<start>": [["<expr>"]],
            "<expr>": [["<term>", "+", "<expr>"], ["<term>"]],
            "<term>": [["<factor>", "*", "<term>"], ["<factor>"]],
            "<factor>": [["(", "<expr>", ")"], ["<number>"]],
            "<number>": [
                ["0"],
                ["1"],
                ["2"],
                ["3"],
                ["4"],
                ["5"],
                ["6"],
                ["7"],
                ["8"],
                ["9"],
            ],
            "<invalid>": [["<expr>"]],
        }
    )
    assert Grammar.is_valid(invalid_grammar) == False
