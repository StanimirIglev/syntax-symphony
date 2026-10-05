"""Regression coverage for generation suitability and reliable completion."""

import math
from itertools import combinations, permutations, product

import pytest

from syntax_symphony import DT, Grammar, SyntaxSymphony
from syntax_symphony.grammar import _expansion_completion_cost


@pytest.mark.parametrize(
    ("productions", "nonproductive"),
    [
        ({"<start>": ["<A>"], "<A>": ["<A>"]}, ["<A>", "<start>"]),
        (
            {"<start>": ["<A>"], "<A>": ["<B>"], "<B>": ["<A>"]},
            ["<A>", "<B>", "<start>"],
        ),
        ({"<start>": ["<A>"], "<A>": ["x<A>"]}, ["<A>", "<start>"]),
        (
            {"<start>": ["<A>"], "<A>": ["x", "<B>"], "<B>": ["<B>"]},
            ["<B>"],
        ),
        (
            {"<start>": ["<A><B>"], "<A>": ["x"], "<B>": ["<B>"]},
            ["<B>", "<start>"],
        ),
        ({"<start>": [["<A>"]], "<A>": [["<A>"]]}, ["<A>", "<start>"]),
    ],
    ids=[
        "self-loop",
        "mutual-loop",
        "terminal-prefix",
        "dead-branch",
        "all-children",
        "tokenized-self-loop",
    ],
)
def test_nonproductive_grammars_are_rejected(productions, nonproductive):
    # Construction remains structural: internal maximizing grammars need this.
    grammar = Grammar(productions)

    assert not grammar.is_valid()
    with pytest.raises(ValueError, match="cannot finish") as error:
        grammar.validate()
    assert ", ".join(nonproductive) in str(error.value)
    with pytest.raises(ValueError, match="cannot finish"):
        SyntaxSymphony(grammar)


@pytest.mark.parametrize(
    ("productions", "expected_costs", "output"),
    [
        (
            {"<start>": ["<A>"], "<A>": ["<A>", "x"]},
            {"<start>": 2, "<A>": 1},
            "x",
        ),
        (
            {"<start>": ["<A>"], "<A>": ["<B>", "x"], "<B>": ["<A>"]},
            {"<start>": 2, "<A>": 1, "<B>": 2},
            "x",
        ),
        (
            {"<start>": ["<A>"], "<A>": ["<A>", ""]},
            {"<start>": 2, "<A>": 1},
            "",
        ),
        (
            {"<start>": ["<A><B>"], "<A>": [""], "<B>": ["<B>", ""]},
            {"<start>": 2, "<A>": 1, "<B>": 1},
            "",
        ),
        (
            {"<start>": ["<A><B>"], "<A>": ["<B>"], "<B>": ["x"]},
            {"<start>": 3, "<A>": 2, "<B>": 1},
            "xx",
        ),
    ],
    ids=["self-exit", "indirect-exit", "epsilon-exit", "nullable-children", "depth"],
)
def test_productive_grammars_have_exact_costs(productions, expected_costs, output):
    grammar = Grammar(productions)
    assert grammar.is_valid()
    assert grammar.validate() is None
    assert grammar._analyze().symbol_costs == expected_costs
    fuzzer = SyntaxSymphony(grammar, max_depth=0, seed=42)
    assert fuzzer.fuzz() == output


def test_recursive_costs_are_independent_of_rule_order():
    rules = {"<start>": ["<A>"], "<A>": ["<B>", "x"], "<B>": ["<A>"]}
    expected_costs = {"<start>": 2, "<A>": 1, "<B>": 2}
    for keys in permutations(rules):
        for alternatives in (["<B>", "x"], ["x", "<B>"]):
            grammar = Grammar(
                {key: alternatives if key == "<A>" else rules[key] for key in keys}
            )
            analysis = grammar._analyze()
            assert analysis.symbol_costs == expected_costs
            assert analysis.expansion_costs["<A>"] == tuple(
                3 if expansion == "<B>" else 1 for expansion in alternatives
            )
            assert analysis.expansion_costs["<B>"] == (2,)
            assert SyntaxSymphony(grammar, max_depth=0).fuzz() == "x"


