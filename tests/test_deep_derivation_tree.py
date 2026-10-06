"""Depth regressions checked without recursive fixture construction or inspection."""

import sys

import pytest

from syntax_symphony import DT, Grammar

HEIGHT = 10000
TERMINAL = "λ🦉"


def inspect_tree(root):
    nodes = []
    shape = []
    pending = [root]
    while pending:
        node = pending.pop()
        nodes.append(node)
        shape.append(
            (node.symbol, None if node.children is None else len(node.children))
        )
        pending.extend(reversed(node.children or []))
    return nodes, shape


def inspect_data(root):
    shape = []
    pending = [root]
    while pending:
        node = pending.pop()
        children = node["children"]
        shape.append((node["symbol"], None if children is None else len(children)))
        pending.extend(reversed(children or []))
    return shape


@pytest.fixture
def deep_tree():
    tree = DT(TERMINAL, [])
    for _ in range(HEIGHT - 1):
        tree = DT("<A>", [tree])
    return tree


def test_deep_inspection_and_traversal(deep_tree):
    limit = sys.getrecursionlimit()
    grammar = Grammar({"<start>": ["<A>"], "<A>": ["<A>", TERMINAL]})
    assert deep_tree.height() == HEIGHT
    assert deep_tree.is_valid(grammar)
    assert str(deep_tree) == TERMINAL
    expected_repr = "DT('<A>', [" * (HEIGHT - 1)
    expected_repr += f"DT({TERMINAL!r}, [])" + "])" * (HEIGHT - 1)
    assert repr(deep_tree) == expected_repr

    expected_symbols = ["<A>"] * (HEIGHT - 1) + [TERMINAL]
    assert [node.symbol for node in deep_tree] == expected_symbols
    assert sys.getrecursionlimit() == limit


def test_deep_clone_comparison_and_membership(deep_tree):
    original_nodes, original_shape = inspect_tree(deep_tree)
    clone = deep_tree.clone()
    cloned_nodes, cloned_shape = inspect_tree(clone)
    assert cloned_shape == original_shape
    assert all(
        original is not copied
        for original, copied in zip(original_nodes, cloned_nodes, strict=True)
    )
    assert all(
        original.children is not copied.children
        for original, copied in zip(original_nodes, cloned_nodes, strict=True)
    )
    assert deep_tree == clone
    wrapper = DT("wrapper", [deep_tree])
    assert clone in wrapper

    cloned_nodes[-2].children[0] = DT("different", [])
    assert deep_tree != clone
    assert clone not in wrapper
    assert inspect_tree(deep_tree)[1] == original_shape


def test_deep_dictionary_round_trip_and_symbol_validation(deep_tree):
    expected_shape = [("<A>", 1)] * (HEIGHT - 1) + [(TERMINAL, 0)]
    data = deep_tree.to_dict()
    assert inspect_data(data) == expected_shape
    restored = DT.from_dict(data)
    restored_nodes, restored_shape = inspect_tree(restored)
    assert restored_shape == expected_shape
    assert all(
        original is not rebuilt
        for original, rebuilt in zip(
            inspect_tree(deep_tree)[0], restored_nodes, strict=True
        )
    )

    leaf = data
    while leaf["children"]:
        leaf = leaf["children"][0]
    leaf["symbol"] = 123
    with pytest.raises(TypeError, match="got int"):
        DT.from_dict(data)


def test_deep_invalid_descendant(deep_tree):
    nodes, _ = inspect_tree(deep_tree)
    nodes[-2].children[0] = DT("wrong", [])
    grammar = Grammar({"<start>": ["<A>"], "<A>": ["<A>", TERMINAL]})
    assert not deep_tree.is_valid(grammar)
