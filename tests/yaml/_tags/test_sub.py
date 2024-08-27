import os
import re
from unittest.mock import patch

import pytest

from granular_configuration import Configuration
from granular_configuration.exceptions import (
    EnvironmentVaribleNotFound,
    InterpolationWarning,
    JSONPathOnlyWorksOnMappings,
    JSONPathQueryFailed,
)
from granular_configuration.yaml import loads


def test_loading_env_var() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "test me"}):
        assert loads("!Sub ${unreal_env_variable}") == "test me"
        assert loads("!Sub ${unreal_env_variable:-special}") == "test me"
        assert loads("!Sub ${unreal_env_vari:-special case }") == "special case "


def test_using_jsonpath() -> None:
    test_data = """\
data:
    dog:
        name: nitro
    cat:
        name: never owned a cat
    number: 123
tests:
    a: !Sub ${$.data.dog.name}
    b: !Sub ${$.data.dog}
    c: !Sub ${$.data.*.name}
    d: !Sub ${unreal_env_variable} ${$.data.dog.name} ${unreal_env_vari:-defaulting value}
    e: !Sub ${$.data.number}
"""

    with patch.dict(os.environ, values={"unreal_env_variable": "test me"}):
        output: Configuration = loads(test_data)
        assert output.tests.as_dict() == dict(
            a="nitro",
            b="{'name': 'nitro'}",
            c="['nitro', 'never owned a cat']",
            d="test me nitro defaulting value",
            e="123",
        )


def test_missing_env_var_throws_exception() -> None:
    with patch.dict(os.environ, values={}):
        with pytest.raises(EnvironmentVaribleNotFound):
            loads("!Sub ${unreal_env_vari}")


def test_jsonpath_missing_throw_exception() -> None:
    test_data = """
a: !Sub ${$.no_data.here}
b: c
"""
    with pytest.raises(JSONPathQueryFailed):
        loads(test_data).as_dict()


def test_jsonpath_on_a_scalar_value_makes_no_sense_and_must_fail() -> None:
    test_data = """!Sub ${$.no_data.here}
"""
    with pytest.raises(JSONPathOnlyWorksOnMappings):
        loads(test_data)


def test_get_dollar_curly_brackets_via_html_unescape() -> None:
    test_data = "!Sub ${&#x24;&#x7B;!Sub&#x7D;}"
    assert loads(test_data) == "${!Sub}"


def test_get_dollar_round_brackets_via_html_unescape() -> None:
    test_data = "!Sub ${&#x24;&#40;!Sub&#41;}"
    assert loads(test_data) == "$(!Sub)"


def test_get_dollar_square_brackets_via_html_unescape() -> None:
    test_data = "!Sub ${&#x24;&#91;!Sub&#93;}"
    assert loads(test_data) == "$[!Sub]"


def test_round_brackets_produces_a_warning() -> None:
    test_data = "!Sub $($.help)"
    with pytest.warns(InterpolationWarning, match=re.escape("$()")):
        assert loads(test_data) == "$($.help)"


def test_square_brackets_produces_a_warning() -> None:
    test_data = "!Sub $[$.help]"
    with pytest.warns(InterpolationWarning, match=re.escape("$[]")):
        assert loads(test_data) == "$[$.help]"
