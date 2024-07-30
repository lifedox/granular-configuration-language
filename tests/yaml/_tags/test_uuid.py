import json
from uuid import uuid4

from granular_configuration import json_default
from granular_configuration.yaml import loads


def test_date() -> None:
    uuid = uuid4()
    output = loads(f"!UUID {uuid}")

    assert output == uuid
    assert json.dumps(output, default=json_default) == f'"{uuid}"'
