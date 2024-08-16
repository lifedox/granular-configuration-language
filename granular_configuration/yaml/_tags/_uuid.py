from uuid import UUID

from granular_configuration.yaml.decorators import Tag, as_lazy, interpolate_value_without_ref, string_tag


@string_tag(Tag("!UUID"))
@as_lazy
@interpolate_value_without_ref
def handler(value: str) -> UUID:
    return UUID(hex=value)
