from __future__ import annotations

import typing as typ

from granular_configuration._config import Configuration
from granular_configuration.yaml_handler.decorators import Tag, make_lazy, sequence_of_any_tag


@sequence_of_any_tag(Tag("!Merge"))
@make_lazy
def handler(value: typ.Sequence[typ.Any]) -> Configuration:
    from granular_configuration import merge

    return merge(value)
