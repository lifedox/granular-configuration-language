
import unittest
from mock import patch
import os
from functools import reduce, partial
from six import iteritems, itervalues

from granular_configuration.yaml_handler import loads, Placeholder
from granular_configuration._config import (
    _get_files_from_locations,
    LazyLoadConfiguration,
    _build_configuration,
    Configuration,
    _get_all_unique_locations,
    ConfigurationLocations,
    ConfigurationFiles,
    ConfigurationMultiNamedFiles,
)
from granular_configuration.exceptions import PlaceholderConfigurationError


class TestYamlHandler(unittest.TestCase):
    def test_yaml_env(self):
        with patch.dict(os.environ, values={"unreal_env_variable": "test me"}):
            assert loads("!Env '{{unreal_env_variable}}'").run() == "test me"
            assert loads("!Env '{{unreal_env_variable:special}}'").run() == "test me"
            assert loads("!Env '{{unreal_env_vari:special case }}'").run() == "special case "

            with self.assertRaises(KeyError):
                loads("!Env '{{unreal_env_vari}}'").run()

            with self.assertRaises(ValueError):
                loads("!Env [a]").run()

    def test_yaml_func(self):
        assert loads("!Func functools.reduce").run() is reduce
        assert loads("!Func granular_configuration._config.ConfigurationLocations").run() is ConfigurationLocations

        with self.assertRaises(ValueError):
            loads("!Func unreal.garbage.func").run()

        with self.assertRaises(ValueError):
            loads("!Func sys.stdout").run()

        with self.assertRaises(ValueError):
            loads("!Func [a]").run()

    def test_yaml_class(self):
        assert loads("!Class granular_configuration._config.ConfigurationLocations").run() is ConfigurationLocations

        with self.assertRaises(ValueError):
            loads("!Class functools.reduce").run()

        with self.assertRaises(ValueError):
            loads("!Class unreal.garbage.func").run()

        with self.assertRaises(ValueError):
            loads("!Class [a]").run()

    def test_yaml_placeholder(self):
        placeholder = loads("!Placeholder value")

        assert isinstance(placeholder, Placeholder)
        assert str(placeholder) == "value"

        with self.assertRaises(ValueError):
            loads("!Placeholder []")


if __name__ == "__main__":
    unittest.main()
