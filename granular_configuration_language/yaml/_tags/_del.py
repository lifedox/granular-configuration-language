from __future__ import annotations

from granular_configuration_language.yaml.decorators import Tag, as_not_lazy, string_tag


@string_tag(Tag("!Del"), "Manipulator")
@as_not_lazy
def tag(value: str) -> str:
    return value
