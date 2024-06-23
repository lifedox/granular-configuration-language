from granular_configuration.yaml_handler.decorators import Tag, lazy_exeception, string_tag


@string_tag(Tag("!Del"))
@lazy_exeception
def handler(value: str) -> str:
    return value
