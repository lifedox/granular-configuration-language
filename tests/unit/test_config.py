import unittest
from mock import patch
import os
from functools import reduce, partial
from six import iteritems, itervalues

from granular_configuration.yaml_handler import loads, Placeholder
from granular_configuration._config import (
    _get_files_from_locations, LazyLoadConfiguration, _build_configuration, Configuration, _get_all_unique_locations,
    ConfigurationLocations, ConfigurationFiles, ConfigurationMultiNamedFiles)
from granular_configuration.exceptions import PlaceholderConfigurationError

class TestConfig(unittest.TestCase):

    def test__build_configuration(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        files = list(map(dir_func, ["a/b/t2.txt", "g/h.txt", "c/t.txt"]))


        configuration = _build_configuration(files)

        assert isinstance(configuration, Configuration)

        assert configuration.d == "from c/t.txt"
        assert configuration.c == "from c/t.txt"
        assert configuration.b == "from c/t.txt"
        assert configuration.h == "from g/h.txt"
        assert configuration.a == "from a/b/t2.txt"
        assert configuration.map == {"a": "from a/b/t2.txt",
                                     "h": "from g/h.txt",
                                     "c": "from c/t.txt"
                                    }
        assert configuration.deep_test.a.b == 10
        assert configuration.placeholder_test.overridden == 'This should be overridden'
        assert configuration.env_test.default == "This should be seen"

        with self.assertRaises(AttributeError) as cm:
            configuration.doesnotexist

        assert str(cm.exception) == 'Configuration value "doesnotexist" does not exist'

        with self.assertRaises(AttributeError) as cm:
            configuration.deep_test.a.doesnotexist

        assert str(cm.exception) == 'Configuration value "deep_test.a.doesnotexist" does not exist'

        with self.assertRaises(PlaceholderConfigurationError) as cm:
            configuration.placeholder_test.not_overridden

        assert str(cm.exception) == 'Configuration expects "placeholder_test.not_overridden" to be overwritten. Message: "This should not be overridden"'


    def test__build_configuration_placeholder_root(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        files = list(map(dir_func, ["placeholder_test1.yaml", "placeholder_test2.yaml"]))

        configuration = _build_configuration(files)

        assert isinstance(configuration, Configuration)

        assert configuration.a == {"key1": "value1", "key2": "value2"}

        raw_value = dict(configuration._raw_items())

        assert isinstance(raw_value["b"], Placeholder) and (raw_value["b"].message == "Placeholder over a placeholder")
        assert isinstance(raw_value["c"], Placeholder) and (raw_value["c"].message == "Placeholder over a value")


    def test__build_configuration_mixconfig(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        files = list(map(dir_func, ["mix_config.yaml", "mix_config.ini"]))

        configuration = _build_configuration(files)

        assert isinstance(configuration, Configuration)

        assert configuration.A.key1 == "value1"
        assert configuration.A.key2.deep_key == "Overwritten value"
        assert configuration.A.key3 == "new value"
        assert configuration.B == {None: 1}
        assert configuration.D == {None: 1}






if __name__ == '__main__':
    unittest.main()
