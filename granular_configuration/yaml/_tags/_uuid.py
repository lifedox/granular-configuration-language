from uuid import UUID

from granular_configuration.yaml.decorators import Tag, as_lazy, string_tag


@string_tag(Tag("!UUID"))
@as_lazy
def handler(value: str) -> UUID:
    return UUID(hex=value)
