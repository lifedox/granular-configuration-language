from itertools import combinations

from granular_configuration._utils import OrderedSet


def test_order_is_maintained() -> None:
    for combination in combinations(range(10), 10):
        assert tuple(OrderedSet(combination)) == combination
        assert tuple(reversed(OrderedSet(combination))) == tuple(reversed(combination))


def test_acts_like_a_set() -> None:
    value = OrderedSet((1, 1, 2, 2, 3, 3, 4, 4))
    assert tuple(value) == (1, 2, 3, 4)
    assert value == {1, 2, 3, 4}  # type: ignore
    assert 3 in value


def test_reorder_requires_pop() -> None:
    value = OrderedSet((1, 1, 2, 2, 3, 3, 4, 4))
    value.remove(2)
    value.add(2)
    assert value == {1, 3, 4, 2}  # type: ignore


def test_first_seen_wins() -> None:
    assert tuple(OrderedSet((1, 2, 1, 2, 1, 3, 4, 4, 3, 2, 1, 4))) == (1, 2, 3, 4)


def test_merging_two_sets() -> None:
    assert tuple(OrderedSet() | OrderedSet((1, 2, 3)) | OrderedSet((4, 3, 2))) == (1, 2, 3, 4)
