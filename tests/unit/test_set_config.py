import unittest
from unittest.mock import patch

from granular_configuration import _set_config, testing
from granular_configuration.exceptions import GetConfigReadBeforeSetException


class TestSetConfig(unittest.TestCase):
    def test_set_config(self) -> None:
        with patch("granular_configuration._set_config.LazyLoadConfiguration") as LazyLoadConfiguration, patch(
            "granular_configuration._set_config._SET_CONFIG_META", new=None
        ):
            _set_config.set_config("a", "b")
            assert _set_config._SET_CONFIG_META is not None
            self.assertTupleEqual(_set_config._SET_CONFIG_META, ("a", "b"))
            LazyLoadConfiguration.assert_not_called()

        self.assertIsNone(_set_config._SET_CONFIG_META)

    def test_set_config_twice(self) -> None:
        with patch("granular_configuration._set_config.LazyLoadConfiguration") as LazyLoadConfiguration, patch(
            "granular_configuration._set_config._SET_CONFIG_META", new=None
        ):
            _set_config.set_config("a", "b")
            _set_config.set_config("c", "d")
            assert _set_config._SET_CONFIG_META is not None
            self.assertTupleEqual(_set_config._SET_CONFIG_META, ("c", "d"))
            LazyLoadConfiguration.assert_not_called()

        self.assertIsNone(_set_config._SET_CONFIG_META)

    def test_set_config_twice_empty(self) -> None:
        with patch("granular_configuration._set_config.LazyLoadConfiguration") as LazyLoadConfiguration, patch(
            "granular_configuration._set_config._SET_CONFIG_META", new=None
        ):
            _set_config.set_config("a", "b")
            _set_config.set_config()
            assert _set_config._SET_CONFIG_META is not None
            self.assertTupleEqual(_set_config._SET_CONFIG_META, tuple())
            LazyLoadConfiguration.assert_not_called()

        self.assertIsNone(_set_config._SET_CONFIG_META)

    def test_get_config(self) -> None:
        with patch("granular_configuration._set_config.LazyLoadConfiguration") as LazyLoadConfiguration, patch(
            "granular_configuration._set_config._SET_CONFIG_META", new=None
        ):
            _set_config.set_config("a", "b")

            _set_config.get_config("c", "d", base_path="base_path")

            assert _set_config._SET_CONFIG_META is not None
            self.assertTupleEqual(_set_config._SET_CONFIG_META, ("a", "b"))
            LazyLoadConfiguration.assert_called_once_with(
                "c", "d", "a", "b", base_path="base_path", use_env_location=False
            )

        self.assertIsNone(_set_config._SET_CONFIG_META)

    def test_get_config_set_config_empty(self) -> None:
        with patch("granular_configuration._set_config.LazyLoadConfiguration") as LazyLoadConfiguration, patch(
            "granular_configuration._set_config._SET_CONFIG_META", new=None
        ):
            _set_config.set_config("a", "b")
            _set_config.set_config()

            _set_config.get_config("c", "d", base_path="base_path")

            assert _set_config._SET_CONFIG_META is not None
            self.assertTupleEqual(_set_config._SET_CONFIG_META, tuple())
            LazyLoadConfiguration.assert_called_once_with("c", "d", base_path="base_path", use_env_location=False)

        self.assertIsNone(_set_config._SET_CONFIG_META)

    def test_get_config_no_set_requires(self) -> None:
        with self.assertRaises(GetConfigReadBeforeSetException):

            with patch("granular_configuration._set_config.LazyLoadConfiguration"), patch(
                "granular_configuration._set_config._SET_CONFIG_META", new=None
            ):

                _set_config.get_config("c", "d", base_path="base_path")

            self.assertIsNone(_set_config._SET_CONFIG_META)

    def test_get_config_no_set_no_requires(self) -> None:
        with patch("granular_configuration._set_config.LazyLoadConfiguration") as LazyLoadConfiguration, patch(
            "granular_configuration._set_config._SET_CONFIG_META", new=None
        ):

            _set_config.get_config("c", "d", base_path="base_path", requires_set=False)

            self.assertIsNone(_set_config._SET_CONFIG_META)
            LazyLoadConfiguration.assert_called_once_with("c", "d", base_path="base_path", use_env_location=False)

        self.assertIsNone(_set_config._SET_CONFIG_META)

    def test_clear_config(self) -> None:
        _set_config.set_config("a", "b")
        _set_config.get_config()
        testing.clear_config()

        with self.assertRaises(GetConfigReadBeforeSetException):
            _set_config.get_config()


if __name__ == "__main__":
    unittest.main()
