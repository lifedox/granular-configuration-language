import unittest
from mock import patch, call
import os
from functools import reduce, partial

from granular_configuration.yaml_handler import loads
from granular_configuration._config import (
    _get_files_from_locations, LazyLoadConfiguration, _build_configuration, Configuration, ConfigurationLocations, _get_all_unique_locations)


class TestConfig(unittest.TestCase):
    def test_yaml_env(self):
        with patch.dict(os.environ, values={"unreal_env_variable": "test me"}):
            assert loads("!Env '{{unreal_env_variable}}'") == "test me"
            assert loads("!Env '{{unreal_env_variable:special}}'") == "test me"
            assert loads("!Env '{{unreal_env_vari:special case }}'") == "special case "

            with self.assertRaises(KeyError):
                loads("!Env '{{unreal_env_vari}}'")

            with self.assertRaises(ValueError):
                loads("!Env [a]")


    def test_yaml_func(self):
        assert loads("!Func functools.reduce") is reduce
        assert loads("!Func granular_configuration._config.ConfigurationLocations") is ConfigurationLocations

        with self.assertRaises(ValueError):
            loads("!Func unreal.garbage.func")

        with self.assertRaises(ValueError):
            loads("!Func sys.stdout")

        with self.assertRaises(ValueError):
            loads("!Func [a]")

    def test_yaml_class(self):
        assert loads("!Class granular_configuration._config.ConfigurationLocations") is ConfigurationLocations

        with self.assertRaises(ValueError):
            loads("!Class functools.reduce")

        with self.assertRaises(ValueError):
            loads("!Class unreal.garbage.func")


        with self.assertRaises(ValueError):
            loads("!Class [a]")


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

        with self.assertRaises(AttributeError):
            configuration.doesnotexist

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



if __name__ == '__main__':
    unittest.main()
