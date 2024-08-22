import os
import typing as typ
from itertools import product
from unittest.mock import patch

import pytest

from granular_configuration import Configuration
from granular_configuration.exceptions import EnvironmentVaribleNotFound, ParseEnvParsingError
from granular_configuration.yaml import loads


def test_scalar__string() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "test me"}):
        assert loads("!ParseEnv unreal_env_variable") == "test me"


def test_scalar__float() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "3.0"}):
        assert loads("!ParseEnv unreal_env_variable") == 3.0
        assert isinstance(loads("!ParseEnv unreal_env_variable"), float)


def test_scalar__int() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "3"}):
        assert loads("!ParseEnv unreal_env_variable") == 3
        assert isinstance(loads("!ParseEnv unreal_env_variable"), int)


def test_scalar__float_string() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "'3'"}):
        assert loads("!ParseEnv unreal_env_variable") == "3"


def test_scalar__null() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "null"}):
        assert loads("!ParseEnv unreal_env_variable") is None


def test_scalar__bool_true() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "true"}):
        assert loads("!ParseEnv unreal_env_variable") is True


def test_scalar__bool_true_casing() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "True"}):
        assert loads("!ParseEnv unreal_env_variable") is True


def test_scalar__bool_false() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "false"}):
        assert loads("!ParseEnv unreal_env_variable") is False


def test_scalar__bool_false_casing() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "False"}):
        assert loads("!ParseEnv unreal_env_variable") is False


def test_scalar__dict() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": '{"a": "value"}'}):
        assert loads("!ParseEnv unreal_env_variable") == {"a": "value"}


def test_scalar__Configuration() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": '{"a": {"b": "value"}}'}):
        value = loads("!ParseEnv unreal_env_variable")
        assert isinstance(value, Configuration)
        assert value == {"a": {"b": "value"}}
        assert isinstance(value["a"], Configuration)


def test_scalar__seq() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "[1, 2, 3]"}):
        assert loads("!ParseEnv unreal_env_variable", mutable=True) == [1, 2, 3]
        assert loads("!ParseEnv unreal_env_variable", mutable=False) == (1, 2, 3)


def test_scalar__recursive() -> None:
    with patch.dict(
        os.environ, values={"unreal_env_variable": "!ParseEnv unreal_env_variable1", "unreal_env_variable1": "42"}
    ):
        assert loads("!ParseEnv unreal_env_variable") == 42


def test_sequence__use_default() -> None:
    with patch.dict(os.environ, values={}):
        assert loads('!ParseEnv ["unreal_env_vari", 1]') == 1
        assert loads('!ParseEnv ["unreal_env_vari", 1.5]') == 1.5
        assert loads('!ParseEnv ["unreal_env_vari", abc]') == "abc"
        assert loads('!ParseEnv ["unreal_env_vari", null]') is None
        assert loads('!ParseEnv ["unreal_env_vari", false]') is False
        value = loads('!ParseEnv ["unreal_env_vari", {"a": {"b": "value"}}]')
        assert isinstance(value, Configuration)
        assert value == {"a": {"b": "value"}}
        assert isinstance(value["a"], Configuration)


def test_sequence__string() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "test me"}):
        assert loads("!ParseEnv [unreal_env_variable, null]") == "test me"


def test_sequence__float() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "3.0"}):
        assert loads("!ParseEnv [unreal_env_variable, null]") == 3.0
        assert isinstance(loads("!ParseEnv [unreal_env_variable, null]"), float)


def test_sequence__int() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "3"}):
        assert loads("!ParseEnv [unreal_env_variable, null]") == 3
        assert isinstance(loads("!ParseEnv [unreal_env_variable, null]"), int)


