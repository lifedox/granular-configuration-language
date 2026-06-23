from __future__ import annotations

from decimal import Decimal

import pytest

from granular_configuration_language._json import dumps
from granular_configuration_language.yaml import loads


@pytest.mark.parametrize("value", ["1", "0", "1.23", "1.3333"])
def test(value: str) -> None:
    output = loads(f"!Decimal {value}")

    assert output == Decimal(value)
    assert dumps(output) == f'"{value}"'
