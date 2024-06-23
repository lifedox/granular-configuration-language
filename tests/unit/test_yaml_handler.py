import os
import typing as typ
from functools import reduce
from itertools import product
from unittest.mock import patch

import pytest

from granular_configuration import Configuration, ConfigurationLocations, Masked
from granular_configuration.exceptions import JSONPathOnlyWorksOnMappings, ParseEnvError
from granular_configuration.yaml import Placeholder, loads


def test_env() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "test me"}):
        assert loads("!Env '{{unreal_env_variable}}'").run() == "test me"
        assert loads("!Env '{{unreal_env_variable:special}}'").run() == "test me"
        assert loads("!Env '{{unreal_env_vari:special case }}'").run() == "special case "

        with pytest.raises(KeyError):
            loads("!Env '{{unreal_env_vari}}'").run()

        with pytest.raises(ValueError):
            loads("!Env [a]").run()


def test_func() -> None:
    assert loads("!Func functools.reduce").run() is reduce
    assert loads("!Func granular_configuration.ConfigurationLocations").run() is ConfigurationLocations

    with pytest.raises(ValueError):
        loads("!Func unreal.garbage.func").run()

    with pytest.raises(ValueError):
        loads("!Func sys.stdout").run()

    with pytest.raises(ValueError):
        loads("!Func [a]").run()


def test_class() -> None:
    assert loads("!Class granular_configuration.ConfigurationLocations").run() is ConfigurationLocations

    with pytest.raises(ValueError):
        loads("!Class functools.reduce").run()

    with pytest.raises(ValueError):
        loads("!Class unreal.garbage.func").run()

    with pytest.raises(ValueError):
        loads("!Class [a]").run()


def test_placeholder() -> None:
    placeholder = loads("!Placeholder value")

    assert isinstance(
        placeholder, Placeholder
    ), f"Placeholder isn't type Placeholder: `{placeholder.__class__.__name__}` {repr(placeholder)}"
    assert str(placeholder) == "value"

    with pytest.raises(ValueError):
        loads("!Placeholder []")


def test_parse_env_scalar__string() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "test me"}):
        assert loads("!ParseEnv unreal_env_variable").run() == "test me"


def test_parse_env_scalar__float() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "3.0"}):
        assert loads("!ParseEnv unreal_env_variable").run() == 3.0
        assert isinstance(loads("!ParseEnv unreal_env_variable").run(), float)


def test_parse_env_scalar__int() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "3"}):
        assert loads("!ParseEnv unreal_env_variable").run() == 3
        assert isinstance(loads("!ParseEnv unreal_env_variable").run(), int)


def test_parse_env_scalar__float_string() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "'3'"}):
        assert loads("!ParseEnv unreal_env_variable").run() == "3"


def test_parse_env_scalar__null() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "null"}):
        assert loads("!ParseEnv unreal_env_variable").run() is None


def test_parse_env_scalar__bool_true() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "true"}):
        assert loads("!ParseEnv unreal_env_variable").run() is True


def test_parse_env_scalar__bool_true_casing() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "True"}):
        assert loads("!ParseEnv unreal_env_variable").run() is True


def test_parse_env_scalar__bool_false() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "false"}):
        assert loads("!ParseEnv unreal_env_variable").run() is False


def test_parse_env_scalar__bool_false_casing() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "False"}):
        assert loads("!ParseEnv unreal_env_variable").run() is False


def test_parse_env_scalar__dict() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": '{"a": "value"}'}):
        assert loads("!ParseEnv unreal_env_variable").run() == {"a": "value"}


def test_parse_env_scalar__Configuration() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": '{"a": {"b": "value"}}'}):
        value = loads("!ParseEnv unreal_env_variable", obj_pairs_hook=Configuration).run()
        assert isinstance(value, Configuration)
        assert value == {"a": {"b": "value"}}
        assert isinstance(value["a"], Configuration)


def test_parse_env_scalar__seq() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "[1, 2, 3]"}):
        assert loads("!ParseEnv unreal_env_variable").run() == [1, 2, 3]


def test_parse_env_scalar__recursive() -> None:
    with patch.dict(
        os.environ, values={"unreal_env_variable": "!ParseEnv unreal_env_variable1", "unreal_env_variable1": "42"}
    ):
        assert loads("!ParseEnv unreal_env_variable").run() == 42


def test_parse_env_scalar__var_parse_error() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "{"}):
        with pytest.raises(ParseEnvError):
            loads("!ParseEnv unreal_env_variable").run()


def test_parse_env_scalar__missing() -> None:
    with patch.dict(os.environ, values={}):
        with pytest.raises(KeyError):
            loads("!ParseEnv unreal_env_vari").run()


def test_parse_env_mapping__error() -> None:
    with patch.dict(os.environ, values={}):
        with pytest.raises(ValueError):
            loads('!ParseEnv {"unreal_env_vari": 1}')


