from granular_configuration.yaml.decorators import (
    Root,
    Tag,
    as_lazy_with_root,
    interpolate_value_with_sub_rules,
    string_tag,
)


@string_tag(Tag("!Sub"))
@as_lazy_with_root
@interpolate_value_with_sub_rules
def handler(value: str, root: Root) -> str:
    return value
