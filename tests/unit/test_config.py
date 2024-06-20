import os
from functools import partial
from pathlib import Path

import pytest

from granular_configuration import Configuration
from granular_configuration._build import build_configuration
from granular_configuration.exceptions import PlaceholderConfigurationError
from granular_configuration.yaml_handler import Placeholder


def test_build_baseline() -> None:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
    dir_func = partial(os.path.join, base_dir)

    files = list(map(Path, map(dir_func, ["a/b/t2.yaml", "g/h.yaml", "c/t.yaml"])))

    configuration = build_configuration(files)

    assert isinstance(configuration, Configuration)

    assert configuration.d == "from c/t.yaml"
    assert configuration.c == "from c/t.yaml"
    assert configuration.b == "from c/t.yaml"
    assert configuration.h == "from g/h.yaml"
    assert configuration.a == "from a/b/t2.yaml"
    assert configuration.map == {"a": "from a/b/t2.yaml", "h": "from g/h.yaml", "c": "from c/t.yaml"}
    assert configuration.deep_test.a.b == 10
    assert configuration.placeholder_test.overridden == "This should be overridden"
    assert configuration.env_test.default == "This should be seen"

    with pytest.raises(AttributeError, match='Configuration value "doesnotexist" does not exist'):
        configuration.doesnotexist

    with pytest.raises(AttributeError, match='Configuration value "deep_test.a.doesnotexist" does not exist'):
        configuration.deep_test.a.doesnotexist

    with pytest.raises(
        PlaceholderConfigurationError,
        match='Configuration expects "placeholder_test.not_overridden" to be overwritten. Message: "This should not be overridden"',
    ):
        configuration.placeholder_test.not_overridden


def test_build_with_a_placeholder_root() -> None:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
    dir_func = partial(os.path.join, base_dir)

    files = list(map(Path, map(dir_func, ["placeholder_test1.yaml", "placeholder_test2.yaml"])))

    configuration = build_configuration(files)

    assert isinstance(configuration, Configuration)

    assert configuration.a == {"key1": "value1", "key2": "value2"}

    raw_value = dict(configuration._raw_items())

    assert isinstance(raw_value["b"], Placeholder) and (raw_value["b"].message == "Placeholder over a placeholder")
    assert isinstance(raw_value["c"], Placeholder) and (raw_value["c"].message == "Placeholder over a value")


def test_build_with_sub() -> None:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
    dir_func = partial(os.path.join, base_dir)

    files = list(map(Path, map(dir_func, ["sub_test1.yaml", "sub_test2.yaml"])))

    configuration = build_configuration(files)

    assert isinstance(configuration, Configuration)
    assert configuration.flags.foo == "bar"
