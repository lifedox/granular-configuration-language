import os
from functools import partial
from unittest.mock import patch

import pytest

from granular_configuration import Configuration
from granular_configuration.exceptions import JSONPathMustStartFromRoot, JSONPathOnlyWorksOnMappings, ParseEnvError
from granular_configuration.yaml import loads

loads = partial(loads, obj_pairs_hook=Configuration)


def test_string_is_scalar_exception() -> None:
    with pytest.raises(ValueError):
        loads("!Mask []")


def test_twople_is_only_two_exception() -> None:
    with pytest.raises(ValueError):
        loads("""!ParseEnv ["a", "b", "c"]""")


def test_parse_env_scalar__var_parse_error() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "{"}):
        with pytest.raises(ParseEnvError):
            loads("!ParseEnv unreal_env_variable")


def test_parse_env_scalar__missing() -> None:
    with patch.dict(os.environ, values={}):
        with pytest.raises(KeyError):
            loads("!ParseEnv unreal_env_vari")


def test_parse_env_mapping__error() -> None:
    with patch.dict(os.environ, values={}):
        with pytest.raises(ValueError):
            loads('!ParseEnv {"unreal_env_vari": 1}')


def test_env() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "test me"}):
        with pytest.raises(KeyError):
            loads("!Env '{{unreal_env_vari}}'")

        with pytest.raises(ValueError):
            loads("!Env [a]")


def test_func() -> None:
    with pytest.raises(ValueError):
        loads("!Func unreal.garbage.func")

    with pytest.raises(ValueError):
        loads("!Func sys.stdout")

    with pytest.raises(ValueError):
        loads("!Func [a]")


def test_class() -> None:
    with pytest.raises(ValueError):
        loads("!Class functools.reduce")

    with pytest.raises(ValueError):
        loads("!Class unreal.garbage.func")

    with pytest.raises(ValueError):
        loads("!Class [a]")


def test_placeholder() -> None:
    with pytest.raises(ValueError):
        loads("!Placeholder []")


def test_parse_env_safe_with_a_tag_fails() -> None:
    with patch.dict(
        os.environ, values={"unreal_env_variable": "!ParseEnv unreal_env_variable1", "unreal_env_variable1": "42"}
    ):
        with pytest.raises(ParseEnvError):
            loads("!ParseEnvSafe unreal_env_variable")


def test_sub__env() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "test me"}):

        with pytest.raises(KeyError):
            loads("!Sub ${unreal_env_vari}")

        with pytest.raises(ValueError):
            loads("!Sub [a]")


def test_sub__jsonpath_missing() -> None:
    test_data = """
a: !Sub ${$.no_data.here}
b: c
"""
    with pytest.raises(KeyError):
        loads(test_data).as_dict()


def test_sub__jsonpath_on_a_scalar_value_makes_no_sense_and_must_fail() -> None:
    test_data = """!Sub ${$.no_data.here}
"""
    with pytest.raises(JSONPathOnlyWorksOnMappings):
        loads(test_data)


def test_ref__jsonpath_missing() -> None:
    test_data = """
a: !Ref $.no_data.here
b: c
"""
    with pytest.raises(KeyError):
        loads(test_data).as_dict()


def test_ref__jsonpointer_missing() -> None:
    test_data = """
a: !Ref /no_data/here
b: c
"""
    with pytest.raises(KeyError):
        assert (
            loads(test_data).as_dict()
            == {}
        )


def test_ref__syntax_Error() -> None:
    test_data = """
a: !Ref no_data/here
b: c
"""
    with pytest.raises(JSONPathMustStartFromRoot):
        assert (
            loads(test_data).as_dict()
            == {}
        )
