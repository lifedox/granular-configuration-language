import unittest
from mock import patch


from granular_configuration._config import LazyLoadConfiguration
from granular_configuration.exceptions import GetConfigReadBeforeSetException

from granular_configuration import _set_config


class TestSetConfig(unittest.TestCase):
    def test_set_config(self):
        with patch("granular_configuration._set_config.LazyLoadConfiguration") as LazyLoadConfiguration, patch(
            "granular_configuration._set_config._SET_CONFIG_META", new=None
        ) as _SET_CONFIG_META:
            _set_config.set_config("a", "b")
            self.assertTupleEqual(_set_config._SET_CONFIG_META, ("a", "b"))
            LazyLoadConfiguration.assert_not_called()

        self.assertIsNone(_set_config._SET_CONFIG_META)

    def test_set_config_twice(self):
        with patch("granular_configuration._set_config.LazyLoadConfiguration") as LazyLoadConfiguration, patch(
            "granular_configuration._set_config._SET_CONFIG_META", new=None
        ) as _SET_CONFIG_META:
            _set_config.set_config("a", "b")
            _set_config.set_config("c", "d")
            self.assertTupleEqual(_set_config._SET_CONFIG_META, ("c", "d"))
            LazyLoadConfiguration.assert_not_called()

        self.assertIsNone(_set_config._SET_CONFIG_META)

    def test_get_config(self):
        with patch("granular_configuration._set_config.LazyLoadConfiguration") as LazyLoadConfiguration, patch(
            "granular_configuration._set_config._SET_CONFIG_META", new=None
        ) as _SET_CONFIG_META:
            _set_config.set_config("a", "b")

            _set_config.get_config("c", "d", base_path="base_path")

            self.assertTupleEqual(_set_config._SET_CONFIG_META, ("a", "b"))
            LazyLoadConfiguration.assert_called_once_with("c", "d", "a", "b", base_path="base_path")

        self.assertIsNone(_set_config._SET_CONFIG_META)

    def test_get_config_no_set_requires(self):
        with self.assertRaises(GetConfigReadBeforeSetException):

            with patch("granular_configuration._set_config.LazyLoadConfiguration") as LazyLoadConfiguration, patch(
                "granular_configuration._set_config._SET_CONFIG_META", new=None
            ) as _SET_CONFIG_META:

                _set_config.get_config("c", "d", base_path="base_path")

            self.assertIsNone(_set_config._SET_CONFIG_META)

    def test_get_config_no_set_no_requires(self):
        with patch("granular_configuration._set_config.LazyLoadConfiguration") as LazyLoadConfiguration, patch(
            "granular_configuration._set_config._SET_CONFIG_META", new=None
        ) as _SET_CONFIG_META:

            _set_config.get_config("c", "d", base_path="base_path", requires_set=False)

            self.assertIsNone(_set_config._SET_CONFIG_META)
            LazyLoadConfiguration.assert_called_once_with("c", "d", base_path="base_path")

        self.assertIsNone(_set_config._SET_CONFIG_META)

    def test_clear_config(self):
        _set_config.set_config("a", "b")
        _set_config.get_config()
        _set_config.clear_config()

        with self.assertRaises(GetConfigReadBeforeSetException):
            _set_config.get_config()


if __name__ == "__main__":
    unittest.main()
