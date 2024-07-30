import os
from unittest.mock import patch

from granular_configuration import Configuration
from granular_configuration.yaml import loads


def test_loading_env_var() -> None:
    with patch.dict(os.environ, values={"unreal_env_variable": "test me"}):
        assert loads("!Sub ${unreal_env_variable}") == "test me"
        assert loads("!Sub ${unreal_env_variable:-special}") == "test me"
        assert loads("!Sub ${unreal_env_vari:-special case }") == "special case "


def test_using_jsonpath() -> None:
    test_data = """\
data:
    dog:
        name: nitro
    cat:
        name: never owned a cat
tests:
    a: !Sub ${$.data.dog.name}
    b: !Sub ${$.data.dog}
    c: !Sub ${$.data.*.name}
    d: !Sub ${unreal_env_variable} ${$.data.dog.name} ${unreal_env_vari:-defaulting value}
"""

    with patch.dict(os.environ, values={"unreal_env_variable": "test me"}):
        output: Configuration = loads(test_data, obj_pairs_hook=Configuration)
        assert output.tests.as_dict() == dict(
            a="nitro",
            b="{'name': 'nitro'}",
            c="['nitro', 'never owned a cat']",
            d="test me nitro defaulting value",
        )

