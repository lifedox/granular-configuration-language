from __future__ import annotations

from pathlib import Path

import pytest

from granular_configuration_language import Configuration, LazyLoadConfiguration
from granular_configuration_language.exceptions import ParsingTriedToCreateALoop
from granular_configuration_language.yaml import loads

ASSET_DIR = (Path(__file__).parent / "../../assets/" / "test_eager_parse_file").resolve()


def test_simple_loading() -> None:
    assert loads("!EagerParseFile simple.yaml", file_path=ASSET_DIR / "dummy.yaml") == "simple.yaml"


def test_simple_loading_with_optional() -> None:
    assert loads("!EagerOptionalParseFile simple.yaml", file_path=ASSET_DIR / "dummy.yaml") == "simple.yaml"


def test_loading_a_file() -> None:
    assert LazyLoadConfiguration(ASSET_DIR / "parsefile1.yaml").eager_load(Configuration).as_dict() == {
        "base": {"a": "from parsefile2.yaml", "b": "From parsefile1.yaml"},
        "data": "From parsefile1.yaml",
        "reach_in": "From parsefile1.yaml",
    }


def test_loading_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        loads("!EagerParseFile does_not_exist.yaml", file_path=ASSET_DIR / "dummy.yaml")


def test_loading_missing_file_with_optional() -> None:
    assert loads("!EagerOptionalParseFile does_not_exist.yaml", file_path=ASSET_DIR / "dummy.yaml") is None


def test_redirect_loading() -> None:
    config = LazyLoadConfiguration(ASSET_DIR / "redirect_parsefile.yaml")
    expect = {
        "base": {"a": "from parsefile2.yaml", "b": "From parsefile1.yaml"},
        "data": "From parsefile1.yaml",
        "reach_in": "From parsefile1.yaml",
    }
    assert config.config == expect


def test_failing_when_creating_a_loop_of_one() -> None:
    with pytest.raises(ParsingTriedToCreateALoop):
        LazyLoadConfiguration(ASSET_DIR / "parsefile_itself.yaml").eager_load(Configuration).as_dict()


def test_failing_when_creating_a_loop_of_many() -> None:
    config = LazyLoadConfiguration(ASSET_DIR / "parsefile_chain" / "up/1.yaml").eager_load(Configuration)

    assert config.safe == "1.yaml"
    assert config.next.safe == "2.yaml"
    assert config.next.next.safe == "3.yaml"

    with pytest.raises(ParsingTriedToCreateALoop):
        config.next.next.bad
