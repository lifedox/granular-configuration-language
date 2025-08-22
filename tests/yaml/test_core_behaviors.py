from __future__ import annotations

import copy
import os
import re
from datetime import date
from unittest.mock import Mock, patch

import pytest

from granular_configuration_language import Configuration
from granular_configuration_language.exceptions import EnvironmentVaribleNotFound
from granular_configuration_language.yaml import LazyEval, loads
from granular_configuration_language.yaml.decorators.interpolate._interpolate import interpolate


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
    assert loads(test).as_dict() == {
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
    assert loads(test).as_dict() == {
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
    assert loads(test, mutable=True) == {
        True: ["y", "yes", "on"],
        False: ["n", "no", "off"],
        "old_octal": 10,
        "real_octal": 8,
        "number": 1000,  # Technicality YAML 1.1 behavior, but Python3 behavior
        "slash": "/",
    }
    assert loads(test) == {
        True: ("y", "yes", "on"),
        False: ("n", "no", "off"),
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
    assert loads(test, mutable=True) == {
        True: [True, True, True],
        False: [False, False, False],
        "old_octal": 8,
        "real_octal": "0o010",
        "number": 1000,
        "slash": "/",  # Technicality YAML 1.2 behavior
    }
    assert loads(test) == {
        True: (True, True, True),
        False: (False, False, False),
        "old_octal": 8,
        "real_octal": "0o010",
        "number": 1000,
        "slash": "/",  # Technicality YAML 1.2 behavior
    }


def test_empty_is_null() -> None:
    assert loads("") is None


def test_LazyEval_does_not_copy() -> None:
    config: Configuration = loads("a: !Date 20121031")
    lazy_eval: LazyEval[date] = next(config._raw_items())[1]
    assert isinstance(lazy_eval, LazyEval)

    copy1 = copy.copy(lazy_eval)
    copy2 = copy.deepcopy(lazy_eval)
    assert copy1 is lazy_eval
    assert copy2 is lazy_eval

    config_copy = copy.deepcopy(config)

    assert config.a == date(2012, 10, 31)
    assert config.a is lazy_eval.result

    copy3: LazyEval[date] = next(config_copy._raw_items())[1]
    assert copy3 is lazy_eval

    assert config_copy.a == date(2012, 10, 31)
    assert config_copy.a is lazy_eval.result


def test_LazyEval_result_runs_once() -> None:
    config: Configuration = loads("a: !Date 20121031")
    lazy_eval: LazyEval[date] = next(config._raw_items())[1]
    assert isinstance(lazy_eval, LazyEval)

    with patch.object(lazy_eval, "_run", new=Mock(side_effect=lazy_eval._run)) as mock:
        # Get the result a multiple times
        result = lazy_eval.result
        result = lazy_eval.result
        result = lazy_eval.result

        # Simulation a two-threads calling before property is cached by removing the cached value
        del lazy_eval.result

        assert lazy_eval.result is result

        mock.assert_called_once()


def test_LazyEval_keys_throw_errors() -> None:
    with pytest.raises(TypeError, match="keys to mappings"):
        loads("""
!Date 20121031: date
""")


def test_interpolatations_starting_with_slash_without_root_error_with_env_var() -> None:
    with patch.dict(os.environ, values={}), pytest.raises(EnvironmentVaribleNotFound, match=re.escape("'/file'")):
        interpolate("${/file}", None)


def test_interpolatations_starting_with_dollar_without_root_error_with_env_var() -> None:
    with patch.dict(os.environ, values={}), pytest.raises(EnvironmentVaribleNotFound, match=re.escape("'$file'")):
        interpolate("${$file}", None)
