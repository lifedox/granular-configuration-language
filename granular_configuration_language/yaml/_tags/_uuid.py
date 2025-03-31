from __future__ import annotations

from uuid import UUID

from granular_configuration_language.yaml.decorators import Tag, as_lazy, interpolate_value_without_ref, string_tag


@string_tag(Tag("!UUID"), "Typer")
@as_lazy
@interpolate_value_without_ref
def tag(value: str) -> UUID:
    return UUID(hex=value)
