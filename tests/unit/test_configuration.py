from __future__ import annotations

from functools import reduce
from pathlib import Path

import pytest

from granular_configuration import Configuration
from granular_configuration._build import build_configuration
from granular_configuration.yaml_handler import Placeholder, loads

ASSET_DIR = (Path(__file__).parent / "../assets/config_location_test").resolve()


def test_converting_Configuration_to_dict() -> None:
    config = loads("a: !Func functools.reduce", Configuration)
    assert isinstance(config, Configuration)
    assert tuple(config.items()) == (("a", reduce),)

    config = loads("a: !Func functools.reduce", Configuration)
    assert tuple(config.values()) == (reduce,)

    config = loads("a: !Func functools.reduce", Configuration)
    assert dict(config) == {"a": reduce}

    config = loads("a: !Func functools.reduce", Configuration)
    assert config.pop("a") == reduce

    config = loads("a: !Func functools.reduce", Configuration)
    assert config.popitem() == ("a", reduce)


def test_Configuration_is_dict() -> None:
    files = (
        ASSET_DIR / "g/h.yaml",
        ASSET_DIR / "c/t.yaml",
    )

    value = build_configuration(files)

    import copy

    new = copy.deepcopy(value)
    assert new == value
    assert value.exists("a") is False
    assert new.exists("a") is False

    new = copy.copy(value)
    assert new == value
    assert value.exists("a") is False
    assert new.exists("a") is False

    new = value.copy()
    assert new == value
    assert value.exists("a") is False
    assert new.exists("a") is False

    assert isinstance(value, dict)


def test_Configuration_exists() -> None:
    config = Configuration(a=1, b=Placeholder("tests"))

    assert config.exists("a") is True
    assert config.exists("b") is False
    assert config.exists("c") is False

    assert ("a" in config) is True
    assert ("b" in config) is True
    assert ("c" in config) is False

    assert config.get("a") == 1
    assert config.get("b") is None
    assert config.get("c") is None


def test_Configuration_as_dict() -> None:
    input = Configuration(a="b", b=Configuration(a=Configuration(a=1)))
    expected = dict(a="b", b=dict(a=dict(a=1)))
    assert input.as_dict() == expected


def test_simple_patch() -> None:
    input = Configuration(a="b")
    with input.patch(dict(a="c")):
        assert input.as_dict() == dict(a="c")
        assert tuple(input._raw_items()) == tuple(dict(a="c").items())

    assert input.as_dict() == dict(a="b")


def test_patch_new_not_allowed() -> None:
    input = Configuration(a="b")

    with pytest.raises(KeyError):
        with input.patch(dict(b="c")):
            assert input.as_dict() == dict(a="b", b="c")


def test_patch_new() -> None:
    input = Configuration(a="b")
    with input.patch(dict(b="c"), allow_new_keys=True):
        assert input.as_dict() == dict(a="b", b="c")
        assert tuple(input._raw_items()) == tuple(dict(a="b", b="c").items())
        assert "b" in input
        assert len(input) == 2

    assert "b" not in input
    assert input.as_dict() == dict(a="b")
    assert len(input) == 1


def test_patch_new_dict() -> None:
    input = Configuration(a="b")
    with input.patch(dict(b="c", e=dict(a=1)), allow_new_keys=True):
        assert input.as_dict() == dict(a="b", b="c", e=dict(a=1))
        assert tuple(input._raw_items()) == tuple(dict(a="b", b="c", e=dict(a=1)).items())
        assert "b" in input
        assert "e" in input
        assert "a" in input.e

    assert input.as_dict() == dict(a="b")


def test_patch_nest_dict_deeper() -> None:
    input = Configuration(a="b")
    with input.patch({"b": {"a": {"a": 2}}}, allow_new_keys=True):
        assert input.as_dict() == {"a": "b", "b": {"a": {"a": 2}}}
        assert tuple(input._raw_items()) == tuple({"a": "b", "b": {"a": {"a": 2}}}.items())

    assert input.as_dict() == dict(a="b")


def test_patch_nest_dict() -> None:
    input = Configuration(a="b", b=Configuration(a=Configuration(a=1)))
    with input.patch({"b": {"a": {"a": 2}}}):
        assert input.as_dict() == {"a": "b", "b": {"a": {"a": 2}}}
        assert tuple(input._raw_items()) == tuple({"a": "b", "b": {"a": {"a": 2}}}.items())

        assert input.b.as_dict() == {"a": {"a": 2}}

    assert input.as_dict() == {"a": "b", "b": {"a": {"a": 1}}}
    assert input.b.as_dict() == {"a": {"a": 1}}


def test_patch_deep_nest_dict() -> None:
    input = Configuration(a="b", b=Configuration(a=Configuration(a=1)))
    with input.b.patch({"a": {"a": 2}}):
        assert input.as_dict() == {"a": "b", "b": {"a": {"a": 2}}}
        assert tuple(input._raw_items()) == tuple({"a": "b", "b": {"a": {"a": 2}}}.items())

    assert input.as_dict() == {"a": "b", "b": {"a": {"a": 1}}}


def test_nested_patch() -> None:
    input = Configuration(a="b")
    with input.patch({"a": "c", "b": "b", "c": "c"}, allow_new_keys=True):
        assert input.as_dict() == {"a": "c", "b": "b", "c": "c"}

        with input.patch({"c": "c1", "d": "c1"}, allow_new_keys=True):
            assert input.as_dict() == {"a": "c", "b": "b", "c": "c1", "d": "c1"}

    assert input.as_dict() == {"a": "b"}


def test_patch_copy() -> None:
    input = Configuration(a="b")
    with input.patch({"a": "c", "b": "b", "c": "c"}, allow_new_keys=True):
        assert input.as_dict() == {"a": "c", "b": "b", "c": "c"}

        with input.patch({"c": "c1", "d": "c1"}, allow_new_keys=True):
            assert input.as_dict() == {"a": "c", "b": "b", "c": "c1", "d": "c1"}

            import copy

            input_copy = copy.copy(input)
            input_deepcopy = copy.deepcopy(input)

            assert input_copy.as_dict() == {"a": "b"}
            assert input_deepcopy.as_dict() == {"a": "b"}

    assert input.as_dict() == {"a": "b"}


def test_patch_nested_sibling() -> None:
    CONFIG = Configuration(
        key1="value1", key2="value2", nested=Configuration(nest_key1="nested_value1", nest_key2="nested_value2")
    )
    patch = dict(key1="new_value", nested=dict(nest_key2="new_value"))
    expected = dict(key1="new_value", key2="value2", nested=dict(nest_key1="nested_value1", nest_key2="new_value"))

    with CONFIG.patch(patch):
        assert CONFIG.as_dict() == expected


def test_nested_patch_full_override() -> None:
    CONFIG = Configuration(
        key1="value1", key2="value2", nested=Configuration(nest_key1="nested_value1", nest_key2="nested_value2")
    )
    patch1 = dict(key1="new value", nested=dict(nest_key2="new value"))
    patch2 = dict(key2="new value2", nested=dict(nest_key1="new value2"))
    expected = {
        "key1": "new value",
        "key2": "new value2",
        "nested": {"nest_key1": "new value2", "nest_key2": "new value"},
    }

    with CONFIG.patch(patch1):
        with CONFIG.patch(patch2):
            assert CONFIG.as_dict() == expected

    with CONFIG.patch(patch2):
        with CONFIG.patch(patch1):
            assert CONFIG.as_dict() == expected
