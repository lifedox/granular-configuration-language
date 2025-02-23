from __future__ import annotations

from granular_configuration_language.yaml.classes import Placeholder
from granular_configuration_language.yaml.decorators import Tag, as_not_lazy, string_tag


@string_tag(Tag("!Placeholder"), "Manipulator")
@as_not_lazy
def handler(value: str) -> Placeholder:
    return Placeholder(value)
