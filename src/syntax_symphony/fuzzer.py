import copy
import logging
import random
from collections import deque
from collections.abc import Callable, Iterable, Iterator

from .derivation_tree import DT
from .grammar import Grammar, _GrammarAnalysis, _is_nonterminal

__all__ = ["SyntaxSymphony"]

_logger = logging.getLogger(__name__)


class SyntaxSymphony:
    """An efficient grammar-based fuzzer.

    The SyntaxSymphony fuzzer aims to cover all elements of the grammar
    utilizing a k-path coverage strategy. The size of the k-paths can be
    adjusted by the user. Depth thresholds bias expansion toward growing
    or finishing the tree.
    """

    def __init__(
        self,
        grammar: Grammar,
        kcov: int = 1,
        min_depth: int = 0,
        max_depth: int = 10,
        seed: int | None = None,
    ):
        """Initialize a fuzzer.

        Args:
            grammar (Grammar): The input grammar.
            kcov (int, optional): Max length for k-paths. Defaults to 1.
            min_depth (int, optional): Minimal depth for derivation trees.
                Defaults to 0.
            max_depth (int, optional): Depth at which minimum-cost completion
                begins. The finished tree may be deeper. Defaults to 10.
            seed (int | None, optional): Random seed for reproducible fuzzing.
                Defaults to None (non-deterministic).

        Raises:
            ValueError: If any rule is undefined, unused, unreachable, or unable
                to finish producing terminal text.
        """
        # Keep nested token lists private so costs and coverage remain consistent.
        self._grammar = copy.deepcopy(grammar)
        _logger.info("Validating grammar and computing completion costs...")
        analysis = self._grammar._analyze()
        analysis.raise_if_invalid()
        self._kcov = kcov
        self._min_depth = min_depth
        self._max_depth = max_depth
        self._rng = random.Random(seed)
        _logger.info("Generating minimizing grammar...")
        self._minimizing_grammar = self._build_biased_grammar(analysis, min)
        _logger.info("Generating maximizing grammar...")
        self._maximizing_grammar = self._build_biased_grammar(analysis, max)
        _logger.info("Computing k-paths...")
        self._uncovered_k_paths = self._compute_k_paths(kcov)
        # NOTE: Shuffle the paths, so that we only need to pop from the list.
        for paths in self._uncovered_k_paths.values():
            self._rng.shuffle(paths)
        self._remaining_k_paths = sum(
            len(paths) for paths in self._uncovered_k_paths.values()
        )

    @property
    def grammar(self) -> Grammar:
        """An independent copy of the grammar used by this fuzzer."""
        return copy.deepcopy(self._grammar)

    @property
    def start_symbol(self) -> str:
        return self._grammar.start_symbol

    def _build_biased_grammar(
        self,
        analysis: _GrammarAnalysis,
        bias: Callable[[Iterable[int | float]], int | float],
    ) -> Grammar:
        """Creates a grammar that is biased towards maximizing/minimizing expansions,
        based on the provided bias function (min or max).

        Args:
            analysis (_GrammarAnalysis): The analysis of the grammar.
            bias (Callable[[Iterable[int | float]], int | float]): The bias
                function to use. Either min or max.

        Returns:
            Grammar: A grammar biased towards maximizing/minimizing expansions.
        """
        biased_grammar: dict[str, list[list[str]]] = {}
        for symbol, expansions in self._grammar.items():
            expansion_costs = analysis.expansion_costs[symbol]
            bias_cost = bias(expansion_costs)
            biased_grammar[symbol] = [
                exp.copy()
                for exp, cost in zip(expansions, expansion_costs, strict=True)
                if cost == bias_cost
            ]
        return Grammar(biased_grammar, start_symbol=self.start_symbol)

    def _symbol_to_tree(self, symbol: str) -> DT:
        """Converts a symbol to a derivation tree.

        Args:
            symbol (str): A grammar symbol.

        Returns:
            DT: A derivation tree representing the symbol.
        """
        if _is_nonterminal(symbol):
            return DT(symbol, None)
        return DT(symbol, [])

    def _pick_grammar(self, depth: int) -> Grammar:
        """Picks the grammar to use based on the depth of the derivation tree.

        Args:
            depth (int): The depth of the current derivation tree.

        Returns:
            Grammar: The grammar to use for the next expansion.
        """
        if depth < self._min_depth:
            return self._maximizing_grammar
        if self._min_depth <= depth < self._max_depth:
            return self._grammar
        return self._minimizing_grammar

    def _k_paths_of_length(self, k: int) -> dict[str, list[list[list[str]]]]:
        """Computes the k-paths starting at each nonterminal.

        Args:
            k (int): The length of the paths.

        Returns:
            dict[str, list[list[str]]]: A dictionary mapping each nonterminal
            to a list of paths.
        """

        def successors(expansion: list[str]) -> Iterator[list[str]]:
            return (
                alternative
                for symbol in expansion
                if _is_nonterminal(symbol)
                for alternative in self._grammar[symbol]
            )

        if k == 1:
            return {
                symbol: [[expansion.copy()] for expansion in alternatives]
                for symbol, alternatives in self._grammar.items()
            }

        paths: dict[str, list[list[list[str]]]] = {}
        for nonterminal in self._grammar:
            paths[nonterminal] = []
            for expansion in self._grammar[nonterminal]:
                path = [expansion]
                stack = [successors(expansion)]
                while stack:
                    child_expansion = next(stack[-1], None)
                    if child_expansion is None:
                        stack.pop()
                        path.pop()
                        continue
                    path.append(child_expansion)
                    if len(path) == k:
                        paths[nonterminal].append([exp.copy() for exp in path])
                        path.pop()
                    else:
                        stack.append(successors(child_expansion))

        return paths

    def _compute_k_paths(self, max_k: int) -> dict[str, list[list[list[str]]]]:
        """Computes the k-paths up to a maximal k.

        Args:
            max_k (int): The maximal length for a path.

        Returns:
            dict[str, list[list[str]]]: A dictionary mapping each nonterminal
            to a list of paths.
        """
        if max_k < 1:
            raise ValueError("max_k must be at least 1.")
        if max_k > 5:
            _logger.warning(
                "max_k > 5 may take a long time and a lot of memory to compute "
                "if the grammar is large."
            )
        kpaths = self._k_paths_of_length(1)
        for k in range(2, max_k + 1):
            new_paths = self._k_paths_of_length(k)
            for symbol, paths in new_paths.items():
                kpaths[symbol].extend(paths)
        return kpaths

    def _k_path_to_tree(self, item: DT, path: list[list[str]]) -> DT:
        """Leads the derivation tree along the k-path expansions.

        Args:
            item (DT): The derivation tree to expand.
            path (list[list[str]]): The path to follow.

        Returns:
            DT: The expanded derivation tree.
        """

        if item.children is not None:
            raise RuntimeError(
                "k-path expansion requires an unexpanded derivation tree node."
            )
        root = DT(item.symbol, None)
        stack = [(root, 0)]
        while stack:
            tree, depth = stack.pop()
            if depth >= len(path):
                continue
            expansion = path[depth]
            if expansion not in self._grammar[tree.symbol]:
                continue
            children = []
            next_depth = depth + 1
            for symbol in reversed(expansion):
                nonterminal = _is_nonterminal(symbol)
                child = DT(symbol, None if nonterminal else [])
                children.append(child)
                if nonterminal and next_depth < len(path):
                    stack.append((child, next_depth))
            children.reverse()
            tree.children = children
        return root

    def remaining_k_paths(self) -> int:
        """Return the number of remaining uncovered k-paths.

        Returns:
            int: The number of remaining uncovered k-paths.
        """
        return self._remaining_k_paths

    def _expand_tree(self, tree: DT) -> DT:
        """Fuzzes a derivation tree by expanding the unexpanded nonterminals.

        Args:
            tree (DT): The starting derivation tree.

        Returns:
            DT: The fuzzed derivation tree.
        """
        queue: deque[tuple[int, DT]] = deque()
        queue.append((0, tree))
        while queue:
            depth, item = queue.popleft()
            if item.children is not None:
                # Nothing to expand
                continue

            if self._uncovered_k_paths[item.symbol] and depth < self._max_depth:
                path = self._uncovered_k_paths[item.symbol].pop()
                self._remaining_k_paths -= 1
                k_tree = self._k_path_to_tree(item, path)
                for i in k_tree:
                    if i.children is None:
                        # Unexpanded nodes always have height one.
                        queue.append((depth + 1, i))
                item.children = k_tree.children
            else:
                grammar = self._pick_grammar(depth)
                expansion = self._rng.choice(grammar[item.symbol])
                tree_expansion = [self._symbol_to_tree(t) for t in expansion]
                item.children = tree_expansion
                queue.extend((depth + 1, t) for t in tree_expansion)
        return tree

    def fuzz_tree(self) -> DT:
        """Generate a complete derivation tree from the configured start symbol."""
        return self._expand_tree(DT(self.start_symbol, None))

    def fuzz(self) -> str:
        """Generates fuzz.

        Returns:
            str: The fuzz.
        """
        return self.fuzz_tree().to_str()
