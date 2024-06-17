from granular_configuration.yaml_handler.classes import Placeholder
from granular_configuration.yaml_handler.decorators import lazy_exeception, string_only_tag


@string_only_tag("!Placeholder")
@lazy_exeception
def handler(value: str) -> Placeholder:
    return Placeholder(value)
