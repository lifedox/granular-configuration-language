from __future__ import annotations

import typing as typ

from granular_configuration.yaml.decorators import Tag, as_lazy, sequence_of_any_tag

if typ.TYPE_CHECKING:  # pragma: no cover
    # Fixes mypy `Cannot determine type of "handler"`
    # Probably forces a ForwardRef during mypy TYPE_CHECKING
    from granular_configuration._config import Configuration
else:  # pragma: no cover  # TYPE_CHECKING
    # Allows `inspect.get_annotations(handler, eval_str=True)`
    from granular_configuration._config import Configuration

merge_tag: typ.Final = Tag("!Merge")


@sequence_of_any_tag(merge_tag)
@as_lazy
def handler(value: typ.Sequence[typ.Any]) -> Configuration:
    from granular_configuration import merge

    return merge(value)
