from __future__ import annotations

from decimal import Decimal

from granular_configuration_language.yaml.decorators import Tag, as_lazy, interpolate_value_without_ref, string_tag


@string_tag(Tag("!Decimal"), "Typer")
@as_lazy
@interpolate_value_without_ref
def tag(value: str) -> Decimal:
    return Decimal(value)
