from __future__ import annotations

from granular_configuration_language.yaml.classes import Masked
from granular_configuration_language.yaml.decorators import Tag, as_lazy, interpolate_value_without_ref, string_tag


@string_tag(Tag("!Mask"), "Typer")
@as_lazy
@interpolate_value_without_ref
def handler(value: str) -> Masked:
    return Masked(value)
