from __future__ import annotations

from sys import intern

from granular_configuration_language.yaml import loads


def test_mask() -> None:
    not_interned = loads("!Sub Not auto interned 1")
    interned = loads("!Intern Not auto interned 2")

    assert not_interned is not intern("Not auto interned 1")
    assert interned is intern("Not auto interned 2")
