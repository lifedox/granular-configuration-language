import os
from unittest.mock import patch

from granular_configuration.yaml import loads


def test_loading_from_environment() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "test me"}):
        assert loads("!Env '{{unreal_env_variable}}'") == "test me"
        assert loads("!Env '{{unreal_env_variable:special}}'") == "test me"
        assert loads("!Env '{{unreal_env_vari:special case }}'") == "special case "

