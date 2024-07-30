from pathlib import Path

import pytest

from granular_configuration import LazyLoadConfiguration
from granular_configuration.yaml import loads

ASSET_DIR = (Path(__file__).parent / "../../assets/").resolve()


def test_that_scalar_fails() -> None:
    with pytest.raises(ValueError):
        loads("!Merge abc")


def test_that_mapping_fails() -> None:
    with pytest.raises(ValueError):
        loads("!Merge {}")


def test_merging_string_returns_empty_dict() -> None:
    test = """\
!Merge
- String 1
- String 2
- String 3
"""
    assert loads(test).as_dict() == {}


def test_merging_mix_returns_ignores_nondict() -> None:
    test = """\
!Merge
- String 1
- 1
- 1.0
- true
- a: b
"""
    assert loads(test).as_dict() == {"a": "b"}


def test_merging_three_dicts() -> None:
    test = """\
!Merge
- String 1
- 1
- 1.0
- true
- a: b
- a: c
  d: e
  f: h
- d: i
  j: k
"""
    assert loads(test).as_dict() == {"a": "c", "d": "i", "f": "h", "j": "k"}


def test_merging_one_dict() -> None:
    test = """\
!Merge
- a: b
"""
    assert loads(test).as_dict() == {"a": "b"}


def test_merging_from_files_nested() -> None:
    assert LazyLoadConfiguration(ASSET_DIR / "merge.yaml").config.as_dict() == {
        "basic": "state",
        "merge": {
            "base": {"a": "from parsefile2.yaml", "b": "From merge.yaml"},
            "data": "From parsefile1.yaml",
            "from": "merge",
            "reach_in": "From merge.yaml",
        },
        "data": "From merge.yaml",
        "base": {"b": "From merge.yaml"},
    }


def test_merging_from_files_at_root() -> None:
    assert LazyLoadConfiguration(ASSET_DIR / "merge_root.yaml").config.as_dict() == {
        "base": {"a": "from parsefile2.yaml", "b": "From parsefile1.yaml"},
        "data": "From parsefile1.yaml",
        "from": "merge",
        "reach_in": "From parsefile1.yaml",
    }


def test_redirect_using_merge() -> None:
    config = LazyLoadConfiguration(ASSET_DIR / "redirect_merge.yaml")
    expect = {
        "base": {"a": "from parsefile2.yaml", "b": "From parsefile1.yaml"},
        "data": "From parsefile1.yaml",
        "reach_in": "From parsefile1.yaml",
    }
    assert config.config == expect


def test_merging_with_a_basic_sub_doesnt_fail() -> None:
    test = """\
!Merge
- !Sub String 1
- a: b
"""
    assert loads(test).as_dict() == {"a": "b"}


def test_merging_with_a_env_sub_doesnt_fail() -> None:
    test = """\
!Merge
- !Sub ${doesn't_exists:-default}
- a: b
"""
    assert loads(test).as_dict() == {"a": "b"}


def test_merging_with_a_jsonpath_Sub_fails_on_RecursionError() -> None:
    test = """\
!Merge
- a: b
- !Sub ${$.a}
"""
    with pytest.raises(RecursionError):
        assert loads(test).as_dict() == {"a": "b"}


def test_merging_with_a_jsonpath_ParseFile_fails_on_RecursionError() -> None:
    test = """\
a: b
c: !Merge
    - a: b
    - !ParseFile ${$.c}
"""
    with pytest.raises(RecursionError):
        assert loads(test).as_dict() == {"a": "b"}


def test_merging_with_a_jsonpointer_ParseFile_fails_on_RecursionError() -> None:
    test = """\
a: b
c: !Merge
    - a: b
    - !ParseFile ${/c}
"""
    with pytest.raises(RecursionError):
        assert loads(test).as_dict() == {"a": "b"}
