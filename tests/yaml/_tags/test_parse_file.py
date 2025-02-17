from __future__ import annotations

import os
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from granular_configuration_language import LazyLoadConfiguration
from granular_configuration_language.exceptions import ParsingTriedToCreateALoop
from granular_configuration_language.yaml import loads

ASSET_DIR = (Path(__file__).parent / "../../assets/" / "merging_and_parsefile").resolve()


def test_loading_a_file() -> None:
    assert LazyLoadConfiguration(ASSET_DIR / "parsefile1.yaml").config.as_dict() == {
        "base": {"a": "from parsefile2.yaml", "b": "From parsefile1.yaml"},
        "data": "From parsefile1.yaml",
        "reach_in": "From parsefile1.yaml",
    }


def test_loading_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        loads("!ParseFile does_not_exist.yaml", file_path=ASSET_DIR / "dummy.yaml")


def test_redirect_loading() -> None:
    config = LazyLoadConfiguration(ASSET_DIR / "redirect_parsefile.yaml")
    expect = {
        "base": {"a": "from parsefile2.yaml", "b": "From parsefile1.yaml"},
        "data": "From parsefile1.yaml",
        "reach_in": "From parsefile1.yaml",
    }
    assert config.config == expect


def test_redirect_loading_with_sub_syntax() -> None:
    assert (
        loads(
            """
file: parsefile1.yaml
contents: !ParseFile ${/file}
"data": "From parse_redirct.yaml"
"base": {"b": "From parse_redirct.yaml"}
""",
            file_path=ASSET_DIR / "dummy.yaml",
        ).as_dict()
        == {
            "file": "parsefile1.yaml",
            "contents": {
                "base": {"a": "from parsefile2.yaml", "b": "From parse_redirct.yaml"},
                "data": "From parsefile1.yaml",
                "reach_in": "From parse_redirct.yaml",
            },
            "data": "From parse_redirct.yaml",
            "base": {"b": "From parse_redirct.yaml"},
        }
    )


def test_failing_when_creating_a_loop_of_one() -> None:
    with pytest.raises(ParsingTriedToCreateALoop, match=re.escape("(parsefile_itself.yaml→...)")):
        LazyLoadConfiguration(ASSET_DIR / "parsefile_itself.yaml").config


def test_failing_when_creating_a_loop_of_many() -> None:
    config = LazyLoadConfiguration(ASSET_DIR / "parsefile_chain" / "up/1.yaml").config

    assert config.safe == "1.yaml"
    assert config.next.safe == "2.yaml"
    assert config.next.next.safe == "3.yaml"

    with pytest.raises(ParsingTriedToCreateALoop, match=re.escape("(1.yaml→2.yaml→3.yaml→...)")):
        config.next.next.bad


def test_parsefile_and_parseenv_can_fail_together_in_a_loop_starting_with_a_file() -> None:
    env = dict(
        VAR1="!ParseEnv VAR2",
        VAR2="!ParseEnv VAR3",
        VAR3="!ParseFile " + (ASSET_DIR / "parsefile_chain" / "up/1.yaml").resolve().__str__(),
    )

    with patch.dict(os.environ, values=env):
        with pytest.raises(
            ParsingTriedToCreateALoop,
            match=re.escape("($VAR1→$VAR2→$VAR3→1.yaml→2.yaml→3.yaml→...)"),
        ):
            loads("!ParseEnv VAR1").next.next.bad


def test_parsefile_and_parseenv_can_fail_together_in_a_loop_starting_with_a_var() -> None:
    env = dict(
        VAR1="!ParseEnv VAR2",
        VAR2="!ParseEnv VAR3",
        VAR3="!ParseFile " + (ASSET_DIR / "parsefile_chain" / "up/1.yaml").resolve().__str__(),
    )
    with patch.dict(os.environ, values=env):
        with pytest.raises(
            ParsingTriedToCreateALoop,
            match=re.escape("(1.yaml→2.yaml→3.yaml→$VAR1→$VAR2→$VAR3→...)"),
        ):

            config = LazyLoadConfiguration(ASSET_DIR / "parsefile_chain" / "up/1.yaml").config
            config.next.next.bad_env
