from __future__ import annotations

import typing as typ

from granular_configuration.yaml.decorators import Tag, make_lazy, sequence_of_any_tag

if typ.TYPE_CHECKING:
    # Fixes mypy `Cannot determine type of "handler"`
    # Probably forces a ForwardRef during mypy TYPE_CHECKING
    from granular_configuration._config import Configuration
else:
    # Allows `inspect.get_annotations(handler, eval_str=True)`
    from granular_configuration._config import Configuration

merge_tag: typ.Final = Tag("!Merge")


@sequence_of_any_tag(merge_tag)
@make_lazy
def handler(value: typ.Sequence[typ.Any]) -> Configuration:
    from granular_configuration import merge

    return merge(value)