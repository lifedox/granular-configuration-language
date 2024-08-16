from __future__ import annotations

import typing as typ

from granular_configuration.yaml.decorators import Tag, as_lazy, sequence_of_any_tag
from granular_configuration._config import Configuration


@sequence_of_any_tag(Tag("!Merge"))
@as_lazy
def handler(value: typ.Sequence[typ.Any]) -> Configuration:
    from granular_configuration import merge

    return merge(value)
