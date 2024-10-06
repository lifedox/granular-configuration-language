from __future__ import annotations

from granular_configuration_language._config import Configuration
from granular_configuration_language.yaml.decorators import Tag, as_lazy, mapping_of_any_tag


@mapping_of_any_tag(Tag("!Dict"))
@as_lazy
def handler(value: Configuration) -> dict:
    return value.as_dict()