def test_parse_env_sequence__use_default() -> None:
    with patch.dict(os.environ, values={}):
        assert loads('!ParseEnv ["unreal_env_vari", 1]').run() == 1
        assert loads('!ParseEnv ["unreal_env_vari", 1.5]').run() == 1.5
        assert loads('!ParseEnv ["unreal_env_vari", abc]').run() == "abc"
        assert loads('!ParseEnv ["unreal_env_vari", null]').run() is None
        assert loads('!ParseEnv ["unreal_env_vari", false]').run() is False
        value = loads('!ParseEnv ["unreal_env_vari", {"a": {"b": "value"}}]', obj_pairs_hook=Configuration).run()
        assert isinstance(value, Configuration)
        assert value == {"a": {"b": "value"}}
        assert isinstance(value["a"], Configuration)


def test_parse_env_sequence__string() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "test me"}):
        assert loads("!ParseEnv [unreal_env_variable, null]").run() == "test me"


def test_parse_env_sequence__float() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "3.0"}):
        assert loads("!ParseEnv [unreal_env_variable, null]").run() == 3.0
        assert isinstance(loads("!ParseEnv [unreal_env_variable, null]").run(), float)


def test_parse_env_sequence__int() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "3"}):
        assert loads("!ParseEnv [unreal_env_variable, null]").run() == 3
        assert isinstance(loads("!ParseEnv [unreal_env_variable, null]").run(), int)


def test_parse_env_safe_sequence__use_default() -> None:
    with patch.dict(os.environ, values={}):
        assert loads('!ParseEnvSafe ["unreal_env_vari", 1]').run() == 1
        assert loads('!ParseEnvSafe ["unreal_env_vari", 1.5]').run() == 1.5
        assert loads('!ParseEnvSafe ["unreal_env_vari", abc]').run() == "abc"
        assert loads('!ParseEnvSafe ["unreal_env_vari", null]').run() is None
        assert loads('!ParseEnvSafe ["unreal_env_vari", false]').run() is False
        value = loads('!ParseEnvSafe ["unreal_env_vari", {"a": {"b": "value"}}]', obj_pairs_hook=Configuration).run()
        assert isinstance(value, Configuration)
        assert value == {"a": {"b": "value"}}
        assert isinstance(value["a"], Configuration)


def test_parse_env_safe_sequence__string() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "test me"}):
        assert loads("!ParseEnvSafe [unreal_env_variable, null]").run() == "test me"


def test_parse_env_safe_sequence__float() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "3.0"}):
        assert loads("!ParseEnvSafe [unreal_env_variable, null]").run() == 3.0
        assert isinstance(loads("!ParseEnvSafe [unreal_env_variable, null]").run(), float)


def test_parse_env_safe_sequence__int() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "3"}):
        assert loads("!ParseEnvSafe [unreal_env_variable, null]").run() == 3
        assert isinstance(loads("!ParseEnvSafe [unreal_env_variable, null]").run(), int)


def test_parse_env_safe_with_a_tag_fails() -> None:
    with patch.dict(
        os.environ, values={"unreal_env_variable": "!ParseEnv unreal_env_variable1", "unreal_env_variable1": "42"}
    ):
        with pytest.raises(ParseEnvError):
            loads("!ParseEnvSafe unreal_env_variable").run()


def test_sub__env() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "test me"}):
        assert loads("!Sub ${unreal_env_variable}").run() == "test me"
        assert loads("!Sub ${unreal_env_variable:-special}").run() == "test me"
        assert loads("!Sub ${unreal_env_vari:-special case }").run() == "special case "

        with pytest.raises(KeyError):
            loads("!Sub ${unreal_env_vari}").run()

        with pytest.raises(ValueError):
            loads("!Sub [a]").run()


def test_sub__jsonpath() -> None:
    test_data = """\
data:
    dog:
        name: nitro
    cat:
        name: never owned a cat
tests:
    a: !Sub ${$.data.dog.name}
    b: !Sub ${$.data.dog}
    c: !Sub ${$.data.*.name}
    d: !Sub ${unreal_env_variable} ${$.data.dog.name} ${unreal_env_vari:-defaulting value}
"""

    with patch.dict(os.environ, values={"unreal_env_variable": "test me"}):
        output: Configuration = loads(test_data, obj_pairs_hook=Configuration)
        assert output.tests.as_dict() == dict(
            a="nitro",
            b="{'name': 'nitro'}",
            c="['nitro', 'never owned a cat']",
            d="test me nitro defaulting value",
        )


def test_sub__jsonpath_missing() -> None:
    test_data = """
a: !Sub ${$.no_data.here}
b: c
"""
    with pytest.raises(KeyError):
        loads(test_data, obj_pairs_hook=Configuration).as_dict()


