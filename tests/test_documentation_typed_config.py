from __future__ import annotations

from pathlib import Path

from granular_configuration_language import Configuration, LazyLoadConfiguration

ASSET_DIR = (Path(__file__).parent / "assets" / "test_typed_configuration").resolve()


class Setting2Config(Configuration):
    sub_setting1: str


class Config(Configuration):
    setting1: str
    setting2: Setting2Config
    example_of_codes: Configuration[int, str]


def test_as_typed() -> None:
    CONFIG = LazyLoadConfiguration(ASSET_DIR / "documentation.yaml", base_path="example_config").as_typed(Config)

    assert CONFIG.setting1 == "value1"
    assert CONFIG.setting2.sub_setting1 == "sub1"
    assert CONFIG.example_of_codes == Configuration({400: "Bad Request", 404: "Not Found"})


def test_getattr() -> None:
    CONFIG = LazyLoadConfiguration(ASSET_DIR / "documentation.yaml", base_path="example_config")

    assert CONFIG.setting1 == "value1"
    assert CONFIG.setting2.sub_setting1 == "sub1"
    assert CONFIG.example_of_codes == Configuration({400: "Bad Request", 404: "Not Found"})


def test_getitem() -> None:
    CONFIG = LazyLoadConfiguration(ASSET_DIR / "documentation.yaml", base_path="example_config")

    assert CONFIG["setting1"] == "value1"
    assert CONFIG["setting2"]["sub_setting1"] == "sub1"
    assert CONFIG["example_of_codes"] == Configuration({400: "Bad Request", 404: "Not Found"})


def test_typed_get() -> None:
    CONFIG = LazyLoadConfiguration(ASSET_DIR / "documentation.yaml", base_path="example_config")

    assert CONFIG.config.typed_get(str, "setting1") == "value1"
    assert CONFIG.config.typed_get(Configuration, "setting2").typed_get(str, "sub_setting1") == "sub1"
    assert (
        CONFIG.config.typed_get(
            Configuration,
            "example_of_codes",
        )
    ) == Configuration({400: "Bad Request", 404: "Not Found"})


def test_as_dict() -> None:
    CONFIG = LazyLoadConfiguration(ASSET_DIR / "documentation.yaml", base_path="example_config").as_typed(Config)

    assert CONFIG.setting2.as_dict() == {"sub_setting1": "sub1"}


def test_as_json_string() -> None:
    CONFIG = LazyLoadConfiguration(ASSET_DIR / "documentation.yaml", base_path="example_config").as_typed(Config)

    assert CONFIG.setting2.as_json_string() == """{"sub_setting1": "sub1"}"""
