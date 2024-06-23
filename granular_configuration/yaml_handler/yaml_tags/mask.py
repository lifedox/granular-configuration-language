from granular_configuration._yaml_classes import Masked
from granular_configuration.yaml_handler.decorators import Tag, lazy_exeception, string_tag


@string_tag(Tag("!Mask"))
@lazy_exeception
def handler(value: str) -> Masked:
    return Masked(value)
