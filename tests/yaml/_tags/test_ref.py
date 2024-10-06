import pytest

from granular_configuration_language import Configuration
from granular_configuration_language.exceptions import JSONPathQueryFailed, JSONPointerQueryFailed, RefMustStartFromRoot
from granular_configuration_language.yaml import loads


def test_ref__jsonpath() -> None:
    test_data = """\
data:
    dog:
        name: nitro
    cat:
        name: never owned a cat
tests:
    a: !Ref $.data.dog.name
    b: !Ref $.data.dog
    c: !Ref $.data.*.name
"""

    output: Configuration = loads(test_data)
    assert output.tests.as_dict() == dict(
        a="nitro",
        b={"name": "nitro"},
        c=["nitro", "never owned a cat"],
    )
    assert output.data.dog.name is output.tests.a
    assert output.data.dog is output.tests.b


def test_ref__jsonpointer() -> None:
    test_data = """\
data:
    dog:
        name: nitro
    cat:
        name: never owned a cat
tests:
    a: !Ref /data/dog/name
    b: !Ref /data/dog
"""

    output: Configuration = loads(test_data)
    assert output.tests.as_dict() == dict(
        a="nitro",
        b={"name": "nitro"},
    )
    assert output.data.dog.name is output.tests.a
    assert output.data.dog is output.tests.b


def test_jsonpath_missing_throws_exception() -> None:
    test_data = """
a: !Ref $.no_data.here
b: c
"""
    with pytest.raises(JSONPathQueryFailed):
        loads(test_data).as_dict()


def test_jsonpointer_missing_throws_exception() -> None:
    test_data = """
a: !Ref /no_data/here
b: c
"""
    with pytest.raises(JSONPointerQueryFailed):
        assert loads(test_data).as_dict() == {}


def test_syntax_error_throws_exception() -> None:
    test_data = """
a: !Ref no_data/here
b: c
"""
    with pytest.raises(RefMustStartFromRoot):
        assert loads(test_data).as_dict() == {}