def test_sub__jsonpath_on_a_scalar_value_makes_no_sense_and_must_fail() -> None:
    test_data = """!Sub ${$.no_data.here}
"""
    with pytest.raises(JSONPathOnlyWorksOnMappings):
        loads(test_data, obj_pairs_hook=Configuration).run()


def product_pylance_helper(*iterable: typ.Iterable[bool]) -> typ.Iterator[typ.Iterable[bool]]:
    return product(*iterable)


def test_nested_parse_env_default() -> None:
    test_data = """\
aws_region: !ParseEnv
- G_ASYNC_KINESIS_AWS_REGION
- !ParseEnv [AWS_DEFAULT_REGION, us-east-1]
"""

    with patch.dict(os.environ, values={"unreal_env_variable": "test me"}):
        output: Configuration = loads(test_data, obj_pairs_hook=Configuration)
        assert getattr(output, "aws_region") == "us-east-1"


def test_nested_parse_env_nested_env() -> None:
    test_data = """\
aws_region: !ParseEnv
- G_ASYNC_KINESIS_AWS_REGION
- !ParseEnv [AWS_DEFAULT_REGION, us-east-1]
"""

    with patch.dict(os.environ, values={"AWS_DEFAULT_REGION": "test me"}):
        output: Configuration = loads(test_data, obj_pairs_hook=Configuration)
        assert getattr(output, "aws_region") == "test me"


def test_nested_parse_env_env() -> None:
    test_data = """\
aws_region: !ParseEnv
- G_ASYNC_KINESIS_AWS_REGION
- !ParseEnv [AWS_DEFAULT_REGION, us-east-1]
"""

    with patch.dict(os.environ, values={"G_ASYNC_KINESIS_AWS_REGION": "test me"}):
        output: Configuration = loads(test_data, obj_pairs_hook=Configuration)
        assert getattr(output, "aws_region") == "test me"


def test_nested_parse_env_with_sub_jsonpath() -> None:
    test_data = """\
aws_region: !ParseEnv
- G_ASYNC_KINESIS_AWS_REGION
- !ParseEnv [AWS_DEFAULT_REGION, us-east-1]
sub: data
"""

    with patch.dict(os.environ, values={"G_ASYNC_KINESIS_AWS_REGION": "!Sub ${$.sub}"}):
        output: Configuration = loads(test_data, obj_pairs_hook=Configuration)
        assert getattr(output, "aws_region") == "data"


def test_del_removes_key() -> None:
    test_data = """\
!Del "I'm gone": &data "I'm data"
"I'm here": *data
"""
    expect = {"I'm here": "I'm data"}

    assert loads(test_data, obj_pairs_hook=Configuration).as_dict() == expect


def test_del_on_non_key_does_alter_the_string() -> None:
    test_data = """\
!Del "I'm gone"
"""
    expect = "I'm gone"

    assert loads(test_data, obj_pairs_hook=Configuration) == expect


def test_supported_key_types() -> None:
    test = """\
'2': "str"
2: integer
1.123: float
"1.123": 'str'
null: test
True: "boolean"
false: "not"
"""
    assert loads(test, obj_pairs_hook=Configuration).as_dict() == {
        "2": "str",
        2: "integer",
        1.123: "float",
        "1.123": "str",
        None: "test",
        True: "boolean",
        False: "not",
    }


def test_anchor_merge() -> None:
    test = """\
!Del part: &part
    a: b
    c: d
whole:
    <<: *part
    e: f
"""
    assert loads(test, obj_pairs_hook=Configuration).as_dict() == {
        "whole": {
            "a": "b",
            "c": "d",
            "e": "f",
        }
    }


def test_spec_1_2() -> None:
    test = """\
true:
  - y
  - yes
  - on
false:
  - n
  - no
  - off
old_octal: 010
real_octal: 0o010
number: 1_000
slash: "\\/"
"""
    assert loads(test, obj_pairs_hook=Configuration).as_dict() == {
        True: ["y", "yes", "on"],
        False: ["n", "no", "off"],
        "old_octal": 10,
        "real_octal": 8,
        "number": 1000,  # Technicality YAML 1.1 behavior, but Python3 behavior
        "slash": "/",
    }


def test_spec_1_1() -> None:
    test = """\
%YAML 1.1
---
true:
  - y
  - yes
  - on
false:
  - n
  - no
  - off
old_octal: 010
real_octal: 0o010
number: 1_000
slash: "\\/"
"""
    assert loads(test, obj_pairs_hook=Configuration).as_dict() == {
        True: [True, True, True],
        False: [False, False, False],
        "old_octal": 8,
        "real_octal": "0o010",
        "number": 1000,
        "slash": "/",  # Technicality YAML 1.2 behavior
    }


def test_empty_is_null() -> None:
    assert loads("") is None


def test_mask() -> None:
    output = loads("!Mask secret")

    assert repr(output) == "'<****>'"
    assert str(output) == "secret"
    assert output == "secret"
    assert isinstance(output, Masked)
