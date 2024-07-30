from pathlib import Path
from granular_configuration import LazyLoadConfiguration, merge

ASSET_DIR = (Path(__file__).parent / "../assets/").resolve()


def test_merging_LazyLoadConfiguration() -> None:
    configs = (
        LazyLoadConfiguration(ASSET_DIR / "parsefile1.yaml"),
        LazyLoadConfiguration(ASSET_DIR / "merge_root.yaml"),
    )
    assert merge(configs).as_dict() == {
        "base": {"a": "from parsefile2.yaml", "b": "From parsefile1.yaml"},
        "data": "From parsefile1.yaml",
        "from": "merge",
        "reach_in": "From parsefile1.yaml",
    }
