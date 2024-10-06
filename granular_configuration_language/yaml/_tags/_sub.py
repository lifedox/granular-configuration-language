from granular_configuration_language.yaml.decorators import Root, Tag, as_lazy_with_root, interpolate_value_with_ref, string_tag
from granular_configuration_language.yaml.decorators.interpolate import does_ref_check


@string_tag(Tag("!Sub"))
@as_lazy_with_root(needs_root_check=does_ref_check)
@interpolate_value_with_ref
def handler(value: str, root: Root) -> str:
    return value