def test_undefined_references_are_not_treated_as_terminals():
    grammar = Grammar({"<start>": ["x<missing>"]})
    assert not grammar.is_valid()
    with pytest.raises(ValueError, match="<missing> is used, but never defined"):
        SyntaxSymphony(grammar)

    assert math.isinf(_expansion_completion_cost(["x", "<missing>"], {}))


@pytest.mark.parametrize(
    "productions",
    [
        {"<start>": [["x"]], "<unused>": [["y"]]},
        {"<start>": [["x"]], "<B>": [["<C>"]], "<C>": [["<B>"]]},
        {"<start>": [["x"]], "<A>": []},
        {"<start>": [["<A>"]], "<A>": [[]]},
        {"<start>": [["x"]], "plain": [["y"]]},
    ],
    ids=["unused", "unreachable-cycle", "no-alternatives", "empty-tokens", "bad-key"],
)
def test_existing_consistency_requirements_are_enforced(productions):
    grammar = Grammar(productions)
    assert not grammar.is_valid()
    with pytest.raises(ValueError, match="Invalid grammar"):
        SyntaxSymphony(grammar)


@pytest.mark.parametrize(
    "productions",
    [
        {"<other>": [["x"]]},
        {"<start>": [["x"], ["y"]]},
        {"<start>": [[123]]},
    ],
    ids=["removed-start", "multiple-start-alternatives", "invalid-token-type"],
)
def test_mutated_grammar_is_revalidated_before_initialization(productions):
    grammar = Grammar({"<start>": ["x"]})
    grammar.data = productions
    assert not grammar.is_valid()
    with pytest.raises(ValueError, match="Invalid grammar"):
        SyntaxSymphony(grammar)


def test_custom_start_symbol_and_maximizing_grammar_remain_supported():
    grammar = Grammar({"<entry>": ["<A>"], "<A>": ["<A>", "x"]}, "<entry>")
    fuzzer = SyntaxSymphony(grammar, min_depth=2, max_depth=2, seed=42)
    assert fuzzer.start_symbol == "<entry>"
    assert fuzzer._maximizing_grammar["<A>"] == [["<A>"]]
    assert not fuzzer._maximizing_grammar.is_valid()
    assert fuzzer.fuzz() == "x"


class BoundedFuzzer(SyntaxSymphony):
    """Turn runaway expansion into a test failure instead of a hanging test."""

    def _symbol_to_tree(self, symbol):
        self.nodes += 1
        if self.nodes > 1000:
            pytest.fail("Generation did not finish within 1,000 fallback nodes")
        return super()._symbol_to_tree(symbol)


@pytest.mark.parametrize("seed", [2, 6, 15, 19, 22, 28, 32, 42])
def test_productive_branching_recursion_has_a_reliable_finishing_phase(seed):
    grammar = Grammar(
        {
            "<start>": ["<A>"],
            "<A>": ["<B>", "x"],
            "<B>": ["<D>", "<A>"],
            "<D>": ["<D><D><D>", "<B>"],
        }
    )
    fuzzer = BoundedFuzzer(grammar, max_depth=0, seed=seed)
    assert grammar._analyze().symbol_costs == {
        "<start>": 2,
        "<A>": 1,
        "<B>": 2,
        "<D>": 3,
    }
    assert fuzzer._minimizing_grammar["<D>"] == [["<B>"]]
    fuzzer.nodes = 0
    assert fuzzer._expand_tree(DT("<D>", None)).to_str() == "x"

    fuzzer = BoundedFuzzer(grammar, max_depth=2, kcov=2, seed=seed)
    fuzzer.nodes = 0
    for _ in range(10):
        tree = fuzzer.fuzz_tree()
        assert tree.is_valid(grammar)
        assert set(tree.to_str()) == {"x"}


