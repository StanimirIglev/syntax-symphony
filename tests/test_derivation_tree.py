import pytest

from syntax_symphony.derivation_tree import DT
from syntax_symphony.grammar import Grammar


@pytest.fixture
def branching_tree() -> DT:
    return DT("S", [DT("A", [DT("C", [])]), DT("B", [DT("D", [])])])


@pytest.mark.parametrize(
    ("children", "expected"),
    [(None, 0), ([], 0), ([DT("A", []), DT("B", [])], 2)],
    ids=["unexpanded", "terminal", "expanded"],
)
def test_dt_length(children, expected):
    assert len(DT("S", children)) == expected


def test_dt_getitem(branching_tree: DT):
    assert branching_tree[0].symbol == "A"
    assert branching_tree[1].symbol == "B"
    assert branching_tree[-1].symbol == "B"
    assert branching_tree[0:1] == [DT("A", [DT("C", [])])]
    with pytest.raises(IndexError):
        _ = branching_tree[2]
    with pytest.raises(IndexError, match="Unexpanded"):
        _ = DT("S", None)[0]


def test_dt_contains(branching_tree: DT):
    assert DT("A", [DT("C", [])]) in branching_tree
    assert DT("C", []) not in branching_tree
    assert DT("C", []) not in DT("S", None)


def test_dt_eq(branching_tree: DT):
    assert branching_tree == DT("S", [DT("A", [DT("C", [])]), DT("B", [DT("D", [])])])
    assert branching_tree != DT("S", [DT("A", []), DT("B", [])])
    assert branching_tree != DT("other", branching_tree.children)
    assert branching_tree != "S"
    assert DT("S", None) == DT("S", None)
    assert DT("S", []) == DT("S", [])
    assert DT("S", None) != DT("S", [])


@pytest.mark.parametrize(
    ("tree", "valid"),
    [
        (
            DT("<start>", [DT("<A>", [DT("x", [])]), DT("<B>", [DT("y", [])])]),
            True,
        ),
        (DT("<start>", None), True),
        (DT("x", []), True),
        (DT("<A>", []), False),
        (DT("unknown", [DT("x", [])]), False),
        (DT("<start>", [DT("wrong", [])]), False),
        (
            DT("<start>", [DT("<A>", [DT("wrong", [])]), DT("<B>", [DT("y", [])])]),
            False,
        ),
    ],
    ids=[
        "complete",
        "partial",
        "terminal",
        "empty-nonterminal",
        "unknown-parent",
        "wrong-expansion",
        "invalid-descendant",
    ],
)
def test_dt_is_valid(tree, valid):
    grammar = Grammar({"<start>": ["<A><B>"], "<A>": ["x"], "<B>": ["y"]})
    assert tree.is_valid(grammar) is valid


@pytest.mark.parametrize("unexpanded", [True, False], ids=["unexpanded", "empty"])
def test_dt_add_child(unexpanded):
    tree = DT("S", None if unexpanded else [])
    tree.add_child(DT("A", []))
    tree.add_child(DT("B", []))
    assert tree.children == [DT("A", []), DT("B", [])]


def test_dt_height(branching_tree: DT):
    assert branching_tree.height() == 3
    assert DT("S", None).height() == 1


@pytest.mark.parametrize(
    "tree",
    [DT("S", None), DT("S", [DT("A", [DT("C", [])]), DT("B", None)])],
    ids=["unexpanded", "nested"],
)
def test_dt_clone_is_independent(tree):
    original_data = tree.to_dict()
    clone = tree.clone()
    assert clone == tree
    original_nodes = list(tree)
    cloned_nodes = list(clone)
    assert all(
        original is not copied
        for original, copied in zip(original_nodes, cloned_nodes, strict=True)
    )

    cloned_nodes[-1].add_child(DT("new-descendant", []))
    clone.add_child(DT("new-child", []))
    assert tree.to_dict() == original_data


@pytest.mark.parametrize(
    ("method", "expected"),
    [
        ("__iter__", ["S", "A", "C", "B", "D"]),
        ("breadth_first_iterator", ["S", "A", "B", "C", "D"]),
        ("depth_first_preorder_iterator", ["S", "A", "C", "B", "D"]),
        ("depth_first_postorder_iterator", ["C", "A", "D", "B", "S"]),
    ],
    ids=["iteration", "breadth-first", "preorder", "postorder"],
)
def test_dt_traversal(branching_tree: DT, method, expected):
    assert [node.symbol for node in getattr(branching_tree, method)()] == expected


def test_dt_text_apis_preserve_terminal_order(branching_tree: DT):
    assert str(branching_tree) == "CD"
    assert branching_tree.to_str() == "CD"


@pytest.mark.parametrize(
    ("tree", "data"),
    [
        (DT("S", None), {"symbol": "S", "children": None}),
        (DT("S", []), {"symbol": "S", "children": []}),
        (
            DT("S", [DT("A", [DT("C", [])]), DT("B", None)]),
            {
                "symbol": "S",
                "children": [
                    {"symbol": "A", "children": [{"symbol": "C", "children": []}]},
                    {"symbol": "B", "children": None},
                ],
            },
        ),
    ],
    ids=["unexpanded", "terminal", "nested-partial"],
)
def test_dt_serialization(tree, data):
    assert tree.to_dict() == data
    assert DT.from_dict(data) == tree


def test_dt_from_dict_rejects_non_string_symbol():
    with pytest.raises(TypeError, match="must be a string"):
        DT.from_dict({"symbol": 123, "children": None})
