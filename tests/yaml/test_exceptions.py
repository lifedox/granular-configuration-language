import os
from unittest.mock import patch

import pytest

from granular_configuration.yaml import loads


def test_string_tag_does_not_take_sequence() -> None:
    with pytest.raises(ValueError):
        loads("!Mask []")


def test_string_tag_does_not_take_mapping() -> None:
    with pytest.raises(ValueError):
        loads("!Mask {}")


def test_twople_only_takes_two() -> None:
    with pytest.raises(ValueError):
        loads("""!ParseEnv ["a", "b", "c"]""")


def test_twople_does_not_take_mapping() -> None:
    with patch.dict(os.environ, values={}):
        with pytest.raises(ValueError):
            loads('!ParseEnv {"unreal_env_vari": 1}')
