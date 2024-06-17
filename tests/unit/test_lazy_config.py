import os
import unittest
from functools import partial
from unittest.mock import patch

from granular_configuration._config import Configuration, ConfigurationLocations, LazyLoadConfiguration
from granular_configuration.exceptions import InvalidBasePathException


class TestLazyLoadConfiguration(unittest.TestCase):
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))

    def test__LazyLoadConfiguration(self) -> None:
        dir_func = partial(os.path.join, self.BASE_DIR)

        directories = list(map(dir_func, ["a/b", "a", "b", "c", "d", "c"]))
        filenames = ["t.yaml", "t2.yaml"]
        files = list(map(dir_func, ["g/b.yaml", "g/h.yaml"]))

        location = (
            ConfigurationLocations(files=files),
            ConfigurationLocations(filenames=filenames, directories=directories),
        )

        config_dict = Configuration({"abc": "test", "name": "me"})

        with (
            patch("granular_configuration._config._build_configuration", return_value=config_dict) as bc_mock,
            patch("granular_configuration._config.get_all_unique_locations", return_value=files) as loc_mock,
        ):
            config = LazyLoadConfiguration(*location)

            bc_mock.assert_not_called()
            loc_mock.assert_not_called()

            assert config.abc == "test"

            bc_mock.assert_called_once_with(files)
            loc_mock.assert_called_once_with(location)

            assert config.name == "me"

            bc_mock.assert_called_once_with(files)
            loc_mock.assert_called_once_with(location)

    def test__LazyLoadConfiguration_with_base_path(self) -> None:
        dir_func = partial(os.path.join, self.BASE_DIR)

        directories = list(map(dir_func, ["a/b", "a", "b", "c", "d", "c"]))
        filenames = ["t.yaml", "t2.yaml"]
        files = list(map(dir_func, ["g/b.yaml", "g/h.yaml"]))

        location = (
            ConfigurationLocations(files=files),
            ConfigurationLocations(filenames=filenames, directories=directories),
        )

        config_dict = Configuration(start=Configuration(id=Configuration({"abc": "test", "name": "me"})))

        with (
            patch("granular_configuration._config._build_configuration", return_value=config_dict) as bc_mock,
            patch("granular_configuration._config.get_all_unique_locations", return_value=files) as loc_mock,
        ):
            config = LazyLoadConfiguration(*location, base_path=["start", "id"])

            bc_mock.assert_not_called()
            loc_mock.assert_not_called()

            assert config.abc == "test"

            bc_mock.assert_called_once_with(files)
            loc_mock.assert_called_once_with(location)

            assert config.name == "me"

            bc_mock.assert_called_once_with(files)
            loc_mock.assert_called_once_with(location)

    def test__LazyLoadConfiguration_get(self) -> None:
        dir_func = partial(os.path.join, self.BASE_DIR)

        directories = list(map(dir_func, ["a/b", "a", "b", "c", "d", "c"]))
        filenames = ["t.yaml", "t2.yaml"]
        files = list(map(dir_func, ["g/b.yaml", "g/h.yaml"]))

        location = (
            ConfigurationLocations(files=files),
            ConfigurationLocations(filenames=filenames, directories=directories),
        )

        config_dict = Configuration({"abc": "test", "name": "me"})

        with (
            patch("granular_configuration._config._build_configuration", return_value=config_dict) as bc_mock,
            patch("granular_configuration._config.get_all_unique_locations", return_value=files) as loc_mock,
        ):
            config = LazyLoadConfiguration(*location)

            assert config.get("abc") == "test"
            assert config.get("name") == "me"

    def test__LazyLoadConfiguration_bad_base_path(self) -> None:

        config_dict = Configuration({"abc": "test", "name": "me"})

        with patch("granular_configuration._config._build_configuration", return_value=config_dict) as bc_mock:
            config = LazyLoadConfiguration(base_path="base")

            with self.assertRaises(InvalidBasePathException):
                config.load_configure()

    def test__LazyLoadConfiguration_string_base_path(self) -> None:
        config_dict = Configuration({"abc": "test", "name": "me"})

        with patch("granular_configuration._config._build_configuration", return_value=config_dict) as bc_mock:
            config = LazyLoadConfiguration(base_path="base")

            self.assertEqual(config._LazyLoadConfiguration__base_path, ["base"])
            bc_mock.assert_not_called()

    def test__LazyLoadConfiguration_list_base_path(self) -> None:
        config_dict = Configuration({"abc": "test", "name": "me"})

        with patch("granular_configuration._config._build_configuration", return_value=config_dict) as bc_mock:
            config = LazyLoadConfiguration(base_path=["base", "path"])

            self.assertEqual(config._LazyLoadConfiguration__base_path, ["base", "path"])
            bc_mock.assert_not_called()

    def test__LazyLoadConfiguration_no_base_path(self) -> None:
        config_dict = Configuration({"abc": "test", "name": "me"})

        with patch("granular_configuration._config._build_configuration", return_value=config_dict) as bc_mock:
            config = LazyLoadConfiguration()

            self.assertEqual(config._LazyLoadConfiguration__base_path, [])
            bc_mock.assert_not_called()

    def test__LazyLoadConfiguration_env(self) -> None:
        env_path = os.path.join(
            self.BASE_DIR,
            "test_env_config.yaml",
        )

        with patch("granular_configuration._config.os.environ", new={"G_CONFIG_LOCATION": env_path}) as env_mock:
            config = LazyLoadConfiguration(
                os.path.join(
                    self.BASE_DIR,
                    "mix_config.yaml",
                ),
                use_env_location=True,
            )
            assert config.A.key1 == "value2"

    def test__LazyLoadConfiguration_env_list(self) -> None:
        env_path = (
            os.path.join(
                self.BASE_DIR,
                "test_env_config.yaml",
            )
            + ","
            + os.path.join(
                self.BASE_DIR,
                "mix_config.yaml",
            )
        )

        with patch("granular_configuration._config.os.environ", new={"G_CONFIG_LOCATION": env_path}) as env_mock:
            config = LazyLoadConfiguration(use_env_location=True)
            assert config.A.key1 == "value1"
            assert config.A.key2 == "MyTestValue"

    def test__LazyLoadConfiguration_env_none(self) -> None:
        with patch("granular_configuration._config.os.environ", new={}):
            config = LazyLoadConfiguration(use_env_location=True)
            assert config.as_dict() == {}

    def test__LazyLoadConfiguration_like_a_mutablemapping(self) -> None:

        dir_func = partial(os.path.join, self.BASE_DIR)

        config = LazyLoadConfiguration(dir_func("test_env_config.yaml"))

        self.assertEqual(config["A"]["key1"], "value2")
        config["B"] = 1
        self.assertEqual(config["B"], 1)
        self.assertEqual(len(config), 2)
        del config["B"]
        self.assertSequenceEqual(list(config), ["A"])


if __name__ == "__main__":
    unittest.main()
