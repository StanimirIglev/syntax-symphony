import re
from unittest.mock import Mock

import pytest

from syntax_symphony import fuzzer as fuzzer_module
from syntax_symphony.derivation_tree import DT
from syntax_symphony.fuzzer import SyntaxSymphony
from syntax_symphony.grammar import Grammar

# --- k-path computation ---


@pytest.mark.parametrize(
    ("k", "expected"),
    [
        (
            1,
            {
                "<start>": [[["<A>"]]],
                "<A>": [[["<B>", "x"]], [["y"]]],
                "<B>": [[["z"]]],
            },
        ),
        (
            2,
            {
                "<start>": [[["<A>"], ["<B>", "x"]], [["<A>"], ["y"]]],
                "<A>": [[["<B>", "x"], ["z"]]],
                "<B>": [],
            },
        ),
        (
            3,
            {
                "<start>": [[["<A>"], ["<B>", "x"], ["z"]]],
                "<A>": [],
                "<B>": [],
            },
        ),
    ],
    ids=["single-expansions", "parent-child", "three-level-chain"],
)
def test_compute_k_paths(tiny_grammar: Grammar, k, expected) -> None:
    fuzzer = SyntaxSymphony(tiny_grammar, kcov=1)
    assert fuzzer._k_paths_of_length(k) == expected


def test_compute_k_paths_accumulates_through_kcov(tiny_grammar: Grammar) -> None:
    fuzzer = SyntaxSymphony(tiny_grammar, kcov=2)

    assert fuzzer._compute_k_paths(2) == {
        "<start>": [[["<A>"]], [["<A>"], ["<B>", "x"]], [["<A>"], ["y"]]],
        "<A>": [[["<B>", "x"]], [["y"]], [["<B>", "x"], ["z"]]],
        "<B>": [[["z"]]],
    }


def test_compute_k_paths_invalid_k(tiny_grammar: Grammar) -> None:
    with pytest.raises(ValueError, match="max_k must be at least 1"):
        SyntaxSymphony(tiny_grammar, kcov=0)


def test_terminal_only_k_paths(terminal_only_grammar: Grammar) -> None:
    fuzzer = SyntaxSymphony(terminal_only_grammar, kcov=1)

    assert fuzzer._uncovered_k_paths == {"<start>": [[["hello"]]]}
    assert fuzzer.remaining_k_paths() == 1


# --- cost computation and biased grammars ---


def test_analysis_computes_symbol_and_alternative_costs(tiny_grammar: Grammar) -> None:
    analysis = tiny_grammar._analyze()

    assert analysis.symbol_costs == {"<start>": 2, "<A>": 1, "<B>": 1}
    assert analysis.expansion_costs == {"<start>": (2,), "<A>": (2, 1), "<B>": (1,)}


def test_biased_grammar_min_max(tiny_grammar: Grammar) -> None:
    fuzzer = SyntaxSymphony(tiny_grammar, kcov=1)

    assert fuzzer._minimizing_grammar["<A>"] == [["y"]]
    assert fuzzer._maximizing_grammar["<A>"] == [["<B>", "x"]]


# --- coverage tracking ---


def test_coverage_depletes_and_generation_continues(tiny_grammar: Grammar) -> None:
    fuzzer = SyntaxSymphony(tiny_grammar, kcov=2, seed=42)
    initial = fuzzer.remaining_k_paths()
    assert initial == 7

    for _ in range(initial):
        before = fuzzer.remaining_k_paths()
        tree = fuzzer.fuzz_tree()
        assert tree.is_valid(tiny_grammar)
        after = fuzzer.remaining_k_paths()
        assert 0 <= after <= before
        if before:
            assert after < before

    assert fuzzer.remaining_k_paths() == 0
    for _ in range(5):
        tree = fuzzer.fuzz_tree()
        assert tree.is_valid(tiny_grammar)
        assert all(node.children is not None for node in tree)
        assert fuzzer.remaining_k_paths() == 0


# --- depth control ---


def test_max_depth_prefers_shallower_expansions(
    depth_chain_grammar: Grammar,
) -> None:
    shallow = SyntaxSymphony(
        depth_chain_grammar,
        kcov=1,
        min_depth=0,
        max_depth=1,
        seed=42,
    )
    deep = SyntaxSymphony(
        depth_chain_grammar,
        kcov=1,
        min_depth=0,
        max_depth=10,
        seed=42,
    )

    shallow_tree = shallow.fuzz_tree()
    deep_tree = deep.fuzz_tree()

    assert shallow_tree.height() < deep_tree.height()


