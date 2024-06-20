from pathlib import Path

import pytest

from granular_configuration import Configuration, LazyLoadConfiguration, merge
from granular_configuration.yaml_handler import loads

ASSET_DIR = (Path(__file__).parent / "../assets/config_location_test").resolve()


def test_that_scalar_fails() -> None:
    with pytest.raises(ValueError):
        loads("!Merge abc")


def test_that_mapping_fails() -> None:
    with pytest.raises(ValueError):
        loads("!Merge {}")


def test_merging_string_returns_empty_dict() -> None:
    test = """\
!Merge
- String 1
- String 2
- String 3
"""
    assert loads(test, obj_pairs_hook=Configuration).run().as_dict() == {}


def test_merging_mix_returns_ignores_nondict() -> None:
    test = """\
!Merge
- String 1
- 1
- 1.0
- true
- a: b
"""
    assert loads(test, obj_pairs_hook=Configuration).run().as_dict() == {"a": "b"}


def test_merging_three_dicts() -> None:
    test = """\
!Merge
- String 1
- 1
- 1.0
- true
- a: b
- a: c
  d: e
  f: h
- d: i
  j: k
"""
    assert loads(test, obj_pairs_hook=Configuration).run().as_dict() == {"a": "c", "d": "i", "f": "h", "j": "k"}


def test_merging_one_dict() -> None:
    test = """\
!Merge
- a: b
"""
    assert loads(test, obj_pairs_hook=Configuration).run().as_dict() == {"a": "b"}


def test_merging_from_files_nested() -> None:
    assert LazyLoadConfiguration(ASSET_DIR / "merge.yaml").config.as_dict() == {
        "basic": "state",
        "merge": {
            "base": {"a": "from parsefile2.yaml", "b": "$.data"},
            "data": "From parsefile1.yaml",
            "from": "merge",
        },
    }


def test_merging_from_files_at_root() -> None:
    assert LazyLoadConfiguration(ASSET_DIR / "merge_root.yaml").config.as_dict() == {
        "base": {"a": "from parsefile2.yaml", "b": "$.data"},
        "data": "From parsefile1.yaml",
        "from": "merge",
    }


def test_parsefile_loading() -> None:
    assert LazyLoadConfiguration(ASSET_DIR / "parsefile1.yaml").config.as_dict() == {
        "base": {"a": "from parsefile2.yaml", "b": "$.data"},
        "data": "From parsefile1.yaml",
    }


def test_parsefile_loading_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        loads("!ParseFile does_not_exist.yaml", obj_pairs_hook=Configuration, file_path=ASSET_DIR / "dummy.yaml").run()


def test_parsefile_redirect_loading() -> None:
    assert loads(
        "!ParseFile parsefile1.yaml", obj_pairs_hook=Configuration, file_path=ASSET_DIR / "dummy.yaml"
    ).run() == {
        "base": {"a": "from parsefile2.yaml", "b": "$.data"},
        "data": "From parsefile1.yaml",
    }


def test_merging_LazyLoadConfiguration() -> None:
    configs = (
        LazyLoadConfiguration(ASSET_DIR / "parsefile1.yaml"),
        LazyLoadConfiguration(ASSET_DIR / "merge_root.yaml"),
    )
    assert merge(configs).as_dict() == {
        "base": {"a": "from parsefile2.yaml", "b": "$.data"},
        "data": "From parsefile1.yaml",
        "from": "merge",
    }
