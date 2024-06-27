from __future__ import annotations
from typing import Any, Union, TYPE_CHECKING
from itertools import chain
from collections import deque
from collections.abc import Iterator

if TYPE_CHECKING:
    from .grammar import Grammar


class DT:
    """A derivation tree.

    Attributes:
        symbol (str): The grammar symbol.
        children (list[DT] | None): The children of the node.
    """

    def __init__(self, symbol: str, children: list[DT] | None):
        self._symbol = symbol
        self.children = children

    def __len__(self) -> int:
        if self.children is None:
            return 0
        return len(self.children)

    def __getitem__(self, index: int | slice) -> Union[DT, list[DT]]:
        if self.children is None:
            raise IndexError("Unxpanded symbols do not have children!")
        return self.children[index]

    def __iter__(self) -> Iterator[DT]:
        return chain([self], *(child for child in self.children or []))

    def __str__(self) -> str:
        if not self.children:
            return str(self.symbol)
        return "".join(str(child) for child in self.children)

    def __repr__(self) -> str:
        return f"DT({self.symbol!r}, {self.children!r})"

    def __contains__(self, item: DT) -> bool:
        if not self.children:
            return False
        return item in self.children

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DT):
            return False
        if self.symbol != other.symbol:
            return False
        if self.children is None and other.children is None:
            return True
        if self.children == [] and other.children == []:
            return True
        return self.children == other.children

    @property
    def symbol(self) -> str:
        """Get the symbol of the node.

        Returns:
            str: The grammar symbol.
        """
        return self._symbol

    def is_valid(self, grammar: Grammar) -> bool:
        """Check if the tree is valid according to the grammar.

        Args:
            grammar (Grammar): The grammar to validate against.

        Returns:
            bool: True if the tree is valid, False otherwise.
        """
        if self.children == []:
            if self.symbol in grammar:
                print(f"Nonterminal {self.symbol} has no children!")
                return False
            return True

        if self.symbol not in grammar:
            print(f"Symbol {self.symbol} not in grammar!")
            return False

        if self.children is None:
            return True

        valid = False
        children = "".join(c.symbol for c in self.children)
        for exp in grammar[self.symbol]:
            if children == "".join(exp):
                valid = True
                break
        if not valid:
            print(f"Invalid expansion: {children} for {self.symbol}")
            return False

        return all(child.is_valid(grammar) for child in self.children)

    def add_child(self, child: DT) -> None:
        """Add a child to the node.

        Args:
            child (DT): The child node to add.
        """
        if self.children is None:
            self.children = []
        self.children.append(child)

    def height(self) -> int:
        """Get the height of the tree.

        Returns:
            int: The height of the tree.
        """
        if not self.children:
            return 1
        return 1 + max(child.height() for child in self.children)

    def clone(self) -> DT:
        """Clone the tree.

        Returns:
            DT : The cloned tree.
        """
        if self.children is None:
            return DT(self.symbol, None)
        return DT(self.symbol, [child.clone() for child in self.children])

    def breadth_first_iterator(self) -> Iterator[DT]:
        """Get a breadth-first iterator.

        Returns:
            BreadthFirstIterator: The breadth-first iterator.
        """
        return BreadthFirstIterator(self)

    def depth_first_preorder_iterator(self) -> Iterator[DT]:
        """Get a depth-first pre-order iterator.

        Returns:
            DepthFirstPreOrderIterator: The depth-first pre-order iterator.
        """
        return DepthFirstPreOrderIterator(self)

    def depth_first_postorder_iterator(self) -> Iterator[DT]:
        """Get a depth-first post-order iterator.

        Returns:
            DepthFirstPostOrderIterator: The depth-first post-order iterator.
        """
        return DepthFirstPostOrderIterator(self)

    def to_str(self) -> str:
        """Convert the tree to a string.

        Returns:
            str: The string depicted by the tree.
        """
        # Iterative to_string method to prevent stack exhaustion for large trees
        # Note: This is also faster than the recursive __str__ method :)
        expanded: list[str] = []
        queue: deque[DT] = deque([self])
        while queue:
            curr_node = queue.popleft()
            symbol, children = curr_node.symbol, curr_node.children
            if children:
                queue.extendleft(reversed(children))
            else:
                expanded.append(symbol)
        return "".join(expanded)

    def to_dict(self) -> dict[str, Any]:
        """Convert the tree to a dictionary.

        Returns:
            dict[str, Any]: The dictionary representation of the tree.
        """
        return {
            "symbol": self.symbol,
            "children": (
                [child.to_dict() for child in self.children]
                if self.children is not None
                else None
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DT:
        """Create a derivation tree from a dictionary.

        Args:
            data (dict[str, Any]): The dictionary representation of the tree.

        Returns:
            DT: The derivation tree.
        """
        symbol = data.get("symbol")
        assert isinstance(symbol, str)
        children = None
        if data["children"] is not None:
            children = [cls.from_dict(child) for child in data["children"]]
        return cls(symbol, children)


class DepthFirstPreOrderIterator(Iterator[DT]):
    """A depth-first pre-order iterator for derivation trees."""

    def __init__(self, root_node: DT):
        self._stack: list[tuple[DT, bool]] = [(root_node, False)]

    def __iter__(self) -> Iterator[DT]:
        return self

    def __next__(self) -> DT:
        while self._stack:
            node, visited = self._stack.pop()
            if not visited:
                self._stack.append((node, True))
                if node.children:
                    for child in reversed(node.children):
                        self._stack.append((child, False))
                return node
        raise StopIteration


class DepthFirstPostOrderIterator(Iterator[DT]):
    """A depth-first post-order iterator for derivation trees."""

    def __init__(self, root_node: DT):
        self._stack: list[tuple[DT, bool]] = [(root_node, False)]

    def __iter__(self) -> Iterator[DT]:
        return self

    def __next__(self) -> DT:
        while self._stack:
            node, visited = self._stack.pop()
            if not visited:
                self._stack.append((node, True))
                if node.children:
                    for child in reversed(node.children):
                        self._stack.append((child, False))
            else:
                return node

        raise StopIteration


class BreadthFirstIterator(Iterator[DT]):
    """A breadth-first iterator for derivation trees."""

    def __init__(self, root_node: DT):
        # Use deque for efficient popping from left
        self._queue = deque([root_node])

    def __iter__(self) -> Iterator[DT]:
        return self

    def __next__(self) -> DT:
        if not self._queue:
            raise StopIteration

        node = self._queue.popleft()
        # Enqueue children for next level in the order they appear
        if node.children:
            self._queue.extend(node.children)

        return node
