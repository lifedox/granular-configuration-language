from granular_configuration.yaml.decorators import Tag, make_lazy_exeception, string_tag


@string_tag(Tag("!Del"))
@make_lazy_exeception
def handler(value: str) -> str:
    return value
