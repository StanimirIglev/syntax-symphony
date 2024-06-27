from syntax_symphony.derivation_tree import DT
from syntax_symphony.grammar import Grammar


def test_dt_creation():
    dt = DT("S", [])
    assert dt.symbol == "S"
    assert dt.children == []


def test_dt_length():
    dt = DT("S", [])
    assert len(dt) == 0
    dt = DT("S", [DT("A", []), DT("B", [])])
    assert len(dt) == 2


def test_dt_getitem():
    dt = DT("S", [DT("A", []), DT("B", [])])
    assert dt[0].symbol == "A"
    assert dt[1].symbol == "B"
    assert dt[0:2] == [DT("A", []), DT("B", [])]


def test_dt_iteration():
    dt = DT("S", [DT("A", []), DT("B", [])])
    symbols = [node.symbol for node in dt]
    assert symbols == ["S", "A", "B"]


def test_dt_str():
    dt = DT("S", [DT("A", []), DT("B", [])])
    assert str(dt) == "AB"


def test_dt_repr():
    dt = DT("S", [DT("A", []), DT("B", [])])
    assert repr(dt) == "DT('S', [DT('A', []), DT('B', [])])"


def test_dt_contains():
    dt = DT("S", [DT("A", []), DT("B", [])])
    assert DT("A", []) in dt
    assert DT("B", []) in dt
    assert DT("C", []) not in dt


def test_dt_eq():
    dt1 = DT("S", [DT("A", []), DT("B", [])])
    dt2 = DT("S", [DT("A", []), DT("B", [])])
    dt3 = DT("S", [DT("A", []), DT("C", [])])
    assert dt1 == dt2
    assert dt1 != dt3


def test_dt_is_valid():
    grammar = Grammar(
        {
            "<S>": ["<_S>"],
            "<_S>": ["<A><B>"],
            "<A>": ["A"],
            "<B>": ["B"],
        },
        "<S>",
    )
    dt1 = DT(
        "<S>",
        [DT("<_S>", [DT("<A>", [DT("A", [])]), DT("<B>", [DT("B", [])])])],
    )
    dt2 = DT(
        "<S>",
        [DT("<_S>", [DT("<A>", [DT("A", [])]), DT("<B>", [DT("C", [])])])],
    )
    assert dt1.is_valid(grammar)
    assert not dt2.is_valid(grammar)


def test_dt_add_child():
    dt = DT("S", [])
    dt.add_child(DT("A", []))
    dt.add_child(DT("B", []))
    assert dt.children == [DT("A", []), DT("B", [])]


def test_dt_height():
    dt = DT("S", [DT("A", []), DT("B", [DT("C", []), DT("D", [])])])
    assert dt.height() == 3


def test_dt_clone():
    dt = DT("S", [DT("A", []), DT("B", [])])
    clone = dt.clone()
    assert clone == dt
    assert clone is not dt


def test_dt_breadth_first_iterator():
    dt = DT("S", [DT("A", []), DT("B", [DT("C", []), DT("D", [])])])
    iterator = dt.breadth_first_iterator()
    symbols = [node.symbol for node in iterator]
    assert symbols == ["S", "A", "B", "C", "D"]


def test_dt_depth_first_preorder_iterator():
    dt = DT("S", [DT("A", []), DT("B", [DT("C", []), DT("D", [])])])
    iterator = dt.depth_first_preorder_iterator()
    symbols = [node.symbol for node in iterator]
    assert symbols == ["S", "A", "B", "C", "D"]


def test_dt_depth_first_postorder_iterator():
    dt = DT("S", [DT("A", []), DT("B", [DT("C", []), DT("D", [])])])
    iterator = dt.depth_first_postorder_iterator()
    symbols = [node.symbol for node in iterator]
    assert symbols == ["A", "C", "D", "B", "S"]


def test_dt_to_str():
    dt = DT("S", [DT("A", []), DT("B", [])])
    assert dt.to_str() == "AB"


def test_dt_to_dict():
    dt = DT("S", [DT("A", []), DT("B", [])])
    data = dt.to_dict()
    assert data == {
        "symbol": "S",
        "children": [
            {"symbol": "A", "children": []},
            {"symbol": "B", "children": []},
        ],
    }


def test_dt_from_dict():
    data = {
        "symbol": "S",
        "children": [
            {"symbol": "A", "children": []},
            {"symbol": "B", "children": []},
        ],
    }
    dt = DT.from_dict(data)
    assert dt.symbol == "S"
    assert dt.children == [DT("A", []), DT("B", [])]
