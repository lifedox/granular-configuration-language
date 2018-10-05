
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
from granular_configuration.exceptions import PlaceholderConfigurationError, ParseEnvError


class TestYamlHandler(unittest.TestCase):
    def test_yaml_env(self):
        with patch.dict(os.environ, values={"unreal_env_variable": "test me"}):
            self.assertEqual(loads("!Env '{{unreal_env_variable}}'").run(), "test me")
            self.assertEqual(loads("!Env '{{unreal_env_variable:special}}'").run(), "test me")
            self.assertEqual(loads("!Env '{{unreal_env_vari:special case }}'").run(), "special case ")

            with self.assertRaises(KeyError):
                loads("!Env '{{unreal_env_vari}}'").run()

            with self.assertRaises(ValueError):
                loads("!Env [a]").run()

    def test_yaml_func(self):
        self.assertIs(loads("!Func functools.reduce").run(), reduce)
        self.assertIs(loads("!Func granular_configuration._config.ConfigurationLocations").run(), ConfigurationLocations)

        with self.assertRaises(ValueError):
            loads("!Func unreal.garbage.func").run()

        with self.assertRaises(ValueError):
            loads("!Func sys.stdout").run()

        with self.assertRaises(ValueError):
            loads("!Func [a]").run()

    def test_yaml_class(self):
        self.assertIs(loads("!Class granular_configuration._config.ConfigurationLocations").run(), ConfigurationLocations)

        with self.assertRaises(ValueError):
            loads("!Class functools.reduce").run()

        with self.assertRaises(ValueError):
            loads("!Class unreal.garbage.func").run()

        with self.assertRaises(ValueError):
            loads("!Class [a]").run()

    def test_yaml_placeholder(self):
        placeholder = loads("!Placeholder value")

        self.assertIsInstance(placeholder, Placeholder)
        self.assertEqual(str(placeholder), "value")

        with self.assertRaises(ValueError):
            loads("!Placeholder []")

    def test_yaml_parse_env_scalar__string(self):
        with patch.dict(os.environ, values={"unreal_env_variable": "test me"}):
            self.assertEqual(loads("!ParseEnv unreal_env_variable").run(), "test me")

    def test_yaml_parse_env_scalar__float(self):
        with patch.dict(os.environ, values={"unreal_env_variable": "3.0"}):
            self.assertEqual(loads("!ParseEnv unreal_env_variable").run(), 3.0)
            self.assertIsInstance(loads("!ParseEnv unreal_env_variable").run(), float)

    def test_yaml_parse_env_scalar__int(self):
        with patch.dict(os.environ, values={"unreal_env_variable": "3"}):
            self.assertEqual(loads("!ParseEnv unreal_env_variable").run(), 3)
            self.assertIsInstance(loads("!ParseEnv unreal_env_variable").run(), int)

    def test_yaml_parse_env_scalar__float_string(self):
        with patch.dict(os.environ, values={"unreal_env_variable": "'3'"}):
            self.assertEqual(loads("!ParseEnv unreal_env_variable").run(), "3")

    def test_yaml_parse_env_scalar__null(self):
        with patch.dict(os.environ, values={"unreal_env_variable": "null"}):
            self.assertIs(loads("!ParseEnv unreal_env_variable").run(), None)

    def test_yaml_parse_env_scalar__bool(self):
        with patch.dict(os.environ, values={"unreal_env_variable": "true"}):
            self.assertEqual(loads("!ParseEnv unreal_env_variable").run(), True)
            self.assertIsInstance(loads("!ParseEnv unreal_env_variable").run(), bool)

    def test_yaml_parse_env_scalar__dict(self):
        with patch.dict(os.environ, values={"unreal_env_variable": '{"a": "value"}'}):
            self.assertDictEqual(loads("!ParseEnv unreal_env_variable").run(), {"a": "value"})

    def test_yaml_parse_env_scalar__Configuration(self):
        with patch.dict(os.environ, values={"unreal_env_variable": '{"a": {"b": "value"}}'}):
            value = loads("!ParseEnv unreal_env_variable", obj_pairs_hook=Configuration).run()
            self.assertIsInstance(value, Configuration)
            self.assertDictEqual(value, {"a": {"b": "value"}})
            self.assertIsInstance(value["a"], Configuration)

    def test_yaml_parse_env_scalar__seq(self):
        with patch.dict(os.environ, values={"unreal_env_variable": '[1, 2, 3]'}):
            self.assertSequenceEqual(loads("!ParseEnv unreal_env_variable").run(), [1, 2, 3])


    def test_yaml_parse_env_scalar__recursive(self):
        with patch.dict(os.environ, values={"unreal_env_variable": '!ParseEnv unreal_env_variable1', "unreal_env_variable1": "42"}):
            value = loads("!ParseEnv unreal_env_variable").run()
            self.assertEqual(loads("!ParseEnv unreal_env_variable").run(), 42)

    def test_yaml_parse_env_scalar__var_parse_error(self):
        with patch.dict(os.environ, values={"unreal_env_variable": '{'}):
            with self.assertRaises(ParseEnvError):
                loads("!ParseEnv unreal_env_variable").run()

    def test_yaml_parse_env_scalar__missing(self):
        with patch.dict(os.environ, values={}):
            with self.assertRaises(KeyError):
                loads("!ParseEnv unreal_env_vari").run()

    def test_yaml_parse_env_mapping__error(self):
        with patch.dict(os.environ, values={}):
            with self.assertRaises(ValueError):
                loads('!ParseEnv {"unreal_env_vari": 1}')

    def test_yaml_parse_env_sequence__use_default(self):
        with patch.dict(os.environ, values={}):
                self.assertEqual(loads('!ParseEnv ["unreal_env_vari", 1]').run(), 1)
                self.assertEqual(loads('!ParseEnv ["unreal_env_vari", 1.5]').run(), 1.5)
                self.assertEqual(loads('!ParseEnv ["unreal_env_vari", abc]').run(), "abc")
                self.assertIs(loads('!ParseEnv ["unreal_env_vari", null]').run(), None)
                self.assertEqual(loads('!ParseEnv ["unreal_env_vari", false]').run(), False)
                value = loads('!ParseEnv ["unreal_env_vari", {"a": {"b": "value"}}]', obj_pairs_hook=Configuration).run()
                self.assertIsInstance(value, Configuration)
                self.assertDictEqual(value, {"a": {"b": "value"}})
                self.assertIsInstance(value["a"], Configuration)

    def test_yaml_parse_env_sequence__string(self):
        with patch.dict(os.environ, values={"unreal_env_variable": "test me"}):
            self.assertEqual(loads("!ParseEnv [unreal_env_variable, null]").run(), "test me")

    def test_yaml_parse_env_sequence__float(self):
        with patch.dict(os.environ, values={"unreal_env_variable": "3.0"}):
            self.assertEqual(loads("!ParseEnv [unreal_env_variable, null]").run(), 3.0)
            self.assertIsInstance(loads("!ParseEnv [unreal_env_variable, null]").run(), float)

    def test_yaml_parse_env_sequence__int(self):
        with patch.dict(os.environ, values={"unreal_env_variable": "3"}):
            self.assertEqual(loads("!ParseEnv [unreal_env_variable, null]").run(), 3)
            self.assertIsInstance(loads("!ParseEnv [unreal_env_variable, null]").run(), int)

if __name__ == "__main__":
    unittest.main()
