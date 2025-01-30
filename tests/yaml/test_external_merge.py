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
