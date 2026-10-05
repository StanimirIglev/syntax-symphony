from __future__ import annotations

import json
import logging
import re
from collections import UserDict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from schema import Schema

__all__ = ["Grammar", "load_grammar_from_file"]

_logger = logging.getLogger(__name__)

# TODO: Consider making the grammar immutable,
# e.g., https://pypi.org/project/immutabledict/ | https://pypi.org/project/frozendict/

_DICT_GRAMMAR_SCHEMA = Schema({str: [str]})
_GRAMMAR_SCHEMA = Schema({str: [[str]]})


def _is_nonterminal(symbol: str) -> bool:
    """Determines if a string is a nonterminal."""
    if symbol == "":
        return False
    return (symbol[0], symbol[-1]) == ("<", ">")


def _expansion_completion_cost(
    expansion: Sequence[str], symbol_costs: Mapping[str, int | float]
) -> int | float:
    """Minimum completion depth, treating undefined nonterminals as infinite."""
    return 1 + max(
        (
            symbol_costs.get(symbol, float("inf"))
            for symbol in expansion
            if _is_nonterminal(symbol)
        ),
        default=0,
    )


@dataclass(frozen=True)
class _GrammarAnalysis:
    """Analysis of a grammar's costs and errors."""

    symbol_costs: dict[str, int | float]
    expansion_costs: dict[str, tuple[int | float, ...]]
    errors: tuple[str, ...]

    def raise_if_invalid(self) -> None:
        if self.errors:
            raise ValueError("Invalid grammar: " + " ".join(self.errors))


