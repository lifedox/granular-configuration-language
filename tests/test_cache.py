from pathlib import Path

from granular_configuration import LazyLoadConfiguration
from granular_configuration._cache import store

ASSET_DIR = (Path(__file__).parent / "assets" / "test_cache").resolve()


def test_shared_config() -> None:
    c1 = LazyLoadConfiguration(ASSET_DIR / "1.yaml")
    c2 = LazyLoadConfiguration(ASSET_DIR / "1.yaml")

    assert len(store) == 1, repr(dict(store))

    config1 = c1.config

    assert len(store) == 1, repr(dict(store))

    assert config1 is c2.config

    assert len(store) == 0, repr(dict(store))

    assert c2.config == {"a": 1}


def test_shared_config_when_disable_caching() -> None:
    c1 = LazyLoadConfiguration(ASSET_DIR / "1.yaml", disable_caching=True)
    c2 = LazyLoadConfiguration(ASSET_DIR / "1.yaml", disable_caching=True)

    assert len(store) == 0, repr(dict(store))

    config1 = c1.config

    assert len(store) == 0, repr(dict(store))

    assert config1 == c2.config
    assert config1 is not c2.config

    assert len(store) == 0, repr(dict(store))

    assert c2.config == {"a": 1}
