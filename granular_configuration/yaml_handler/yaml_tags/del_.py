from granular_configuration.yaml_handler.decorators import lazy_exeception, string_only_tag


@string_only_tag("!Del")
@lazy_exeception
def handler(value: str) -> str:
    return value
