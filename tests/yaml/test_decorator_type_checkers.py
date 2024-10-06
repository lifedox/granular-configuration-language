import os
from unittest.mock import patch

import pytest

from granular_configuration_language.yaml import loads


def test_string_tag_does_not_take_sequence() -> None:
    with pytest.raises(ValueError):
        loads("!Mask []")


def test_string_tag_does_not_take_mapping() -> None:
    with pytest.raises(ValueError):
        loads("!Mask {}")


def test_string_or_twople_tag_only_takes_two() -> None:
    with patch.dict(os.environ, values={}):
        with pytest.raises(ValueError):
            loads("""!ParseEnv ["a", "b", "c"]""")

        with pytest.raises(ValueError):
            loads("""!ParseEnv ["a"]""")


def test_string_or_twople_tag_does_not_take_mapping() -> None:
    with patch.dict(os.environ, values={}):
        with pytest.raises(ValueError):
            loads('!ParseEnv {"unreal_env_vari": 1}')


def test_sequence_of_any_tag_does_not_take_scalar() -> None:
    with pytest.raises(ValueError):
        loads("!Merge abc")


def test_sequence_of_any_tag_does_not_take_mapping() -> None:
    with pytest.raises(ValueError):
        loads("!Merge {}")


def test_mapping_of_any_tag_does_not_take_scalar() -> None:
    with pytest.raises(ValueError):
        loads("!Dict abc")


def test_mapping_of_any_tag_does_not_take_mapping() -> None:
    with pytest.raises(ValueError):
        loads("!Dict []")
