import unittest
from mock import patch, call
import os
from functools import reduce, partial
from six import iteritems, itervalues

from granular_configuration.yaml_handler import loads, Placeholder, LazyEval
from granular_configuration._config import (
    _get_files_from_locations, LazyLoadConfiguration, _build_configuration, Configuration, _get_all_unique_locations,
    ConfigurationLocations, ConfigurationFiles, ConfigurationMultiNamedFiles)
from granular_configuration.exceptions import PlaceholderConfigurationError

class TestConfig(unittest.TestCase):
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





    def test__get_files_from_locations(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        directories = list(map(dir_func, ["a/b", "a", "b", "c", "d", "c"]))
        filenames = ["t.txt", "t2.txt"]
        files = list(map(dir_func, ["g/b.txt", "g/h.txt"]))

        exists = list(map(dir_func, ["a/b/t2.txt", "g/h.txt", "c/t.txt", "c/t2.txt"]))
        assert all(map(os.path.isfile, exists)), "Someone removed test assets"

        locations = _get_files_from_locations(filenames, directories, files)

        assert sorted(locations) == sorted(exists[:3])


    def test__get_files_from_locations_no_filename(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        directories = list(map(dir_func, ["a/b", "a", "b", "c", "d", "c"]))
        filenames = []
        files = list(map(dir_func, ["g/b.txt", "g/h.txt"]))

        exists = list(map(dir_func, ["g/h.txt"]))
        assert all(map(os.path.isfile, exists)), "Someone removed test assets"

        locations = _get_files_from_locations(filenames, directories, files)

        assert sorted(locations) == sorted(exists)


    def test__get_files_from_locations_no_dirs(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        directories = []
        filenames = ["t.txt", "t2.txt"]
        files = list(map(dir_func, ["g/b.txt", "g/h.txt"]))

        exists = list(map(dir_func, ["g/h.txt"]))
        assert all(map(os.path.isfile, exists)), "Someone removed test assets"

        locations = _get_files_from_locations(filenames, directories, files)

        assert sorted(locations) == sorted(exists)

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




    def test__ConfigurationLocations(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        directories = list(map(dir_func, ["a/b", "a", "b", "c", "d", "c"]))
        filenames = ["t.txt", "t2.txt"]
        files = list(map(dir_func, ["g/b.txt", "g/h.txt"]))

        exists = list(map(dir_func, ["g/h.txt", "a/b/t2.txt", "c/t.txt", "c/t2.txt"]))
        assert all(map(os.path.isfile, exists)), "Someone removed test assets"

        with patch("granular_configuration._config._get_files_from_locations", side_effect=_get_files_from_locations) as loc_mock:
            from_files = ConfigurationLocations(files=files)
            from_priority = ConfigurationLocations(filenames=filenames, directories=directories)

            loc_mock.assert_not_called()

            assert list(from_files.get_locations()) == exists[0:1]
            loc_mock.assert_called_with(filenames=None, directories=None, files=files)

            assert list(from_priority.get_locations()) == exists[1:3]
            loc_mock.assert_called_with(filenames=filenames, directories=directories, files=None)

            assert loc_mock.call_count == 2


    def test__ConfigurationFiles(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        files = list(map(dir_func, ["placeholder_test1.yaml", "placeholder_test2.yaml"]))

        assert list(ConfigurationFiles(files).get_locations()) == files


    def test__ConfigurationMultiNamedFiles(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        directories = list(map(dir_func, ["a/b", "a", "b", "c", "d", "c"]))
        filenames = ["t2.txt"]

        exists = list(map(dir_func, ["a/b/t2.txt", "c/t2.txt"]))
        assert all(map(os.path.isfile, exists)), "Someone removed test assets"

        assert list(ConfigurationMultiNamedFiles(filenames=filenames, directories=directories).get_locations()) == exists


    def test__get_all_unique_locations(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        directories = list(map(dir_func, ["a/b", "a", "b", "c", "d", "c"]))
        filenames = ["t.txt", "t2.txt"]
        files = list(map(dir_func, ["g/b.txt", "g/h.txt"]))

        exists = list(map(dir_func, ["g/h.txt", "a/b/t2.txt", "c/t.txt", "c/t2.txt"]))
        assert all(map(os.path.isfile, exists)), "Someone removed test assets"

        from_files = ConfigurationLocations(files=files)
        from_priority = ConfigurationLocations(filenames=filenames, directories=directories)

        assert list(_get_all_unique_locations([from_files, from_priority, from_files])) == exists[:3]
        assert list(_get_all_unique_locations([from_files, from_priority, from_files, from_priority, from_files])) == exists[:3]


    def test__LazyLoadConfiguration(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        directories = list(map(dir_func, ["a/b", "a", "b", "c", "d", "c"]))
        filenames = ["t.txt", "t2.txt"]
        files = list(map(dir_func, ["g/b.txt", "g/h.txt"]))

        location = (ConfigurationLocations(files=files),
                    ConfigurationLocations(filenames=filenames, directories=directories))

        config_dict = Configuration({"abc": "test", "name": "me" })

        with patch("granular_configuration._config._build_configuration", return_value=config_dict) as bc_mock, \
             patch("granular_configuration._config._get_all_unique_locations", return_value=files) as loc_mock:
            config = LazyLoadConfiguration(*location)

            bc_mock.assert_not_called()
            loc_mock.assert_not_called()

            assert config.abc == "test"

            bc_mock.assert_called_once_with(files)
            loc_mock.assert_called_once_with(location)

            assert config.name == "me"

            bc_mock.assert_called_once_with(files)
            loc_mock.assert_called_once_with(location)


    def test__LazyLoadConfiguration_with_base_path(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        directories = list(map(dir_func, ["a/b", "a", "b", "c", "d", "c"]))
        filenames = ["t.txt", "t2.txt"]
        files = list(map(dir_func, ["g/b.txt", "g/h.txt"]))

        location = (ConfigurationLocations(files=files),
                    ConfigurationLocations(filenames=filenames, directories=directories))

        config_dict = Configuration(start=Configuration(id=Configuration({"abc": "test", "name": "me" })))

        with patch("granular_configuration._config._build_configuration", return_value=config_dict) as bc_mock, \
             patch("granular_configuration._config._get_all_unique_locations", return_value=files) as loc_mock:
            config = LazyLoadConfiguration(*location, base_path=["start", "id"])

            bc_mock.assert_not_called()
            loc_mock.assert_not_called()

            assert config.abc == "test"

            bc_mock.assert_called_once_with(files)
            loc_mock.assert_called_once_with(location)

            assert config.name == "me"

            bc_mock.assert_called_once_with(files)
            loc_mock.assert_called_once_with(location)

    def test__LazyLoadConfiguration_get(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        directories = list(map(dir_func, ["a/b", "a", "b", "c", "d", "c"]))
        filenames = ["t.txt", "t2.txt"]
        files = list(map(dir_func, ["g/b.txt", "g/h.txt"]))

        location = (ConfigurationLocations(files=files),
                    ConfigurationLocations(filenames=filenames, directories=directories))

        config_dict = Configuration({"abc": "test", "name": "me" })

        with patch("granular_configuration._config._build_configuration", return_value=config_dict) as bc_mock, \
             patch("granular_configuration._config._get_all_unique_locations", return_value=files) as loc_mock:
            config = LazyLoadConfiguration(*location)

            assert config.get("abc") == "test"
            assert config.get("name") == "me"




if __name__ == '__main__':
    unittest.main()
