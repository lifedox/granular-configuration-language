from __future__ import annotations

import collections.abc as tabc
import typing as typ

import granular_configuration_language
from granular_configuration_language._configuration import Configuration
from granular_configuration_language.yaml.decorators import (
    LoadOptions,
    Tag,
    as_lazy_with_load_options,
    sequence_of_any_tag,
)


@sequence_of_any_tag(Tag("!Merge"), "Manipulator")
@as_lazy_with_load_options
def tag(value: tabc.Sequence[typ.Any], options: LoadOptions) -> Configuration:
    return granular_configuration_language.merge(value, mutable=options.mutable)
