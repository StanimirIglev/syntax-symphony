from __future__ import annotations
import re
from collections import UserDict
from schema import Schema  # type: ignore

# TODO: Consider making the grammar immutable,
# e.g., https://pypi.org/project/immutabledict/ | https://pypi.org/project/frozendict/

dict_grammar_schema = Schema({str: [str]})
grammar_schema = Schema({str: [[str]]})


def is_nonterminal(symbol: str) -> bool:
    """Determines if a string is a nonterminal."""
    if symbol == "":
        return False
    return (symbol[0], symbol[-1]) == ("<", ">")


class Grammar(UserDict[str, list[list[str]]]):
    """A context-free grammar.

    Attributes:
        start_symbol (str): The start symbol of the grammar.
    """

    def __init__(
        self,
        productions: (
            dict[str, list[list[str]]] | dict[str, list[str]] | None
        ) = None,
        start_symbol: str = "<start>",
        **kwargs,  # type: ignore
    ):
        if dict_grammar_schema.is_valid(productions):
            print("Normalizing grammar...")
            productions = normalize(productions)  # type: ignore

        grammar_schema.validate(productions)

        super().__init__(productions, **kwargs)  # type: ignore
        assert (
            start_symbol in self
        ), f"Start symbol '{start_symbol}' not found in grammar."
        self._start_symbol = start_symbol
        assert (
            len(self[start_symbol]) == 1
        ), "Start symbol must have exactly one expansion alternative."

    @property
    def start_symbol(self) -> str:
        """Get the start symbol of the grammar."""
        return self._start_symbol

    def __repr__(self):
        return f"Grammar({super().__repr__()})"

    def __str__(self):
        result: list[str] = []
        for nonterminal, expansions in self.items():
            rule = f"{nonterminal} ::= {' | '.join(''.join(expansion) for expansion in expansions)}"
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
        return {
            k: ["".join(expansion) for expansion in v] for k, v in self.items()
        }

    @classmethod
    def from_dict(cls, grammar: dict[str, list[str]]) -> Grammar:
        """Create a Grammar object from a dictionary.

        Args:
            grammar (dict[str, list[str]]): A dictionary representing a grammar.

        Returns:
            Grammar: A Grammar object.
        """
        return cls(normalize(grammar))

    @staticmethod
    def extract_nonterminals(expansion: list[str]) -> list[str]:
        """Extract nonterminals from an expansion.

        Args:
            expansion (list[str]): A list of symbols.

        Returns:
            list[str]: A list of nonterminals.
        """
        return [symbol for symbol in expansion if is_nonterminal(symbol)]

    @staticmethod
    def reachable_nonterminals(grammar: Grammar) -> set[str]:
        """Find all reachable nonterminals in the grammar.

        Args:
            grammar (Grammar): A context-free grammar.

        Returns:
            set[str]: A set of reachable nonterminals.
        """
        reachable: set[str] = set()
        stack = [grammar.start_symbol]

        while stack:
            symbol = stack.pop()
            if symbol not in reachable:
                reachable.add(symbol)
                for expansion in grammar.get(symbol, []):
                    for nonterminal in Grammar.extract_nonterminals(expansion):
                        if nonterminal not in reachable:
                            stack.append(nonterminal)

        return reachable

    @staticmethod
    def unreachable_nonterminals(grammar: Grammar) -> set[str]:
        """Find all unreachable nonterminals in the grammar.

        Args:
            grammar (Grammar): A context-free grammar.

        Returns:
            set[str]: A set of unreachable nonterminals.
        """
        return set(grammar.keys()) - Grammar.reachable_nonterminals(grammar)

    @staticmethod
    def is_valid(grammar: Grammar) -> bool:
        """Check if a grammar is valid.

        Args:
            grammar (Grammar): A context-free grammar.

        Returns:
            bool: True if the grammar is valid, False otherwise.
        """

        defined_nonterminals = set(grammar.keys())
        used_nonterminals = {grammar.start_symbol}

        for nonterminal, expansions in grammar.items():
            if not expansions:
                print(f"{nonterminal} has an empty expansion list")
                return False

            for expansion in expansions:
                if not expansion:
                    print(f"{nonterminal} contains an empty expansion")
                    return False
                used_nonterminals.update(
                    Grammar.extract_nonterminals(expansion)
                )

        unused_nonterminals = defined_nonterminals - used_nonterminals
        undefined_nonterminals = used_nonterminals - defined_nonterminals

        if unused_nonterminals:
            for unused_nonterminal in unused_nonterminals:
                print(f"{unused_nonterminal} is defined, but unused.")

        if undefined_nonterminals:
            for undefined_nonterminal in undefined_nonterminals:
                print(f"{undefined_nonterminal} is used, but never defined.")

        unreachable = Grammar.unreachable_nonterminals(grammar)
        if unreachable:
            for unreachable_nonterminal in unreachable:
                print(
                    f"{unreachable_nonterminal} is unreachable from {grammar.start_symbol}."
                )

        return used_nonterminals == defined_nonterminals and not unreachable


RE_NONTERMINAL = re.compile(r"(<[^<> ]*>)")


def normalize(grammar: dict[str, list[str]]) -> dict[str, list[list[str]]]:
    """Normalize a grammar.

    Args:
        grammar (dict[str, list[str]]): A dictionary representing a grammar.

    Returns:
        dict[str, list[list[str]]]: A normalized grammar.
    """

    def split(expansion: str) -> list[str]:
        if expansion == "":
            return [""]
        return [
            token for token in re.split(RE_NONTERMINAL, expansion) if token
        ]

    return {
        k: [split(expression) for expression in alternatives]
        for k, alternatives in grammar.items()
    }