@pytest.mark.parametrize(
    ("min_depth", "expected_text", "expected_height"),
    [(0, "t", 3), (2, "u", 4)],
    ids=["ordinary-choice", "grow-before-finishing"],
)
def test_min_depth_controls_fallback_expansion(
    depth_chain_grammar: Grammar, monkeypatch, min_depth, expected_text, expected_height
) -> None:
    fuzzer = SyntaxSymphony(
        depth_chain_grammar,
        kcov=1,
        min_depth=min_depth,
        max_depth=10,
        seed=7,
    )
    # Coverage paths take priority over the fallback depth policy.
    for _ in range(fuzzer.remaining_k_paths()):
        fuzzer.fuzz_tree()
    assert fuzzer.remaining_k_paths() == 0
    monkeypatch.setattr(fuzzer._rng, "choice", lambda alternatives: alternatives[-1])

    tree = fuzzer.fuzz_tree()
    assert tree.to_str() == expected_text
    assert tree.height() == expected_height
    assert tree.is_valid(depth_chain_grammar)


# --- seed reproducibility ---


@pytest.mark.parametrize("seed", [None, 0, 42], ids=["default", "zero", "positive"])
def test_seed_is_forwarded_to_local_rng(tiny_grammar: Grammar, monkeypatch, seed):
    factory = Mock(wraps=fuzzer_module.random.Random)
    monkeypatch.setattr(fuzzer_module.random, "Random", factory)

    SyntaxSymphony(tiny_grammar, seed=seed)

    factory.assert_called_once_with(seed)


# --- helpers and edge cases ---


def test_symbol_to_tree(tiny_grammar: Grammar) -> None:
    fuzzer = SyntaxSymphony(tiny_grammar, kcov=1)

    nonterminal = fuzzer._symbol_to_tree("<A>")
    terminal = fuzzer._symbol_to_tree("x")

    assert nonterminal.symbol == "<A>"
    assert nonterminal.children is None
    assert terminal.symbol == "x"
    assert terminal.children == []


def test_fuzz_tree_returns_fresh_complete_trees(tiny_grammar: Grammar) -> None:
    fuzzer = SyntaxSymphony(tiny_grammar, kcov=1, seed=42)
    first = fuzzer.fuzz_tree()
    second = fuzzer.fuzz_tree()
    assert isinstance(first, DT)
    assert first is not second
    for tree in (first, second):
        assert tree.symbol == tiny_grammar.start_symbol
        assert tree.is_valid(tiny_grammar)
        assert all(
            node.children is not None for node in tree.depth_first_preorder_iterator()
        )


def test_string_and_tree_generation_share_seed_and_coverage(
    tiny_grammar: Grammar,
) -> None:
    strings = SyntaxSymphony(tiny_grammar, kcov=2, seed=99)
    repeated = SyntaxSymphony(tiny_grammar, kcov=2, seed=99)
    trees = SyntaxSymphony(tiny_grammar, kcov=2, seed=99)
    for _ in range(10):
        assert strings.fuzz() == repeated.fuzz() == trees.fuzz_tree().to_str()
        assert (
            strings.remaining_k_paths()
            == repeated.remaining_k_paths()
            == trees.remaining_k_paths()
        )
    assert strings.remaining_k_paths() == 0


def test_recursive_generation_returns_complete_valid_trees(expr_grammar: Grammar):
    fuzzer = SyntaxSymphony(expr_grammar, kcov=2, seed=42)

    for _ in range(20):
        tree = fuzzer.fuzz_tree()
        assert tree.is_valid(expr_grammar)
        assert all(node.children is not None for node in tree)
        text = tree.to_str()
        assert text
        assert not re.search(r"<[^>]+>", text)


def test_k_path_to_tree_leaves_unmatched_siblings_for_completion():
    grammar = Grammar({"<start>": ["<A><B>"], "<A>": ["x"], "<B>": ["y"]})
    fuzzer = SyntaxSymphony(grammar, kcov=2, seed=42)

    tree = fuzzer._k_path_to_tree(DT("<start>", None), [["<A>", "<B>"], ["x"]])
    assert tree == DT("<start>", [DT("<A>", [DT("x", [])]), DT("<B>", None)])
    # Each root path must finish the sibling that is not part of that path.
    for _ in range(3):
        completed = fuzzer.fuzz_tree()
        assert completed.is_valid(grammar)
        assert completed.to_str() == "xy"


def test_k_path_to_tree_rejects_expanded_node(terminal_only_grammar: Grammar):
    fuzzer = SyntaxSymphony(terminal_only_grammar)
    with pytest.raises(RuntimeError, match="unexpanded derivation tree node"):
        fuzzer._k_path_to_tree(DT("<start>", []), [["hello"]])
