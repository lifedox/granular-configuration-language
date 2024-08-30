import re
from pathlib import Path

import pytest

from granular_configuration import Configuration
from granular_configuration._build import build_configuration
from granular_configuration.exceptions import PlaceholderConfigurationError
from granular_configuration.yaml import Placeholder

ASSET_DIR = (Path(__file__).parent / "assets" / "test_build_configuration").resolve()


def test_build_with_a_placeholder() -> None:
    files = (
        ASSET_DIR / "placeholder_test1.yaml",
        ASSET_DIR / "placeholder_test2.yaml",
    )

    configuration = build_configuration(files, False)

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


def test_build_with_sub() -> None:
    files = (
        ASSET_DIR / "sub_test1.yaml",
        ASSET_DIR / "sub_test2.yaml",
    )

    configuration = build_configuration(files, False)

    assert isinstance(configuration, Configuration)
    assert configuration.flags.foo == "bar"
