from pathlib import Path

import pytest

from granular_configuration import LazyLoadConfiguration
from granular_configuration.yaml import loads

ASSET_DIR = (Path(__file__).parent / "../../assets/" / "merging_and_parsefile").resolve()


def test_parsefile_loading() -> None:
    assert LazyLoadConfiguration(ASSET_DIR / "parsefile1.yaml").config.as_dict() == {
        "base": {"a": "from parsefile2.yaml", "b": "From parsefile1.yaml"},
        "data": "From parsefile1.yaml",
        "reach_in": "From parsefile1.yaml",
    }


def test_parsefile_loading_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        loads("!ParseFile does_not_exist.yaml", file_path=ASSET_DIR / "dummy.yaml")


def test_parsefile_redirect_loading() -> None:
    config = LazyLoadConfiguration(ASSET_DIR / "redirect_parsefile.yaml")
    expect = {
        "base": {"a": "from parsefile2.yaml", "b": "From parsefile1.yaml"},
        "data": "From parsefile1.yaml",
        "reach_in": "From parsefile1.yaml",
    }
    assert config.config == expect


def test_parsefile_redirect_loading_sub_syntax() -> None:
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
