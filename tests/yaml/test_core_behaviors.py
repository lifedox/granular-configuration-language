import copy
from datetime import date

from granular_configuration import Configuration
from granular_configuration.yaml import LazyEval, loads


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
    lazy_eval: LazyEval = next(config._raw_items())[1]

    copy1 = copy.copy(lazy_eval)
    copy2 = copy.deepcopy(lazy_eval)
    assert copy1 is lazy_eval
    assert copy2 is lazy_eval

    config_copy = copy.deepcopy(config)

    assert config.a == date(2012, 10, 31)

    copy3: LazyEval = next(config_copy._raw_items())[1]
    assert copy3 is lazy_eval

    assert config_copy.a == date(2012, 10, 31)
