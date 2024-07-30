import json

from granular_configuration import Configuration, json_default
from granular_configuration.yaml import loads


def test_json_dump() -> None:
    test: Configuration = loads(
        """
a: b
          """
    )

    expected = """{"a": "b"}"""
    assert json.dumps(test, default=json_default) == expected
