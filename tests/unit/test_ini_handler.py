import unittest
from functools import reduce
from collections import OrderedDict

from yaml.parser import ParserError
from granular_configuration.ini_handler import loads
from granular_configuration.yaml_handler import loads as yaml_loads
from granular_configuration._config import Configuration
from granular_configuration.exceptions import IniKeyExistAsANonMapping, IniTryToReplaceExistingKey


class TestIniHandler(unittest.TestCase):
    def test_default(self):
        test = """\
[ROOT]
a=b
b=c
"""
        assert loads(test, Configuration).as_dict() == {"a": "b", "b": "c"}

    def test_default_dict(self):
        test = """\
[ROOT]
a=b
b=c
"""
        expected = OrderedDict()
        expected["a"] = "b"
        expected["b"] = "c"

        assert loads(test) == expected

    def test_value_types(self):
        test = """\
[ROOT]
a=1
b=true
c=null
d=1.123
e='1'
"""
        assert loads(test, Configuration).as_dict() == {"a": 1, "b": True, "c": None, "d": 1.123, "e": "1"}

    def test_key_types(self):
        test = """\
[ROOT]
'1'= "str"
1= integer
1.123= float
"1.123"= 'str'
null= test
True= "boolean"
false= "not"
"""
        assert loads(test, Configuration).as_dict() == {"1": "str", 1: "integer", 1.123: "float", "1.123": "str", None: "test", True: "boolean", False: "not"}

    def test_yaml_key_types(self):
        test = """\
'1': "str"
1: integer
1.123: float
"1.123": 'str'
null: test
True: "boolean"
false: "not"
"""
        assert yaml_loads(test, Configuration).as_dict() == {"1": "str", 1: "integer", 1.123: "float", "1.123": "str", None: "test", True: "boolean", False: "not"}

    def test_empty_dicts(self):
        test = """\
[A]

[F.G]

"""
        assert loads(test, Configuration).as_dict() == {"A": {}, "F":{"G": {}}}


    def test_nested_types(self):
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
        assert loads(test, Configuration).as_dict() == {"A": {"a":"b", "B":{"a":"b", "C":{"a":"b"}}, "D":{"E":{}}}, "F":{"G": {}}}


    def test_tags(self):
        test = """\
[A]
a=!Env 'no sub'
b=!Func functools.reduce
"""
        assert loads(test, Configuration).as_dict() == {"A": {"a":"no sub", "b": reduce}}


    def test_bad_replace(self):

        with self.assertRaises(IniTryToReplaceExistingKey):
            test = """\
[A]
a='str'

[A.a]

"""
            print(loads(test, Configuration).as_dict())


    def test_bad_replace_in_chain(self):

        with self.assertRaises(IniKeyExistAsANonMapping):
            test = """\
[A]
a='str'

[A.a.c]

"""
            print(loads(test, Configuration).as_dict())


    def test_bad_replace_at_root(self):

        with self.assertRaises(IniKeyExistAsANonMapping):
            test = """\
[ROOT]
A='str'

[A.a.c]
B='str'

"""
            print(loads(test, Configuration).as_dict())



    def test_out_of_order(self):

        with self.assertRaises(IniTryToReplaceExistingKey):
            test = """\
[A.a]

[A]


"""
            print(loads(test, Configuration).as_dict())



    def test_bad_yaml(self):

        with self.assertRaises(ParserError):
            test = """\
[A]
a={

"""
            print(loads(test, Configuration).as_dict())

