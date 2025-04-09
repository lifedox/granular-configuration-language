from __future__ import annotations

from pathlib import Path

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


def test_loading_missing_file_with_optional_is_none() -> None:
    assert loads("!OptionalParseFile does_not_exist.yaml", file_path=ASSET_DIR / "dummy.yaml") is None


def test_redirect_loading() -> None:
    config = LazyLoadConfiguration(ASSET_DIR / "redirect_parsefile.yaml")
    expect = {
        "base": {"a": "from parsefile2.yaml", "b": "From parsefile1.yaml"},
        "data": "From parsefile1.yaml",
        "reach_in": "From parsefile1.yaml",
    }
    assert config.config == expect


def test_redirect_loading_with_sub_syntax() -> None:
    assert loads(
        """
file: parsefile1.yaml
contents: !ParseFile ${/file}
"data": "From parse_redirct.yaml"
"base": {"b": "From parse_redirct.yaml"}
""",
        file_path=ASSET_DIR / "dummy.yaml",
    ).as_dict() == {
        "file": "parsefile1.yaml",
        "contents": {
            "base": {"a": "from parsefile2.yaml", "b": "From parse_redirct.yaml"},
            "data": "From parsefile1.yaml",
            "reach_in": "From parse_redirct.yaml",
        },
        "data": "From parse_redirct.yaml",
        "base": {"b": "From parse_redirct.yaml"},
    }


def test_failing_when_creating_a_loop_of_one() -> None:
    with pytest.raises(ParsingTriedToCreateALoop):
        LazyLoadConfiguration(ASSET_DIR / "parsefile_itself.yaml").config


def test_failing_when_creating_a_loop_of_many() -> None:
    config = LazyLoadConfiguration(ASSET_DIR / "parsefile_chain" / "up/1.yaml").config

    assert config.safe == "1.yaml"
    assert config.next.safe == "2.yaml"
    assert config.next.next.safe == "3.yaml"

    with pytest.raises(ParsingTriedToCreateALoop):
        config.next.next.bad
