from __future__ import annotations

from datetime import date, datetime

from granular_configuration_language.yaml.decorators import Tag, as_lazy, interpolate_value_without_ref, string_tag


@string_tag(Tag("!Date"), "Typer")
@as_lazy
@interpolate_value_without_ref
def date_(value: str) -> date:
    return date.fromisoformat(value)


@string_tag(Tag("!DateTime"), "Typer")
@as_lazy
@interpolate_value_without_ref
def datetime_(value: str) -> date:
    return datetime.fromisoformat(value)
