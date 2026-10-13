from __future__ import annotations

from sys import intern

from granular_configuration_language.yaml.decorators import Tag, as_lazy, interpolate_value_without_ref, string_tag


@string_tag(Tag("!Intern"), "Typer")
@as_lazy
@interpolate_value_without_ref
def tag(value: str) -> str:
    return intern(value)
