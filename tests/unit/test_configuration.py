import unittest
import os
from functools import reduce, partial
from six import iteritems, itervalues

from granular_configuration.yaml_handler import loads, Placeholder
from granular_configuration._config import (
    _build_configuration, Configuration)

class TestConfiguration(unittest.TestCase):

    def test_converting_Configuration_to_dict(self):
        config = loads("a: !Func functools.reduce", Configuration)
        assert isinstance(config, Configuration)
        assert tuple(iteritems(config)) == (("a", reduce),)

        config = loads("a: !Func functools.reduce", Configuration)
        assert tuple(itervalues(config)) == (reduce, )

        config = loads("a: !Func functools.reduce", Configuration)
        assert dict(config) == {"a": reduce}

        config = loads("a: !Func functools.reduce", Configuration)
        assert config.pop("a") == reduce

        config = loads("a: !Func functools.reduce", Configuration)
        assert config.popitem() == ("a", reduce, )


    def test_Configuration_is_dict(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        files = list(map(dir_func, ["g/h.txt", "c/t.txt"]))

        value = _build_configuration(files)
        assert isinstance(value, dict)

        from copy import deepcopy

        new = deepcopy(value)

        assert new == value

        assert value.exists("a") is False
        assert new.exists("a") is False


    def test_Configuration_exists(self):
        config = Configuration(a=1, b=Placeholder("tests"))

        assert config.exists("a") is True
        assert config.exists("b") is False
        assert config.exists("c") is False

        assert ("a" in config) is True
        assert ("b" in config) is True
        assert ("c" in config) is False

        assert config.get("a") == 1
        assert config.get("b") is None
        assert config.get("c") is None


    def test_Configuration_as_dict(self):
        input = Configuration(a="b", b=Configuration(a=Configuration(a=1)))
        expected = dict(a="b", b=dict(a=dict(a=1)))
        assert input.as_dict() == expected




if __name__ == '__main__':
    unittest.main()
