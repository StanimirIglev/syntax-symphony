import copy
from itertools import chain
import random
from collections import deque
from typing import Callable, Generator, Iterable
from .grammar import Grammar, is_nonterminal
from .derivation_tree import DT


class SyntaxSymphony:
    """An efficient grammar-based fuzzer.

    The SyntaxSymphony fuzzer aims to cover all elements of the grammar
    utilizing a k-path coverage strategy. The size of the k-paths can be
    adjusted by the user.
    Additionally, the fuzzer provides a mechanism to control the size
    of the generated values by controlling the minimal and maximal depth
    of the derivation trees.
    """

    def __init__(
        self,
        grammar: Grammar,
        kcov: int = 1,
        min_depth: int = 0,
        max_depth: int = 10,
    ):
        """Initialize a fuzzer.

        Args:
            grammar (Grammar): The input grammar.
            kcov (int, optional): Max length for k-paths. Defaults to 1.
            min_depth (int, optional): Minimal depth for derivation trees. Defaults to 0.
            max_depth (int, optional): Maximal depth for derivation trees. Defaults to 10.
        """
        self.grammar = grammar
        self.start_symbol = grammar.start_symbol
        self._kcov = kcov
        self._min_depth = min_depth
        self._max_depth = max_depth
        self.symbol_costs: dict[str, int | float] = {}
        print("Computing costs...")
        self.costs = self.compute_cost()
        print("Generating minimizing grammar...")
        self.minimizing_grammar = self.compute_biased_grammar(min)
        print("Generating maximizing grammar...")
        self.maximizing_grammar = self.compute_biased_grammar(max)
        print("Computing k-paths...")
        self.k_paths = self.compute_k_paths(kcov)
        self.uncovered_k_paths = copy.deepcopy(self.k_paths)
        # NOTE: Shuffle the paths, so that we only need to pop from the list.
        for symbol in self.uncovered_k_paths:
            random.shuffle(self.uncovered_k_paths[symbol])
        # self.k_tree_generator = self.convert_paths_to_trees(self.k_paths)

    def symbol_cost(self, symbol: str, seen: set[str]) -> int | float:
        """Computes the cost of a symbol.

        Args:
            symbol (str): The symbol to compute the cost of.
            seen (set[str]): The set of symbols that have already been seen.

        Returns:
            int | float: The cost of the symbol.
        """
        if symbol in self.symbol_costs:
            return self.symbol_costs[symbol]

        if symbol in seen:
            cost = float("inf")
            self.symbol_costs[symbol] = cost
            return cost

        expansion_costs = [
            self.expansion_cost(exp, seen | {symbol})
            for exp in self.grammar.get(symbol, [])
        ]
        min_cost = min(expansion_costs, default=0)
        self.symbol_costs[symbol] = min_cost
        return min_cost

    def expansion_cost(
        self,
        expansion: list[str],
        seen: set[str],
    ) -> int | float:
        """Computes the cost of an expansion.

        Args:
            expansion (list[str]): The expansion to compute the cost of.
            seen (set[str]): The set of symbols that have already been seen.

        Returns:
            int | float: The cost of the expansion.
        """
        symbol_costs = [
            self.symbol_cost(symbol, seen)
            for symbol in expansion
            if symbol in self.grammar
        ]
        return max(symbol_costs, default=0) + 1

    def compute_cost(self) -> dict[str, dict[str, int | float]]:
        """Computes the costs for each symbol and its expansions.

        Returns:
            dict[str, dict[str, int | float]]: A dictionary mapping each symbol to a dictionary
            mapping each expansion to its cost.
        """
        costs: dict[str, dict[str, int | float]] = {}
        for sym in self.grammar:
            costs[sym] = {}
            for exp in self.grammar[sym]:
                costs[sym]["".join(exp)] = self.expansion_cost(exp, set())
        return costs

    def compute_biased_grammar(
        self, bias: Callable[[Iterable[int | float]], int | float]
    ) -> Grammar:
        """Creates a grammar that is biased towards maximizing/minimizing expansions,
        based on the provided bias function (min or max).

        Args:
            bias (Callable[[Iterable[int  |  float]], int  |  float]): The bias function to use.
            Either min or max.

        Returns:
            Grammar: A grammar biased towards maximizing/minimizing expansions.
        """
        biased_grammar: dict[str, list[list[str]]] = {}
        for symbol, exp_costs in self.costs.items():
            expansions = self.grammar[symbol]
            bias_cost = bias(exp_costs["".join(exp)] for exp in expansions)
            biased_grammar[symbol] = [
                exp
                for exp in expansions
                if exp_costs["".join(exp)] == bias_cost
            ]
        return Grammar(biased_grammar, start_symbol=self.start_symbol)

    def symbol_to_tree(self, symbol: str) -> DT:
        """Converts a symbol to a derivation tree.

        Args:
            symbol (str): A grammar symbol.

        Returns:
            DT: A derivation tree representing the symbol.
        """
        if is_nonterminal(symbol):
            return DT(symbol, None)
        else:
            return DT(symbol, [])

    def _pick_grammar(self, depth: int) -> Grammar:
        """Picks the grammar to use based on the depth of the derivation tree.

        Args:
            depth (int): The depth of the current derivation tree.

        Returns:
            Grammar: The grammar to use for the next expansion.
        """
        if depth < self._min_depth:
            return self.maximizing_grammar
        elif self._min_depth <= depth < self._max_depth:
            return self.grammar
        else:
            return self.minimizing_grammar

    def _compute_k_paths(self, k: int) -> dict[str, list[list[list[str]]]]:
        """Computes the k-paths starting at each nonterminal.

        Args:
            k (int): The length of the paths.

        Returns:
            dict[str, list[list[str]]]: A dictionary mapping each nonterminal to a list of paths.
        """

        def helper(expansion: list[str], depth: int) -> list[list[list[str]]]:
            if depth == 0:
                return [[expansion]]

            new_paths: list[list[list[str]]] = []
            for symbol in expansion:
                if is_nonterminal(symbol):
                    for sub_expansion in self.grammar[symbol]:
                        for path in helper(sub_expansion, depth - 1):
                            new_paths.append([expansion] + path)
            return new_paths

        paths: dict[str, list[list[list[str]]]] = {}
        for nonterminal in self.grammar:
            paths[nonterminal] = []
            for expansion in self.grammar[nonterminal]:
                paths[nonterminal].extend(helper(expansion, k - 1))

        return paths

    def compute_k_paths(
        self, max_k: int = 1
    ) -> dict[str, list[list[list[str]]]]:
        """Computes the k-paths up to a maximal k.

        Args:
            max_k (int, optional): The maximal length for a path. Defaults to 1.

        Returns:
            dict[str, list[list[str]]]: A dictionary mapping each nonterminal to a list of paths.
        """
        if max_k < 1:
            raise ValueError("max_k must be at least 1.")
        if max_k > 5:
            print(
                "Warning: max_k > 5 may take a long time"
                " and a lot of memory to compute"
                " if the grammar is large."
            )
        kpaths = self._compute_k_paths(1)
        for k in range(2, max_k + 1):
            new_paths = self._compute_k_paths(k)
            for symbol, paths in new_paths.items():
                kpaths[symbol].extend(paths)
        return kpaths

    def convert_paths_to_trees(
        self, paths: dict[str, list[list[list[str]]]]
    ) -> Generator[DT, None, None]:
        """Converts the k-path symbol map to derivation trees.

        Args:
            paths (dict[str, list[list[str]]]):
                A dictionary mapping each nonterminal to a list of paths.

        Returns:
            Generator[DT, None, None]: A generator for derivation trees.
        """
        # NOTE: Legacy function.

        def expand_tree(tree: DT, path: list[list[str]], depth: int) -> DT:
            if depth >= len(path):
                return tree

            expansion = path[depth]
            children: list[DT] = []

            if expansion not in self.grammar[tree.symbol]:
                tree.children = None
                return tree

            for symbol in expansion:
                if is_nonterminal(symbol):
                    child_tree = expand_tree(DT(symbol, None), path, depth + 1)
                    children.append(child_tree)
                else:
                    children.append(DT(symbol, []))

            tree.children = children
            return tree

        for nonterminal in paths:
            for path in paths[nonterminal]:
                yield expand_tree(DT(nonterminal, None), path, 0)

    def complete_tree(self, dtree: DT) -> DT:
        """Completes a derivation tree by expanding the unexpanded nonterminals.

        Args:
            dtree (DT): The derivation tree to complete.

        Returns:
            DT: The completed derivation tree.
        """
        symbol, children = dtree.symbol, dtree.children
        if children:
            return DT(symbol, [self.complete_tree(c) for c in children])
        if is_nonterminal(symbol):
            return self.tree_fuzz(dtree)
        else:
            return DT(symbol, [])

    def _k_path_to_tree(self, item: DT, path: list[list[str]]) -> DT:
        """Leads the derivation tree along the k-path expansions.

        Args:
            item (DT): The derivation tree to expand.
            path (list[list[str]]): The path to follow.

        Returns:
            DT: The expanded derivation tree.
        """

        def expand_tree(tree: DT, path: list[list[str]], depth: int) -> DT:
            if depth >= len(path):
                return tree

            expansion = path[depth]
            children: list[DT] = []

            if expansion not in self.grammar[tree.symbol]:
                tree.children = None
                return tree

            for symbol in expansion:
                if is_nonterminal(symbol):
                    child_tree = expand_tree(DT(symbol, None), path, depth + 1)
                    children.append(child_tree)
                else:
                    children.append(DT(symbol, []))

            tree.children = children
            return tree

        assert item.children is None
        return expand_tree(DT(item.symbol, None), path, 0)

    def remaining_k_paths(self) -> int:
        """Computes the number of remaining uncovered k-paths.

        Returns:
            int: The number of remaining uncovered k-paths.
        """
        return len(
            list(chain.from_iterable(list(self.uncovered_k_paths.values())))
        )

    def tree_fuzz(self, tree: DT) -> DT:
        """Fuzzes a derivation tree by expanding the unexpanded nonterminals.

        Args:
            tree (DT): The starting derivation tree.

        Returns:
            DT: The fuzzed derivation tree.
        """
        queue: deque[tuple[int, DT]] = deque()
        queue.append((0, tree))
        while queue:
            (depth, item) = queue.popleft()
            if item.children is not None:
                # Nothing to expand
                continue

            if (
                len(self.uncovered_k_paths[item.symbol]) > 0
                and depth < self._max_depth
            ):
                path = self.uncovered_k_paths[item.symbol].pop()
                k_tree = self._k_path_to_tree(item, path)
                for i in k_tree:
                    if i.children is None:
                        queue.append((depth + i.height(), i))
                item.children = k_tree.children
            else:
                grammar = self._pick_grammar(depth)
                expansion = random.choice(grammar[item.symbol])
                tree_expansion = [self.symbol_to_tree(t) for t in expansion]
                item.children = tree_expansion
                queue.extend((depth + 1, t) for t in tree_expansion)
        return tree

    def fuzz(self) -> str:
        """Generates fuzz.

        Returns:
            str: The fuzz.
        """
        tree = self.tree_fuzz(DT(self.start_symbol, None))
        return tree.to_str()
