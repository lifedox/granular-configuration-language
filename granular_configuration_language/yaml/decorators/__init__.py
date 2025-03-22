from __future__ import annotations

from granular_configuration_language.yaml.classes import LoadOptions, Root
from granular_configuration_language.yaml.decorators._base import Tag, TagDecoratorBase
from granular_configuration_language.yaml.decorators._lazy import (
    as_lazy,
    as_lazy_with_load_options,
    as_lazy_with_root,
    as_lazy_with_root_and_load_options,
    as_not_lazy,
)
from granular_configuration_language.yaml.decorators._type_checking import (
    mapping_of_any_tag,
    sequence_of_any_tag,
    string_or_twople_tag,
    string_tag,
)
from granular_configuration_language.yaml.decorators._with_tag import with_tag
from granular_configuration_language.yaml.decorators.interpolate import (
    interpolate_value_with_ref,
    interpolate_value_without_ref,
)
