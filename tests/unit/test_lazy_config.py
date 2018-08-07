import unittest
from mock import patch
import os
from functools import partial


from granular_configuration._config import (
    LazyLoadConfiguration, Configuration,
    ConfigurationLocations)

class TestLazyLoadConfiguration(unittest.TestCase):

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