def test_safe_sequence__use_default() -> None:
    with patch.dict(os.environ, values={}):
        assert loads('!ParseEnvSafe ["unreal_env_vari", 1]') == 1
        assert loads('!ParseEnvSafe ["unreal_env_vari", 1.5]') == 1.5
        assert loads('!ParseEnvSafe ["unreal_env_vari", abc]') == "abc"
        assert loads('!ParseEnvSafe ["unreal_env_vari", null]') is None
        assert loads('!ParseEnvSafe ["unreal_env_vari", false]') is False
        value = loads('!ParseEnvSafe ["unreal_env_vari", {"a": {"b": "value"}}]')
        assert isinstance(value, Configuration)
        assert value == {"a": {"b": "value"}}
        assert isinstance(value["a"], Configuration)


def test_safe_sequence__string() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "test me"}):
        assert loads("!ParseEnvSafe [unreal_env_variable, null]") == "test me"


def test_safe_sequence__float() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "3.0"}):
        assert loads("!ParseEnvSafe [unreal_env_variable, null]") == 3.0
        assert isinstance(loads("!ParseEnvSafe [unreal_env_variable, null]"), float)


def test_safe_sequence__int() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "3"}):
        assert loads("!ParseEnvSafe [unreal_env_variable, null]") == 3
        assert isinstance(loads("!ParseEnvSafe [unreal_env_variable, null]"), int)


def product_pylance_helper(*iterable: typ.Iterable[bool]) -> typ.Iterator[typ.Iterable[bool]]:
    return product(*iterable)


def test_nested_parse_env_default() -> None:
    test_data = """\
aws_region: !ParseEnv
- G_ASYNC_KINESIS_AWS_REGION
- !ParseEnv [AWS_DEFAULT_REGION, us-east-1]
"""

    with patch.dict(os.environ, values={"unreal_env_variable": "test me"}):
        output: Configuration = loads(test_data)
        assert getattr(output, "aws_region") == "us-east-1"


def test_nested_parse_env_nested_env() -> None:
    test_data = """\
aws_region: !ParseEnv
- G_ASYNC_KINESIS_AWS_REGION
- !ParseEnv [AWS_DEFAULT_REGION, us-east-1]
"""

    with patch.dict(os.environ, values={"AWS_DEFAULT_REGION": "test me"}):
        output: Configuration = loads(test_data)
        assert getattr(output, "aws_region") == "test me"


def test_nested_parse_env_env() -> None:
    test_data = """\
aws_region: !ParseEnv
- G_ASYNC_KINESIS_AWS_REGION
- !ParseEnv [AWS_DEFAULT_REGION, us-east-1]
"""

    with patch.dict(os.environ, values={"G_ASYNC_KINESIS_AWS_REGION": "test me"}):
        output: Configuration = loads(test_data)
        assert getattr(output, "aws_region") == "test me"


def test_nested_parse_env_with_sub_jsonpath() -> None:
    test_data = """\
aws_region: !ParseEnv
- G_ASYNC_KINESIS_AWS_REGION
- !ParseEnv [AWS_DEFAULT_REGION, us-east-1]
sub: data
"""

    with patch.dict(os.environ, values={"G_ASYNC_KINESIS_AWS_REGION": "!Sub ${$.sub}"}):
        output: Configuration = loads(test_data)
        assert getattr(output, "aws_region") == "data"


def test_parsing_bad_data_throws_exception() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "{"}):
        with pytest.raises(ParseEnvParsingError):
            loads("!ParseEnv unreal_env_variable")


def test_missing_env_var_throws_exception() -> None:
    with patch.dict(os.environ, values={}):
        with pytest.raises(EnvironmentVaribleNotFound):
            loads("!ParseEnv unreal_env_vari")


def test_parse_env_safe_with_a_tag_fails() -> None:
    with patch.dict(
        os.environ, values={"unreal_env_variable": "!ParseEnv unreal_env_variable1", "unreal_env_variable1": "42"}
    ):
        with pytest.raises(ParseEnvParsingError):
            loads("!ParseEnvSafe unreal_env_variable")
