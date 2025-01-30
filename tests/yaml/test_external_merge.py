from pathlib import Path

from granular_configuration_language import merge

ASSET_DIR = (Path(__file__).parent / "../assets/" / "merging_and_parsefile").resolve()


def test_merging_LazyLoadConfiguration() -> None:
    configs = (
        (ASSET_DIR / "parsefile1.yaml"),
        (ASSET_DIR / "merge_root.yaml"),
    )
    assert merge(configs).as_dict() == {
        "base": {"a": "from parsefile2.yaml", "b": "From parsefile1.yaml"},
        "data": "From parsefile1.yaml",
        "from": "merge",
        "reach_in": "From parsefile1.yaml",
    }
