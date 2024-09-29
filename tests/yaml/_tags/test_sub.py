import os
import re
from unittest.mock import patch

import pytest

from granular_configuration import Configuration
from granular_configuration.exceptions import (
    EnvironmentVaribleNotFound,
    InterpolationSyntaxError,
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
    test_data = "!Sub ${$.no_data.here}"
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


def test_get_dollar_sign_from_dollar_sign() -> None:
    test_data = "!Sub ${$}{VAR}"
    with patch.dict(os.environ, values={}):
        assert loads(test_data) == "${VAR}"


def test_environment_variable_nesting() -> None:
    test_data = """\
data: dog
tests:
    a: !Sub ${VAR1:+VAR2}
    b: !Sub ${UNREAL1:+VAR2}
    c: !Sub ${UNREAL1:+UNREAL2:-test-c}
    d: !Sub ${UNREAL1:+UNREAL2:+$.data}
    e: !Sub ${UNREAL1:+UNREAL2:+/data}
    f: !Sub ${VAR1:+VAR2:+/data}
    g: !Sub ${UNREAL1:+VAR2:+/data}
    h: !Sub ${UNREAL1:+UNREAL2:+&#x24;&#x7B;&#x7D;}
    i: !Sub ${UNREAL1:+UNREAL2:+$}
"""

    with patch.dict(os.environ, values={"VAR1": "var1", "VAR2": "var2"}):
        output: Configuration = loads(test_data)
        assert output.tests.as_dict() == dict(
            a="var1",
            b="var2",
            c="test-c",
            d="dog",
            e="dog",
            f="var1",
            g="var2",
            h="${}",
            i="$",
        )


def test_environment_variable_default_with_nester_symbol_does_not_modify_value() -> None:
    test_data = "!Sub ${unreal_env_variable:-default:+value}"
    with patch.dict(os.environ, values={}):
        assert loads(test_data) == "default:+value"


def test_environment_variable_default_with_default_symbol_does_not_modify_value() -> None:
    test_data = "!Sub ${unreal_env_variable:-default:-value}"
    with patch.dict(os.environ, values={}):
        assert loads(test_data) == "default:-value"


def test_that_double_colon_returns_single_colon() -> None:
    test_data = "!Sub ${::}"
    with patch.dict(os.environ, values={":": "value"}):
        assert loads(test_data) == "value"


def test_that_quad_colon_returns_double_colon() -> None:
    test_data = "!Sub ${::::}"
    with patch.dict(os.environ, values={"::": "value"}):
        assert loads(test_data) == "value"


def test_environment_variable_default_with_colon_does_not_modify_value() -> None:
    test_data = "!Sub ${unreal_env_variable:-default::value}"
    with patch.dict(os.environ, values={}):
        assert loads(test_data) == "default::value"


def test_environment_variable_with_dangling_colon_errors() -> None:
    test_data = "!Sub ${unreal_env_variable:bad_syntax}"
    with patch.dict(os.environ, values={}), pytest.raises(InterpolationSyntaxError, match=re.escape('":b"')):
        loads(test_data)


def test_environment_variable_with_dangling_colon_errors_in_nesting() -> None:
    test_data = "!Sub ${unreal_env_variable:+unreal_env_variable:bad_syntax}"
    with patch.dict(os.environ, values={}), pytest.raises(InterpolationSyntaxError, match=re.escape('":b"')):
        loads(test_data)


def test_allowing_environment_variables_with_colons_via_double_colon() -> None:
    test_data = """\
tests:
    a: !Sub ${a::b}
    b: !Sub ${a::b:-default}
    c: !Sub ${a::b:+a::b}
    d: !Sub ${a::b_not:-default}
    e: !Sub ${a::b_not:+a::b}
    f: !Sub ${a::b_not:+$}
"""

    with patch.dict(os.environ, values={"a:b": "a:b"}):
        output: Configuration = loads(test_data)
        assert output.tests.as_dict() == dict(
            a="a:b",
            b="a:b",
            c="a:b",
            d="default",
            e="a:b",
            f="$",
        )


def test_that_empty_interpolation_errors() -> None:
    test_data = "!Sub ${}"
    with patch.dict(os.environ, values={}), pytest.raises(InterpolationSyntaxError, match=re.escape('"${}"')):
        loads(test_data)


def test_that_single_colon_interpolation_errors() -> None:
    test_data = "!Sub ${:}"
    with patch.dict(os.environ, values={}), pytest.raises(InterpolationSyntaxError, match=re.escape('":None"')):
        loads(test_data)


def test_special_static_cases() -> None:
    assert loads("!Sub $") == "$"
    assert loads("!Sub ${") == "${"
