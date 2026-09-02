import re

import pytest

from syntax_symphony.derivation_tree import DT
from syntax_symphony.fuzzer import SyntaxSymphony
from syntax_symphony.grammar import Grammar

# --- k-path computation ---


def test_compute_k_paths_k1(tiny_grammar: Grammar) -> None:
    fuzzer = SyntaxSymphony(tiny_grammar, kcov=1)
    paths = fuzzer._compute_k_paths(1)

    assert paths["<start>"] == [[["<A>"]]]
    assert paths["<A>"] == [[["<B>", "x"]], [["y"]]]
    assert paths["<B>"] == [[["z"]]]


def test_compute_k_paths_k2(tiny_grammar: Grammar) -> None:
    fuzzer = SyntaxSymphony(tiny_grammar, kcov=1)
    paths = fuzzer._compute_k_paths(2)

    assert paths["<A>"] == [[["<B>", "x"], ["z"]]]
    assert paths["<start>"] == [[["<A>"], ["<B>", "x"]], [["<A>"], ["y"]]]
    assert paths["<B>"] == []


def test_compute_k_paths_k3(tiny_grammar: Grammar) -> None:
    fuzzer = SyntaxSymphony(tiny_grammar, kcov=1)
    paths = fuzzer._compute_k_paths(3)

    assert paths["<start>"] == [[["<A>"], ["<B>", "x"], ["z"]]]
    assert paths["<A>"] == []
    assert paths["<B>"] == []


def test_compute_k_paths_accumulates_through_kcov(tiny_grammar: Grammar) -> None:
    fuzzer = SyntaxSymphony(tiny_grammar, kcov=2)

    assert len(fuzzer.k_paths["<start>"]) == 3
    assert len(fuzzer.k_paths["<A>"]) == 3
    assert len(fuzzer.k_paths["<B>"]) == 1


def test_compute_k_paths_invalid_k(tiny_grammar: Grammar) -> None:
    fuzzer = SyntaxSymphony(tiny_grammar, kcov=1)

    with pytest.raises(ValueError, match="max_k must be at least 1"):
        fuzzer.compute_k_paths(0)


def test_terminal_only_k_paths(terminal_only_grammar: Grammar) -> None:
    fuzzer = SyntaxSymphony(terminal_only_grammar, kcov=1)

    assert fuzzer.k_paths == {"<start>": [[["hello"]]]}
    assert fuzzer.remaining_k_paths() == 1


# --- cost computation and biased grammars ---


def test_compute_cost(tiny_grammar: Grammar) -> None:
    fuzzer = SyntaxSymphony(tiny_grammar, kcov=1)

    assert fuzzer.costs["<A>"] == {"<B>x": 2, "y": 1}
    assert fuzzer.costs["<B>"] == {"z": 1}
    assert fuzzer.costs["<start>"] == {"<A>": 2}


def test_biased_grammar_min_max(tiny_grammar: Grammar) -> None:
    fuzzer = SyntaxSymphony(tiny_grammar, kcov=1)

    assert fuzzer.minimizing_grammar["<A>"] == [["y"]]
    assert fuzzer.maximizing_grammar["<A>"] == [["<B>", "x"]]


# --- coverage tracking ---


def test_remaining_k_paths_initial_count(tiny_grammar: Grammar) -> None:
    fuzzer = SyntaxSymphony(tiny_grammar, kcov=2, seed=42)

    assert fuzzer.remaining_k_paths() == 7


def test_k_paths_depleted_after_fuzzing(tiny_grammar: Grammar) -> None:
    fuzzer = SyntaxSymphony(tiny_grammar, kcov=2, seed=42)
    initial = fuzzer.remaining_k_paths()

    for _ in range(initial):
        fuzzer.fuzz()

    assert fuzzer.remaining_k_paths() == 0


