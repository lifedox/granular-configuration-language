from granular_configuration.yaml.decorators import (
    Root,
    Tag,
    as_lazy_with_root,
    interpolate_value_without_ref,
    string_tag,
)
from granular_configuration.yaml.decorators.ref import resolve_json_ref


@string_tag(Tag("!Ref"))
@as_lazy_with_root
@interpolate_value_without_ref
def handler(value: str, root: Root) -> str:
    return resolve_json_ref(value, root)
