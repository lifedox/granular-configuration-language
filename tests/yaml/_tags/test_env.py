from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from granular_configuration_language.exceptions import EnvironmentVaribleNotFound
from granular_configuration_language.yaml import loads


def test_loading_from_environment() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "test me"}):
        assert loads("!Env '{{unreal_env_variable}}'") == "test me"
        assert loads("!Env '{{unreal_env_variable:special}}'") == "test me"
        assert loads("!Env '{{unreal_env_vari:special case }}'") == "special case "


def test_missing_env_var_throws_exception() -> None:
    with patch.dict(os.environ, values={}):
        with pytest.raises(EnvironmentVaribleNotFound):
            loads("!Env '{{unreal_env_variable}}'")
