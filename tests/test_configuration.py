from __future__ import annotations

import copy
import re
import typing as typ

import pytest

from granular_configuration_language import Configuration, MutableConfiguration
from granular_configuration_language._s import setter_secret
from granular_configuration_language.yaml import LazyEval, Placeholder, loads


def test_private_set_is_protected() -> None:
    config = Configuration()

    with pytest.raises(TypeError):
        config._private_set("a", 1, "hello")

    config._private_set("a", 1, setter_secret)
    assert config["a"] == 1


def test_using_like_mapping() -> None:
    config = Configuration(name="me")

    assert config.name == "me"
    assert tuple(config.items()) == (("name", "me"),)
    assert tuple(config.values()) == ("me",)
    assert dict(config) == {"name": "me"}


def test_using_MutableConfiguration_like_dict() -> None:
    config = MutableConfiguration(name="me")

    assert config.name == "me"
    assert tuple(config.items()) == (("name", "me"),)
    assert tuple(config.values()) == ("me",)
    assert dict(config) == {"name": "me"}
    assert config.pop("name") == "me"

    config = MutableConfiguration(name="me")

    assert config.popitem() == ("name", "me")


def test_making_copies() -> None:
    value = Configuration(b=1, c=2)

    new = copy.deepcopy(value)
    assert type(value) is Configuration
    assert new == value
    assert value.exists("a") is False
    assert new.exists("a") is False

    new = copy.copy(value)
    assert type(value) is Configuration
    assert new == value
    assert value.exists("a") is False
    assert new.exists("a") is False

    new = value.copy()
    assert type(value) is Configuration
    assert new == value
    assert value.exists("a") is False
    assert new.exists("a") is False


def test_making_mutable_copies() -> None:
    value = MutableConfiguration(b=1, c=2)

    new = copy.deepcopy(value)
    assert type(value) is MutableConfiguration
    assert new == value
    assert value.exists("a") is False
    assert new.exists("a") is False

    new = copy.copy(value)
    assert type(value) is MutableConfiguration
    assert new == value
    assert value.exists("a") is False
    assert new.exists("a") is False

    new = value.copy()
    assert type(value) is MutableConfiguration
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


def test_typed_get() -> None:
    test: Configuration = loads(
        """
a: b
b: 1
c: 1.0
d: true
          """
    )

    assert test.typed_get(str, "a") == "b"
    assert test.typed_get(int, "b") == 1
    assert test.typed_get(float, "c") == 1.0
    assert test.typed_get(bool, "d") is True


def test_typed_get_fails_on_incorrect_type() -> None:
    test: Configuration = loads(
        """
a: b
          """
    )

    with pytest.raises(TypeError):
        test.typed_get(int, "a")


def test_typed_get_keyerrors_as_a_dict_should() -> None:
    test: Configuration = loads(
        """
a: b
          """
    )

    with pytest.raises(KeyError):
        test.typed_get(int, "b")


def test_typed_get_default_as_a_dict_should() -> None:
    test: Configuration = loads(
        """
a: b
          """
    )

    assert test.typed_get(int, "b", default=1) == 1


def test_typed_get_predicate_replacement() -> None:
    test: Configuration = loads(
        """
a: null
          """
    )

    def isNone(value: typ.Any) -> typ.TypeGuard[str]:
        return value is None

    assert test.typed_get(str, "a", default=1, predicate=isNone) is None


def test_typed_get_predicate_replacement_failure() -> None:
    test: Configuration = loads(
        """
a: null
          """
    )

    def isNone(value: typ.Any) -> typ.TypeGuard[str]:
        return False

    with pytest.raises(TypeError):
        test.typed_get(str, "a", default=1, predicate=isNone)


def test_missing_attribute_raise_useful_message() -> None:
    test: Configuration = loads(
        """
a:
  b:
    c: Here
          """
    )

    with pytest.raises(AttributeError, match=re.escape("Request attribute `$.a.b.doesnotexist` does not exist")):
        test.a.b.doesnotexist


def test_attribute_name_is_assign_at_read() -> None:
    test: Configuration = loads(
        """
a:
  b:
    c:
      d:
e: !Ref $.a
          """
    )

    assert str(test.a._Configuration__attribute_name) == "$.a"
    assert str(test.e._Configuration__attribute_name) == "$.e"
    assert str(test.a.b.c._Configuration__attribute_name) == "$.a.b.c"
    assert str(test.e.b.c._Configuration__attribute_name) == "$.e.b.c"


def test_evalute_all_run_all_LazyEval() -> None:
    test: Configuration = loads(
        """
base: data
test:
    a: !Ref /base
    b: !Ref /base
    c: !Ref /base
    d: !Ref /base
"""
    )

    for _, value in test.test._raw_items():
        assert isinstance(value, LazyEval)

    test.evaluate_all()

    for _, value in test.test._raw_items():
        assert not isinstance(value, LazyEval)
