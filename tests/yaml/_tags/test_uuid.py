from __future__ import annotations

from uuid import uuid4

from granular_configuration_language._json import dumps
from granular_configuration_language.yaml import loads


def test_date() -> None:
    uuid = uuid4()
    output = loads(f"!UUID {uuid}")

    assert output == uuid
    assert dumps(output) == f'"{uuid}"'
