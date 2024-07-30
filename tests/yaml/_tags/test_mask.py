from granular_configuration import Masked
from granular_configuration.yaml import loads


def test_mask() -> None:
    output = loads("!Mask secret")

    assert repr(output) == "'<****>'"
    assert str(output) == "secret"
    assert output == "secret"
    assert isinstance(output, Masked)
