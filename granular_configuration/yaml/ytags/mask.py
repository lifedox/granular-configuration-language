from granular_configuration.yaml.classes import Masked
from granular_configuration.yaml.decorators import Tag, lazy_exeception, string_tag


@string_tag(Tag("!Mask"))
@lazy_exeception
def handler(value: str) -> Masked:
    return Masked(value)
