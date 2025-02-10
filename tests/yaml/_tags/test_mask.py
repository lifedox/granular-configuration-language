from __future__ import annotations

from granular_configuration_language import Masked
from granular_configuration_language.yaml import loads


def test_mask() -> None:
    output = loads("!Mask secret")

    assert repr(output) == "'<****>'"
    assert str(output) == "secret"
    assert output == "secret"
    assert isinstance(output, Masked)