def test_input_and_inspection_mutations_do_not_reconfigure_fuzzer():
    productions = {"<start>": [["<A>"]], "<A>": [["x"]]}
    grammar = Grammar(productions)
    fuzzer = SyntaxSymphony(grammar, max_depth=0)
    productions["<A>"][0][0] = "<A>"
    grammar["<start>"][0][0] = "<missing>"
    fuzzer.grammar["<A>"][0][0] = "<A>"

    assert fuzzer.grammar["<A>"] == [["x"]]
    assert fuzzer.fuzz() == "x"


@pytest.mark.parametrize("kcov", [1, 2])
def test_computed_coverage_paths_do_not_alias_grammar_token_lists(kcov):
    grammar = Grammar({"<start>": ["<A>"], "<A>": ["x"]})
    fuzzer = SyntaxSymphony(grammar, kcov=kcov)
    paths = fuzzer._compute_k_paths(kcov)
    for symbol_paths in paths.values():
        for path in symbol_paths:
            for expansion in path:
                expansion[:] = ["<broken>"]

    assert fuzzer.grammar == grammar
    assert fuzzer.fuzz() == "x"


@pytest.mark.parametrize("reverse", [False, True])
def test_finishing_rules_use_token_costs_even_when_joined_text_collides(reverse):
    # The second alternative is a literal terminal, not a reference to <A>.
    alternatives = [["<A>", "x"], ["<A>x"]]
    if reverse:
        alternatives.reverse()
    grammar = Grammar({"<start>": [["<A>"]], "<A>": alternatives})
    fuzzer = BoundedFuzzer(grammar, max_depth=0)
    fuzzer.nodes = 0

    assert grammar._analyze().expansion_costs["<A>"] == ((1, 2) if reverse else (2, 1))
    assert fuzzer._minimizing_grammar["<A>"] == [["<A>x"]]
    assert fuzzer._maximizing_grammar["<A>"] == [["<A>", "x"]]
    assert fuzzer.fuzz() == "<A>x"


def test_completion_analysis_handles_chains_beyond_python_recursion_limit():
    length = 1100
    productions = {"<start>": ["<0>"]}
    productions.update({f"<{i}>": [f"<{i + 1}>"] for i in range(length - 1)})
    productions[f"<{length - 1}>"] = ["x"]
    fuzzer = SyntaxSymphony(Grammar(productions), max_depth=0)
    assert fuzzer.fuzz() == "x"


def test_small_grammars_agree_with_independent_derivation_search():
    """Compare bottom-up costs to uncached search through derivation choices."""

    def search_cost(symbol, rules, ancestors=frozenset()):
        # Repeating a symbol on a branch cannot improve its minimum depth.
        if symbol in ancestors:
            return math.inf
        return min(
            1
            + max(
                (
                    search_cost(child, rules, ancestors | {symbol})
                    for child in expansion
                    if child in rules
                ),
                default=0,
            )
            for expansion in rules[symbol]
        )

    expressions = ["x", "", "<A>", "<B>", "<A><B>", "<A><A>", "<B><B>"]
    alternatives = [(exp,) for exp in expressions] + list(combinations(expressions, 2))
    for a, b in product(alternatives, repeat=2):
        productions = {"<start>": ["<A>"], "<A>": list(a), "<B>": list(b)}
        original = Grammar(productions)
        expected = {symbol: search_cost(symbol, original) for symbol in original}
        b_reachable = any("<B>" in expansion for expansion in original["<A>"])
        valid = b_reachable and all(math.isfinite(cost) for cost in expected.values())

        for rules in (productions, dict(reversed(list(productions.items())))):
            grammar = Grammar(rules)
            assert grammar.is_valid() == valid
            if not valid:
                with pytest.raises(ValueError, match="Invalid grammar"):
                    SyntaxSymphony(grammar)
                continue

            fuzzer = BoundedFuzzer(grammar, max_depth=0)
            assert grammar._analyze().symbol_costs == expected
            for symbol, choices in fuzzer._minimizing_grammar.items():
                for expansion in choices:
                    assert all(
                        expected[child] < expected[symbol]
                        for child in expansion
                        if child in expected
                    )
            fuzzer.nodes = 0
            tree = fuzzer.fuzz_tree()
            assert tree.is_valid(grammar)
