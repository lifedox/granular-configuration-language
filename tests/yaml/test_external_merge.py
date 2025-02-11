from __future__ import annotations

from pathlib import Path

from granular_configuration_language import (
    Configuration,
    LazyLoadConfiguration,
    MutableConfiguration,
    MutableLazyLoadConfiguration,
    merge,
)

ASSET_DIR = (Path(__file__).parent / "../assets/" / "merging_and_parsefile").resolve()


def test_merging_LazyLoadConfiguration() -> None:
    configs = (
        LazyLoadConfiguration(ASSET_DIR / "parsefile1.yaml"),
        MutableLazyLoadConfiguration(ASSET_DIR / "merge_root.yaml"),
    )
    assert merge(configs).as_dict() == {
        "base": {"a": "from parsefile2.yaml", "b": "From parsefile1.yaml"},
        "data": "From parsefile1.yaml",
        "from": "merge",
        "reach_in": "From parsefile1.yaml",
    }


def test_merging_SafeConfigurationProxy() -> None:
    configs = (
        LazyLoadConfiguration(ASSET_DIR / "parsefile1.yaml").as_typed(Configuration),
        LazyLoadConfiguration(ASSET_DIR / "merge_root.yaml"),
    )
    assert merge(configs).as_dict() == {
        "base": {"a": "from parsefile2.yaml", "b": "From parsefile1.yaml"},
        "data": "From parsefile1.yaml",
        "from": "merge",
        "reach_in": "From parsefile1.yaml",
    }


def test_merging_paths_immutably() -> None:
    configs = (
        (ASSET_DIR / "parsefile1.yaml"),
        (ASSET_DIR / "merge_root.yaml"),
    )
    config = merge(configs)
    assert isinstance(config, Configuration)
    assert config.as_dict() == {
        "base": {"a": "from parsefile2.yaml", "b": "From parsefile1.yaml"},
        "data": "From parsefile1.yaml",
        "from": "merge",
        "reach_in": "From parsefile1.yaml",
    }


def test_merging_paths_mutably() -> None:
    configs = (
        (ASSET_DIR / "parsefile1.yaml"),
        (ASSET_DIR / "merge_root.yaml"),
    )
    config = merge(configs, mutable=True)
    assert isinstance(config, MutableConfiguration)
    assert config.as_dict() == {
        "base": {"a": "from parsefile2.yaml", "b": "From parsefile1.yaml"},
        "data": "From parsefile1.yaml",
        "from": "merge",
        "reach_in": "From parsefile1.yaml",
    }


def test_ref_cannot_cross_loading_boundary() -> None:
    # Merging three separate `LazyLoadConfiguration` instances
    config = merge(sorted((ASSET_DIR / "ref_cannot_cross_loading_boundary").glob("*.yaml")))

    assert config.as_dict() == {
        "test": {
            1: "I came from 1.yaml",
            2: "I came from 2.yaml",
            3: "I came from 3.yaml",
        },
        "ref": "I came from 3.yaml",
    }

    # One `LazyLoadConfiguration` merging three files
    config = LazyLoadConfiguration(*sorted((ASSET_DIR / "ref_cannot_cross_loading_boundary").glob("*.yaml"))).config

    assert config.as_dict() == {
        "test": {
            1: "I came from 3.yaml",
            2: "I came from 3.yaml",
            3: "I came from 3.yaml",
        },
        "ref": "I came from 3.yaml",
    }

    # !Merge
    config = LazyLoadConfiguration(ASSET_DIR / "ref_cannot_cross_loading_boundary.yaml").config

    assert config.as_dict() == {
        "test": {
            1: "I came from 3.yaml",
            2: "I came from 3.yaml",
            3: "I came from 3.yaml",
        },
        "ref": "I came from 3.yaml",
    }
