from __future__ import annotations

from granular_configuration_language.yaml.decorators import (
    Root,
    Tag,
    as_lazy_with_root,
    interpolate_value_with_ref,
    string_tag,
)
from granular_configuration_language.yaml.decorators.interpolate import interpolation_needs_ref_condition


@string_tag(Tag("!Sub"))
@as_lazy_with_root(needs_root_condition=interpolation_needs_ref_condition)
@interpolate_value_with_ref
def handler(value: str, root: Root) -> str:
    return value
