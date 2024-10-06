# Note: Tag specific json dump tests are with the individual tag tests
from collections import UserDict, deque

import pytest

from granular_configuration_language._json import dumps


def test_general_mapping_can_be_dumped() -> None:
    data = UserDict({"a": 1})

    assert dumps(data) == r'{"a": 1}'


def test_general_sequence_can_be_dumped() -> None:
    data = deque((1, 2, 3))

    assert dumps(data) == r"[1, 2, 3]"


def test_TypeError_for_unhandled_types() -> None:
    with pytest.raises(TypeError):
        dumps(object())
