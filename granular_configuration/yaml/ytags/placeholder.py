from granular_configuration.yaml.classes import Placeholder
from granular_configuration.yaml.decorators import Tag, lazy_exeception, string_tag


@string_tag(Tag("!Placeholder"))
@lazy_exeception
def handler(value: str) -> Placeholder:
    return Placeholder(value)
