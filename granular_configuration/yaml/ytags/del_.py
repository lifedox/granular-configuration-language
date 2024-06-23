from granular_configuration.yaml.decorators import Tag, lazy_exeception, string_tag


@string_tag(Tag("!Del"))
@lazy_exeception
def handler(value: str) -> str:
    return value
