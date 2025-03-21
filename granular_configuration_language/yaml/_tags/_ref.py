from __future__ import annotations

import typing as typ

from granular_configuration_language.yaml.decorators import (
    Root,
    Tag,
    as_lazy_with_root,
    interpolate_value_with_ref,
    string_tag,
)
from granular_configuration_language.yaml.decorators.ref import resolve_json_ref


@string_tag(Tag("!Ref"), "Manipulator")
@as_lazy_with_root
@interpolate_value_with_ref
def handler(value: str, root: Root) -> typ.Any:
    return resolve_json_ref(value, root)
