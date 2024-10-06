from granular_configuration_language.yaml.decorators import Masked, Tag, as_not_lazy, interpolate_value_without_ref, string_tag


@string_tag(Tag("!Mask"))
@as_not_lazy
@interpolate_value_without_ref
def handler(value: str) -> Masked:
    return Masked(value)
