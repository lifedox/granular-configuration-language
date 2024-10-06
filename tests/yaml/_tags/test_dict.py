from granular_configuration_language.yaml import loads


def test_mapping_of_any_tag_takes_mapping() -> None:
    value = loads(
        """
!Dict
a: 1
b: 2
!Del c: 3
"""
    )

    assert type(value) is dict
    assert value == dict(a=1, b=2)


def test_laziness() -> None:
    value = loads(
        """
base: data
test: !Dict
    a: !Ref /base
    b: !Ref /base
    c: !Ref /base
    d: !Ref /base
"""
    ).test

    assert type(value) is dict
    assert value == {
        "a": "data",
        "b": "data",
        "c": "data",
        "d": "data",
    }
