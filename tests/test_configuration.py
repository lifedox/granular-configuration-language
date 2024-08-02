from __future__ import annotations

from functools import reduce
from pathlib import Path

from granular_configuration import Configuration, LazyLoadConfiguration
from granular_configuration.yaml import Placeholder, loads

ASSET_DIR = (Path(__file__).parent / "assets").resolve()


def test_using_like_dict() -> None:
    config = LazyLoadConfiguration(ASSET_DIR / "func_test.yaml").config

    assert config.a is reduce
    assert tuple(config.items()) == (("a", reduce),)
    assert tuple(config.values()) == (reduce,)
    assert dict(config) == {"a": reduce}
    assert config.pop("a") == reduce

    config = LazyLoadConfiguration(ASSET_DIR / "func_test.yaml").config
    assert config.popitem() == ("a", reduce)


def test_making_copies() -> None:
    value = LazyLoadConfiguration(
        ASSET_DIR / "old" / "g/h.yaml",
        ASSET_DIR / "old" / "c/t.yaml",
    ).config

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


def test_exists() -> None:
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


def test_as_dict() -> None:
    input = Configuration(a="b", b=Configuration(a=Configuration(a=1)))
    expected = dict(a="b", b=dict(a=dict(a=1)))
    assert input.as_dict() == expected


def test_json_dump() -> None:
    test: Configuration = loads(
        """
a: b
          """
    )

    expected = """{"a": "b"}"""
    assert test.as_json_string() == expected
