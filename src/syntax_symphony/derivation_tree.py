from __future__ import annotations

import logging
from collections import deque
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

_logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .grammar import Grammar


class DT:
    """A derivation tree.

    Operations support finite acyclic trees. Do not mutate children during
    traversal. Repeated references to a subtree are visited per occurrence.

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

    def __getitem__(self, index: int | slice) -> DT | list[DT]:
        if self.children is None:
            raise IndexError("Unexpanded symbols do not have children!")
        return self.children[index]

    def __iter__(self) -> Iterator[DT]:
        return self.depth_first_preorder_iterator()

    def __str__(self) -> str:
        return self.to_str()

    def __repr__(self) -> str:
        parts: list[str] = []
        stack: list[tuple[Iterator[DT], bool]] = [(iter((self,)), True)]
        while stack:
            cursor, first = stack[-1]
            try:
                node = next(cursor)
            except StopIteration:
                stack.pop()
                if stack:
                    parts.append("])")
                continue
            if not first:
                parts.append(", ")
            stack[-1] = (cursor, False)
            parts.append(f"DT({node.symbol!r}, ")
            if node.children is None:
                parts.append("None)")
            else:
                parts.append("[")
                stack.append((iter(node.children), True))
        return "".join(parts)

    def __contains__(self, item: DT) -> bool:
        if not self.children:
            return False
        return item in self.children

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DT):
            return False
        stack: list[Iterator[tuple[DT, DT]]] = [iter(((self, other),))]
        while stack:
            try:
                left, right = next(stack[-1])
            except StopIteration:
                stack.pop()
                continue
            if left is right:
                continue
            if left.symbol != right.symbol:
                return False
            if left.children is None or right.children is None:
                if left.children is not right.children:
                    return False
                continue
            if len(left.children) != len(right.children):
                return False
            stack.append(iter(zip(left.children, right.children, strict=True)))
        return True

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
        for node, _ in self._preorder_with_depth():
            if node.children == []:
                if node.symbol in grammar:
                    _logger.warning("Nonterminal %s has no children!", node.symbol)
                    return False
                continue

            if node.symbol not in grammar:
                _logger.warning("Symbol %s not in grammar!", node.symbol)
                return False

            if node.children is None:
                continue

            children = "".join(child.symbol for child in node.children)
            if not any(children == "".join(exp) for exp in grammar[node.symbol]):
                _logger.warning("Invalid expansion: %s for %s", children, node.symbol)
                return False
        return True

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
        return max(depth for _, depth in self._preorder_with_depth())

    def _preorder_with_depth(self) -> Iterator[tuple[DT, int]]:
        """Walk left to right with root depth one and one cursor per ancestor."""
        stack: list[tuple[Iterator[DT], int]] = [(iter((self,)), 1)]
        while stack:
            cursor, depth = stack[-1]
            try:
                node = next(cursor)
            except StopIteration:
                stack.pop()
                continue
            yield node, depth
            if node.children:
                stack.append((iter(node.children), depth + 1))

    def clone(self) -> DT:
        """Clone the tree.

        Returns:
            DT : The cloned tree.
        """
        stack: list[tuple[DT, Iterator[DT], list[DT]]] = [
            (self, iter(self.children or ()), [])
        ]
        while True:
            node, cursor, children = stack[-1]
            try:
                child = next(cursor)
            except StopIteration:
                copied = DT(node.symbol, None if node.children is None else children)
                stack.pop()
                if not stack:
                    return copied
                stack[-1][2].append(copied)
            else:
                stack.append((child, iter(child.children or ()), []))

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
        children: list[dict[str, Any]] = []
        result: dict[str, Any] = {
            "symbol": self.symbol,
            "children": None if self.children is None else children,
        }
        stack: list[tuple[Iterator[DT], list[dict[str, Any]]]] = [
            (iter(self.children or ()), children)
        ]
        while stack:
            cursor, destination = stack[-1]
            try:
                child = next(cursor)
            except StopIteration:
                stack.pop()
                continue
            child_children: list[dict[str, Any]] = []
            destination.append(
                {
                    "symbol": child.symbol,
                    "children": None if child.children is None else child_children,
                }
            )
            if child.children:
                stack.append((iter(child.children), child_children))
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DT:
        """Create a derivation tree from a dictionary.

        Args:
            data (dict[str, Any]): The dictionary representation of the tree.

        Returns:
            DT: The derivation tree.
        """

        def frame(
            node: dict[str, Any],
        ) -> tuple[str, Iterator[dict[str, Any]], list[DT], bool]:
            symbol = node.get("symbol")
            if not isinstance(symbol, str):
                raise TypeError(
                    "Derivation tree symbol must be a string, "
                    f"got {type(symbol).__name__}."
                )
            children = node["children"]
            return (
                symbol,
                iter(()) if children is None else iter(children),
                [],
                children is None,
            )

        stack = [frame(data)]
        while True:
            symbol, cursor, children, unexpanded = stack[-1]
            try:
                child = next(cursor)
            except StopIteration:
                node = cls(symbol, None if unexpanded else children)
                stack.pop()
                if not stack:
                    return node
                stack[-1][2].append(node)
            else:
                stack.append(frame(child))


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