class Grammar(UserDict[str, list[list[str]]]):
    """A context-free grammar.

    Attributes:
        start_symbol (str): The start symbol of the grammar.

    Construction checks the data shape and start rule. Use ``is_valid()`` or
    ``validate()`` to check that the grammar is suitable for generation.
    """

    def __init__(
        self,
        productions: dict[str, list[list[str]]] | dict[str, list[str]] | None = None,
        start_symbol: str = "<start>",
        **kwargs: Any,
    ):
        if _DICT_GRAMMAR_SCHEMA.is_valid(productions):
            _logger.debug("Normalizing grammar...")
            productions = _normalize(productions)  # type: ignore

        _GRAMMAR_SCHEMA.validate(productions)

        super().__init__(productions, **kwargs)  # type: ignore
        if start_symbol not in self:
            raise ValueError(f"Start symbol '{start_symbol}' not found in grammar.")
        self._start_symbol = start_symbol
        if len(self[start_symbol]) != 1:
            raise ValueError(
                "Start symbol must have exactly one expansion alternative."
            )

    @property
    def start_symbol(self) -> str:
        """Get the start symbol of the grammar."""
        return self._start_symbol

    def __repr__(self) -> str:
        return f"Grammar({super().__repr__()})"

    def __str__(self) -> str:
        result: list[str] = []
        for nonterminal, expansions in self.items():
            joined = " | ".join("".join(expansion) for expansion in expansions)
            rule = f"{nonterminal} ::= {joined}"
            if nonterminal == self.start_symbol:
                result.insert(0, rule)
            else:
                result.append(rule)
        return "\n".join(result)

    def to_dict(self) -> dict[str, list[str]]:
        """Convert the grammar to a dictionary.

        Returns:
            dict[str, list[str]]: A dictionary representing the grammar.
        """
        return {k: ["".join(expansion) for expansion in v] for k, v in self.items()}

    @classmethod
    def from_dict(cls, grammar: dict[str, list[str]]) -> Grammar:
        """Create a Grammar object from a dictionary.

        Args:
            grammar (dict[str, list[str]]): A dictionary representing a grammar.

        Returns:
            Grammar: A Grammar object.
        """
        return cls(_normalize(grammar))

    @staticmethod
    def _extract_nonterminals(expansion: list[str]) -> list[str]:
        """Extract nonterminals from an expansion.

        Args:
            expansion (list[str]): A list of symbols.

        Returns:
            list[str]: A list of nonterminals.
        """
        return [symbol for symbol in expansion if _is_nonterminal(symbol)]

    def reachable_nonterminals(self) -> set[str]:
        """Find all reachable nonterminals in the grammar.

        Returns:
            set[str]: A set of reachable nonterminals.
        """
        reachable: set[str] = set()
        stack = [self.start_symbol]

        while stack:
            symbol = stack.pop()
            if symbol not in reachable:
                reachable.add(symbol)
                for expansion in self.get(symbol, []):
                    for nonterminal in self._extract_nonterminals(expansion):
                        if nonterminal not in reachable:
                            stack.append(nonterminal)

        return reachable

    def unreachable_nonterminals(self) -> set[str]:
        """Find all unreachable nonterminals in the grammar.

        Returns:
            set[str]: A set of unreachable nonterminals.
        """
        return set(self) - self.reachable_nonterminals()

    def _analyze(self) -> _GrammarAnalysis:
        """Compute diagnostics and all completion costs."""
        if not _GRAMMAR_SCHEMA.is_valid(self.data):
            return _GrammarAnalysis(
                {},
                {},
                ("Grammar must map strings to lists of token-list alternatives.",),
            )

        errors: list[str] = []
        if self.start_symbol not in self:
            errors.append(f"Start symbol '{self.start_symbol}' not found in grammar.")
        elif len(self[self.start_symbol]) != 1:
            errors.append("Start symbol must have exactly one expansion alternative.")

        defined_nonterminals = set(self)
        used_nonterminals = {self.start_symbol}

        for nonterminal, expansions in self.items():
            if not _is_nonterminal(nonterminal):
                errors.append(f"'{nonterminal}' is not a nonterminal symbol.")
            if not expansions:
                errors.append(f"{nonterminal} has an empty expansion list.")

            for expansion in expansions:
                if not expansion:
                    errors.append(f"{nonterminal} contains an empty expansion.")
                used_nonterminals.update(self._extract_nonterminals(expansion))

        errors.extend(
            f"{symbol} is defined, but unused."
            for symbol in sorted(defined_nonterminals - used_nonterminals)
        )
        errors.extend(
            f"{symbol} is used, but never defined."
            for symbol in sorted(used_nonterminals - defined_nonterminals)
        )
        errors.extend(
            f"{symbol} is unreachable from {self.start_symbol}."
            for symbol in sorted(self.unreachable_nonterminals())
        )
        if errors:
            return _GrammarAnalysis({}, {}, tuple(errors))

        costs: dict[str, int | float] = dict.fromkeys(self, float("inf"))
        while True:
            changed = False
            for nonterminal, alternatives in self.items():
                cost = min(
                    _expansion_completion_cost(expansion, costs)
                    for expansion in alternatives
                )
                if cost < costs[nonterminal]:
                    costs[nonterminal] = cost
                    changed = True
            if not changed:
                break

        nonproductive = sorted(
            symbol for symbol, cost in costs.items() if cost == float("inf")
        )
        if nonproductive:
            errors.append(
                "Grammar cannot finish from these reachable symbols: "
                + ", ".join(nonproductive)
                + ". Add an alternative that can produce terminal text."
            )
        expansion_costs = {
            symbol: tuple(
                _expansion_completion_cost(expansion, costs)
                for expansion in alternatives
            )
            for symbol, alternatives in self.items()
        }
        return _GrammarAnalysis(costs, expansion_costs, tuple(errors))

    def validate(self) -> None:
        """Raise if the grammar is unsuitable for generation; otherwise return None.

        Every rule must be defined, used, reachable, and able to finish.

        Raises:
            ValueError: If the grammar is unsuitable for generation.
        """
        self._analyze().raise_if_invalid()

    def is_valid(self) -> bool:
        """Check generation suitability, logging consistency/productivity errors."""
        analysis = self._analyze()
        for error in analysis.errors:
            _logger.warning("%s", error)
        return not analysis.errors


_RE_NONTERMINAL = re.compile(r"(<[^<> ]*>)")


def _normalize(grammar: dict[str, list[str]]) -> dict[str, list[list[str]]]:
    """Normalize a grammar.

    Args:
        grammar (dict[str, list[str]]): A dictionary representing a grammar.

    Returns:
        dict[str, list[list[str]]]: A normalized grammar.
    """

    def split(expansion: str) -> list[str]:
        if expansion == "":
            return [""]
        return [token for token in re.split(_RE_NONTERMINAL, expansion) if token]

    return {
        k: [split(expression) for expression in alternatives]
        for k, alternatives in grammar.items()
    }


def load_grammar_from_file(
    path: str,
) -> dict[str, list[str]] | dict[str, list[list[str]]]:
    """Load a grammar dictionary from a JSON file.

    Args:
        path: Path to a JSON grammar file.

    Returns:
        A grammar dictionary suitable for passing to ``Grammar``.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file contents are not valid JSON.
        TypeError: If the parsed JSON value is not an object.
    """
    with open(path, encoding="utf-8") as file:
        grammar_dict = json.loads(file.read())

    if not isinstance(grammar_dict, dict):
        raise TypeError(
            f"Grammar file '{path}' must contain a JSON object, "
            f"got {type(grammar_dict).__name__}."
        )

    return grammar_dict
