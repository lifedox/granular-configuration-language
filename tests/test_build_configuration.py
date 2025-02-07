import gc
import re
from pathlib import Path

import pytest

from granular_configuration_language import Configuration, LazyLoadConfiguration, merge
from granular_configuration_language.exceptions import PlaceholderConfigurationError
from granular_configuration_language.yaml import Placeholder

ASSET_DIR = (Path(__file__).parent / "assets" / "test_build_configuration").resolve()


def test_mapping_can_override_a_placeholder() -> None:
    files = (
        ASSET_DIR / "placeholder_test1.yaml",
        ASSET_DIR / "placeholder_test2.yaml",
    )

    configuration = LazyLoadConfiguration(*files).config

    assert isinstance(configuration, Configuration)

    assert configuration.a == {"key1": "value1", "key2": "value2"}

    raw_value = dict(configuration._raw_items())

    assert isinstance(raw_value["b"], Placeholder) and (raw_value["b"].message == "Placeholder over a placeholder")
    assert isinstance(raw_value["c"], Placeholder) and (raw_value["c"].message == "Placeholder over a value")

    with pytest.raises(
        PlaceholderConfigurationError,
        match=re.escape('!Placeholder at `$.b` was not overwritten. Message: "Placeholder over a placeholder"'),
    ):
        configuration.b


def test_mapping_can_override_a_value() -> None:
    files = (ASSET_DIR / "sub_test2.yaml",)
    injected_before = Configuration(injected=False, flags="flags")
    injected_after = Configuration(injected=True, flags=Configuration(defaults="injected"))

    config = merge((injected_before, LazyLoadConfiguration(*files), injected_after))

    assert config.injected is True
    assert config.flags.defaults == "injected"


def test_injection() -> None:
    files = (ASSET_DIR / "sub_test2.yaml",)
    injected_before = Configuration(injected=False, flags="flags")
    injected_after = Configuration(injected=True, flags=Configuration(defaults="injected"))

    llc = LazyLoadConfiguration(*files, inject_before=injected_before, inject_after=injected_after)

    gc.collect()

    assert len(gc.get_referrers(injected_after)) == 1
    assert len(gc.get_referrers(injected_before)) == 1

    config = llc.config

    assert config.injected is True
    assert config.flags.defaults == "injected"

    gc.collect()

    assert len(gc.get_referrers(injected_after)) == 0
    assert len(gc.get_referrers(injected_before)) == 0
