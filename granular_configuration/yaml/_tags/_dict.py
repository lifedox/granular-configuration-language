import typing as typ

from granular_configuration.yaml.decorators import Tag, as_not_lazy, mapping_of_any_tag


@mapping_of_any_tag(Tag("!Dict"))
@as_not_lazy
def handler(value: typ.Mapping) -> dict:
    return dict(value)
