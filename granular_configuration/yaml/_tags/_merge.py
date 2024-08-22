from __future__ import annotations

import typing as typ

from granular_configuration._config import Configuration
from granular_configuration.yaml.decorators import LoadOptions, Tag, as_lazy_with_load_options, sequence_of_any_tag


@sequence_of_any_tag(Tag("!Merge"))
@as_lazy_with_load_options
def handler(value: typ.Sequence[typ.Any], options: LoadOptions) -> Configuration:
    from granular_configuration import merge

    return merge(value, mutable=options.mutable)
