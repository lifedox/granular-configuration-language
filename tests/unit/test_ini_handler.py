import unittest
from collections import OrderedDict
from functools import reduce

from ruamel.yaml.parser import ParserError

from granular_configuration._config import Configuration
from granular_configuration.exceptions import IniKeyExistAsANonMapping, IniTryToReplaceExistingKey
from granular_configuration.ini_handler import loads
from granular_configuration.yaml_handler import loads as yaml_loads


class TestIniHandler(unittest.TestCase):
    def test_default(self) -> None:
        test = """\
[ROOT]
a=b
b=c
"""
        assert loads(test, Configuration).as_dict() == {"a": "b", "b": "c"}

    def test_default_dict(self) -> None:
        test = """\
[ROOT]
a=b
b=c
"""
        expected = OrderedDict()
        expected["a"] = "b"
        expected["b"] = "c"

        assert loads(test) == expected

    def test_value_types(self) -> None:
        test = """\
[ROOT]
a=1
b=true
c=null
d=1.123
e='1'
"""
        assert loads(test, Configuration).as_dict() == {"a": 1, "b": True, "c": None, "d": 1.123, "e": "1"}

    def test_key_types(self) -> None:
        test = """\
[ROOT]
'2'= "str"
2= integer
1.123= float
"1.123"= 'str'
null= test
True= "boolean"
false= "not"
"""
        assert loads(test, Configuration).as_dict() == {
            "2": "str",
            2: "integer",
            1.123: "float",
            "1.123": "str",
            None: "test",
            True: "boolean",
            False: "not",
        }

    def test_yaml_key_types(self) -> None:
        test = """\
'2': "str"
2: integer
1.123: float
"1.123": 'str'
null: test
True: "boolean"
false: "not"
"""
        assert yaml_loads(test, Configuration).as_dict() == {
            "2": "str",
            2: "integer",
            1.123: "float",
            "1.123": "str",
            None: "test",
            True: "boolean",
            False: "not",
        }

    def test_empty_dicts(self) -> None:
        test = """\
[A]

[F.G]

"""
        assert loads(test, Configuration).as_dict() == {"A": {}, "F": {"G": {}}}

    def test_nested_types(self) -> None:
        test = """\
[A]
a=b

[A.B]
a=b

[F.G]

[A.B.C]
a=b

[A.D.E]

"""
        assert loads(test, Configuration).as_dict() == {
            "A": {"a": "b", "B": {"a": "b", "C": {"a": "b"}}, "D": {"E": {}}},
            "F": {"G": {}},
        }

    def test_tags(self) -> None:
        test = """\
[A]
a=!Env 'no sub'
b=!Func functools.reduce
"""
        assert loads(test, Configuration).as_dict() == {"A": {"a": "no sub", "b": reduce}}

    def test_bad_replace(self) -> None:

        with self.assertRaises(IniTryToReplaceExistingKey):
            test = """\
[A]
a='str'

[A.a]

"""
            print(loads(test, Configuration).as_dict())

    def test_bad_replace_in_chain(self) -> None:

        with self.assertRaises(IniKeyExistAsANonMapping):
            test = """\
[A]
a='str'

[A.a.c]

"""
            print(loads(test, Configuration).as_dict())

    def test_bad_replace_at_root(self) -> None:

        with self.assertRaises(IniKeyExistAsANonMapping):
            test = """\
[ROOT]
A='str'

[A.a.c]
B='str'

"""
            print(loads(test, Configuration).as_dict())

    def test_out_of_order(self) -> None:

        with self.assertRaises(IniTryToReplaceExistingKey):
            test = """\
[A.a]

[A]


"""
            print(loads(test, Configuration).as_dict())

    def test_bad_yaml(self) -> None:

        with self.assertRaises(ParserError):
            test = """\
[A]
a={

"""
            print(loads(test, Configuration).as_dict())
