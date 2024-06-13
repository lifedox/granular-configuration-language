from __future__ import annotations

import os
import unittest
from functools import partial, reduce
from pathlib import Path

from granular_configuration._config import Configuration, _build_configuration
from granular_configuration.yaml_handler import loads
from granular_configuration.yaml_handler import Placeholder


class TestConfiguration(unittest.TestCase):
    def test_converting_Configuration_to_dict(self) -> None:
        config = loads("a: !Func functools.reduce", Configuration)
        assert isinstance(config, Configuration)
        assert tuple(config.items()) == (("a", reduce),)

        config = loads("a: !Func functools.reduce", Configuration)
        assert tuple(config.values()) == (reduce,)

        config = loads("a: !Func functools.reduce", Configuration)
        assert dict(config) == {"a": reduce}

        config = loads("a: !Func functools.reduce", Configuration)
        assert config.pop("a") == reduce

        config = loads("a: !Func functools.reduce", Configuration)
        assert config.popitem() == ("a", reduce)

    def test_Configuration_is_dict(self) -> None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/config_location_test"))
        dir_func = partial(os.path.join, base_dir)

        files = list(map(Path, map(dir_func, ["g/h.txt", "c/t.txt"])))

        value = _build_configuration(files)

        import copy

        new = copy.deepcopy(value)
        assert new == value
        assert value.exists("a") is False
        assert new.exists("a") is False

        new = copy.copy(value)
        assert new == value
        assert value.exists("a") is False
        assert new.exists("a") is False

        new = value.copy()
        assert new == value
        assert value.exists("a") is False
        assert new.exists("a") is False

        assert isinstance(value, dict)

    def test_Configuration_exists(self) -> None:
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

    def test_Configuration_as_dict(self) -> None:
        input = Configuration(a="b", b=Configuration(a=Configuration(a=1)))
        expected = dict(a="b", b=dict(a=dict(a=1)))
        assert input.as_dict() == expected

    def test_simple_patch(self) -> None:
        input = Configuration(a="b")
        with input.patch(dict(a="c")):
            self.assertDictEqual(input.as_dict(), dict(a="c"))
            self.assertSequenceEqual(tuple(input._raw_items()), tuple(dict(a="c").items()))

        self.assertDictEqual(input.as_dict(), dict(a="b"))

    def test_patch_new_not_allowed(self) -> None:
        input = Configuration(a="b")

        with self.assertRaises(KeyError):
            with input.patch(dict(b="c")):
                self.assertDictEqual(input.as_dict(), dict(a="b", b="c"))

    def test_patch_new(self) -> None:
        input = Configuration(a="b")
        with input.patch(dict(b="c"), allow_new_keys=True):
            self.assertDictEqual(input.as_dict(), dict(a="b", b="c"))
            self.assertSequenceEqual(tuple(input._raw_items()), tuple(dict(a="b", b="c").items()))
            self.assertIn("b", input)
            self.assertEqual(len(input), 2)

        self.assertNotIn("b", input)
        self.assertDictEqual(input.as_dict(), dict(a="b"))
        self.assertEqual(len(input), 1)

    def test_patch_new_dict(self) -> None:
        input = Configuration(a="b")
        with input.patch(dict(b="c", e=dict(a=1)), allow_new_keys=True):
            self.assertDictEqual(input.as_dict(), dict(a="b", b="c", e=dict(a=1)))
            self.assertSequenceEqual(tuple(input._raw_items()), tuple(dict(a="b", b="c", e=dict(a=1)).items()))
            self.assertIn("b", input)
            self.assertIn("e", input)
            self.assertIn("a", input.e)

        self.assertDictEqual(input.as_dict(), dict(a="b"))

    def test_patch_nest_dict_deeper(self) -> None:
        input = Configuration(a="b")
        with input.patch({"b": {"a": {"a": 2}}}, allow_new_keys=True):
            self.assertDictEqual(input.as_dict(), {"a": "b", "b": {"a": {"a": 2}}})
            self.assertSequenceEqual(tuple(input._raw_items()), tuple({"a": "b", "b": {"a": {"a": 2}}}.items()))

        self.assertDictEqual(input.as_dict(), dict(a="b"))

    def test_patch_nest_dict(self) -> None:
        input = Configuration(a="b", b=Configuration(a=Configuration(a=1)))
        with input.patch({"b": {"a": {"a": 2}}}):
            self.assertDictEqual(input.as_dict(), {"a": "b", "b": {"a": {"a": 2}}})
            self.assertSequenceEqual(tuple(input._raw_items()), tuple({"a": "b", "b": {"a": {"a": 2}}}.items()))

            self.assertDictEqual(input.b.as_dict(), {"a": {"a": 2}})

        self.assertDictEqual(input.as_dict(), {"a": "b", "b": {"a": {"a": 1}}})
        self.assertDictEqual(input.b.as_dict(), {"a": {"a": 1}})

    def test_patch_deep_nest_dict(self) -> None:
        input = Configuration(a="b", b=Configuration(a=Configuration(a=1)))
        with input.b.patch({"a": {"a": 2}}):
            self.assertDictEqual(input.as_dict(), {"a": "b", "b": {"a": {"a": 2}}})
            self.assertSequenceEqual(tuple(input._raw_items()), tuple({"a": "b", "b": {"a": {"a": 2}}}.items()))

        self.assertDictEqual(input.as_dict(), {"a": "b", "b": {"a": {"a": 1}}})

    def test_nested_patch(self) -> None:
        input = Configuration(a="b")
        with input.patch({"a": "c", "b": "b", "c": "c"}, allow_new_keys=True):
            self.assertDictEqual(input.as_dict(), {"a": "c", "b": "b", "c": "c"})

            with input.patch({"c": "c1", "d": "c1"}, allow_new_keys=True):
                self.assertDictEqual(input.as_dict(), {"a": "c", "b": "b", "c": "c1", "d": "c1"})

        self.assertDictEqual(input.as_dict(), {"a": "b"})

    def test_patch_copy(self) -> None:
        input = Configuration(a="b")
        with input.patch({"a": "c", "b": "b", "c": "c"}, allow_new_keys=True):
            self.assertDictEqual(input.as_dict(), {"a": "c", "b": "b", "c": "c"})

            with input.patch({"c": "c1", "d": "c1"}, allow_new_keys=True):
                self.assertDictEqual(input.as_dict(), {"a": "c", "b": "b", "c": "c1", "d": "c1"})

                import copy

                input_copy = copy.copy(input)
                input_deepcopy = copy.deepcopy(input)

                self.assertDictEqual(input_copy.as_dict(), {"a": "b"})
                self.assertDictEqual(input_deepcopy.as_dict(), {"a": "b"})

        self.assertDictEqual(input.as_dict(), {"a": "b"})

    def test_patch_nested_sibling(self) -> None:
        CONFIG = Configuration(
            key1="value1", key2="value2", nested=Configuration(nest_key1="nested_value1", nest_key2="nested_value2")
        )
        patch = dict(key1="new_value", nested=dict(nest_key2="new_value"))
        expected = dict(key1="new_value", key2="value2", nested=dict(nest_key1="nested_value1", nest_key2="new_value"))

        with CONFIG.patch(patch):
            self.assertDictEqual(CONFIG.as_dict(), expected)

    def test_nested_patch_full_override(self) -> None:
        CONFIG = Configuration(
            key1="value1", key2="value2", nested=Configuration(nest_key1="nested_value1", nest_key2="nested_value2")
        )
        patch1 = dict(key1="new value", nested=dict(nest_key2="new value"))
        patch2 = dict(key2="new value2", nested=dict(nest_key1="new value2"))
        expected = {
            "key1": "new value",
            "key2": "new value2",
            "nested": {"nest_key1": "new value2", "nest_key2": "new value"},
        }

        with CONFIG.patch(patch1):
            with CONFIG.patch(patch2):
                self.assertDictEqual(CONFIG.as_dict(), expected)

        with CONFIG.patch(patch2):
            with CONFIG.patch(patch1):
                self.assertDictEqual(CONFIG.as_dict(), expected)


if __name__ == "__main__":
    unittest.main()
