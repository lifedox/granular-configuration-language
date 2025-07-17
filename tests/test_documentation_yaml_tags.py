from __future__ import annotations

from uuid import UUID

from granular_configuration_language.yaml import loads


def test_Del_example1_is_correct() -> None:
    test_data = """\
!Del hidden: &common_setting Some Value
copy1: *common_setting
copy2: *common_setting
"""
    expected = {"copy1": "Some Value", "copy2": "Some Value"}

    assert loads(test_data) == expected


def test_Del_example2_is_correct() -> None:
    test_data = """\
!Del setting_with_tag: &user_id !UUID 83e3c814-2cdf-4fe6-b703-89b0a379759e
user: *user_id
"""
    expected = {"user": UUID("83e3c814-2cdf-4fe6-b703-89b0a379759e")}

    assert loads(test_data) == expected


def test_Del_example2_is_correct_different_order() -> None:
    test_data = """\
!Del setting_with_tag: !UUID &user_id 83e3c814-2cdf-4fe6-b703-89b0a379759e
user: *user_id
"""
    expected = {"user": UUID("83e3c814-2cdf-4fe6-b703-89b0a379759e")}

    assert loads(test_data) == expected