def test_no_paths_reused_after_depletion(tiny_grammar: Grammar) -> None:
    fuzzer = SyntaxSymphony(tiny_grammar, kcov=2, seed=42)

    while fuzzer.remaining_k_paths() > 0:
        fuzzer.fuzz()

    for _ in range(5):
        before = fuzzer.remaining_k_paths()
        fuzzer.fuzz()
        assert fuzzer.remaining_k_paths() == before == 0


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

    shallow_tree = shallow.tree_fuzz(DT(shallow.start_symbol, None))
    deep_tree = deep.tree_fuzz(DT(deep.start_symbol, None))

    assert shallow_tree.height() < deep_tree.height()


def test_min_depth_biases_toward_deeper_expansions(
    depth_chain_grammar: Grammar,
) -> None:
    low_min = SyntaxSymphony(
        depth_chain_grammar,
        kcov=1,
        min_depth=0,
        max_depth=10,
        seed=7,
    )
    high_min = SyntaxSymphony(
        depth_chain_grammar,
        kcov=1,
        min_depth=2,
        max_depth=10,
        seed=7,
    )

    low_tree = low_min.tree_fuzz(DT(low_min.start_symbol, None))
    high_tree = high_min.tree_fuzz(DT(high_min.start_symbol, None))

    assert high_tree.height() >= low_tree.height()


# --- seed reproducibility ---


def test_same_seed_same_output(tiny_grammar: Grammar) -> None:
    first = SyntaxSymphony(tiny_grammar, kcov=2, seed=99)
    second = SyntaxSymphony(tiny_grammar, kcov=2, seed=99)

    assert [first.fuzz() for _ in range(5)] == [second.fuzz() for _ in range(5)]


def test_different_seed_different_output(tiny_grammar: Grammar) -> None:
    first = SyntaxSymphony(tiny_grammar, kcov=2, seed=99)
    second = SyntaxSymphony(tiny_grammar, kcov=2, seed=100)

    assert [first.fuzz() for _ in range(5)] != [second.fuzz() for _ in range(5)]


def test_same_seed_same_shuffle_order(tiny_grammar: Grammar) -> None:
    first = SyntaxSymphony(tiny_grammar, kcov=2, seed=42)
    second = SyntaxSymphony(tiny_grammar, kcov=2, seed=42)

    assert first.uncovered_k_paths == second.uncovered_k_paths


# --- helpers and edge cases ---


def test_symbol_to_tree(tiny_grammar: Grammar) -> None:
    fuzzer = SyntaxSymphony(tiny_grammar, kcov=1)

    nonterminal = fuzzer.symbol_to_tree("<A>")
    terminal = fuzzer.symbol_to_tree("x")

    assert nonterminal.symbol == "<A>"
    assert nonterminal.children is None
    assert terminal.symbol == "x"
    assert terminal.children == []


def test_complete_tree(tiny_grammar: Grammar) -> None:
    fuzzer = SyntaxSymphony(tiny_grammar, kcov=1, seed=42)
    partial = DT("<start>", [DT("<A>", None)])
    completed = fuzzer.complete_tree(partial)

    assert completed.to_str()
    assert "<" not in completed.to_str()


def test_fuzz_returns_only_terminals(expr_grammar: Grammar) -> None:
    fuzzer = SyntaxSymphony(expr_grammar, kcov=1, seed=42)

    for _ in range(10):
        result = fuzzer.fuzz()
        assert isinstance(result, str)
        assert len(result) > 0
        assert not re.search(r"<[^>]+>", result)


def test_recursive_grammar_fuzz_succeeds(expr_grammar: Grammar) -> None:
    fuzzer = SyntaxSymphony(expr_grammar, kcov=2, seed=42)

    results = {fuzzer.fuzz() for _ in range(20)}
    assert len(results) > 1


def test_fuzz(expr_grammar: Grammar) -> None:
    symphony = SyntaxSymphony(expr_grammar, seed=42)
    result = symphony.fuzz()
    assert isinstance(result, str)
    assert len(result) > 0
