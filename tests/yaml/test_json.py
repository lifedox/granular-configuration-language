# Note: Tag specific json dump tests are with the individual tag tests
from __future__ import annotations

from collections import UserDict, deque
from pathlib import Path

import pytest

from granular_configuration_language._json import dumps
from granular_configuration_language._lazy_load_configuration import Configuration, LazyLoadConfiguration

ASSET_DIR = (Path(__file__).parent / "../assets" / "test_typed_configuration").resolve()


def test_general_mapping_can_be_dumped() -> None:
    data = UserDict({"a": 1})

    assert dumps(data) == r'{"a": 1}'


def test_general_sequence_can_be_dumped() -> None:
    data = deque((1, 2, 3))

    assert dumps(data) == r"[1, 2, 3]"


def test_TypeError_for_unhandled_types() -> None:
    with pytest.raises(TypeError):
        dumps(object())


def test_literal_string_can_be_dumped() -> None:
    assert dumps("test") == '"test"'


def test_callable_class_with_just_method_can_be_dumped() -> None:
    class A:
        def __call__(self) -> None:
            pass

    assert dumps(A()) == '"<tests.yaml.test_json.A()>"'


def test_inline_function_can_be_dumped() -> None:
    def function() -> None:
        pass

    assert dumps(function) == '"<tests.yaml.test_json.function>"'


def test_LazyLoadConfiguration_can_be_dumped() -> None:
    config = LazyLoadConfiguration(ASSET_DIR / "config.yaml")
    typed = LazyLoadConfiguration(ASSET_DIR / "config.yaml").as_typed(Configuration)

    assert dumps(config) == dumps(typed)
