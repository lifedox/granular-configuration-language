from granular_configuration.yaml.classes import Masked
from granular_configuration.yaml.decorators import Tag, as_not_lazy, string_tag


@string_tag(Tag("!Mask"))
@as_not_lazy
def handler(value: str) -> Masked:
    return Masked(value)
