import pytest

from syntax_symphony.grammar import Grammar


@pytest.fixture
def tiny_grammar() -> Grammar:
    return Grammar(
        {
            "<start>": [["<A>"]],
            "<A>": [["<B>", "x"], ["y"]],
            "<B>": [["z"]],
        }
    )


@pytest.fixture
def terminal_only_grammar() -> Grammar:
    return Grammar({"<start>": [["hello"]]})


@pytest.fixture
def depth_chain_grammar() -> Grammar:
    """Grammar where maximizing expansions deepen the derivation tree."""
    return Grammar(
        {
            "<start>": [["<a>"]],
            "<a>": [["<b>"], ["t"]],
            "<b>": [["<c>"], ["u"]],
            "<c>": [["v"]],
        }
    )


@pytest.fixture
def expr_grammar() -> Grammar:
    return Grammar(
        {
            "<start>": [["<expr>"]],
            "<expr>": [
                ["<term>", " + ", "<expr>"],
                ["<term>", " - ", "<expr>"],
                ["<term>"],
            ],
            "<term>": [
                ["<factor>", " * ", "<term>"],
                ["<factor>", " / ", "<term>"],
                ["<factor>"],
            ],
            "<factor>": [["<number>"], ["(", "<expr>", ")"]],
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
