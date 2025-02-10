from __future__ import annotations

from granular_configuration_language.yaml import loads


def test_del_removes_key() -> None:
    test_data = """\
!Del "I'm gone": &data "I'm data"
"I'm here": *data
"""
    expect = {"I'm here": "I'm data"}

    assert loads(test_data).as_dict() == expect


def test_del_on_non_key_does_alter_the_string() -> None:
    test_data = """\
!Del "I'm gone"
"""
    expect = "I'm gone"

    assert loads(test_data) == expect


def test_del_with_ref_value() -> None:
    test_data = """\
!Del store: &setting !Ref $.a
a: 1
b: *setting
"""
    expect = {"a": 1, "b": 1}

    assert loads(test_data) == expect
