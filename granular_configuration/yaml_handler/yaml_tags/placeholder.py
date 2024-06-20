from granular_configuration._yaml_classes import Placeholder
from granular_configuration.yaml_handler.decorators import lazy_exeception, string_tag


@string_tag("!Placeholder")
@lazy_exeception
def handler(value: str) -> Placeholder:
    return Placeholder(value)
