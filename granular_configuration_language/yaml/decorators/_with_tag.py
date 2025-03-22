from __future__ import annotations

import collections.abc as tabc
import typing as typ

from granular_configuration_language.yaml.classes import RT, P, Tag
from granular_configuration_language.yaml.decorators._tag_tracker import tracker


def with_tag(func: tabc.Callable[typ.Concatenate[Tag, P], RT]) -> tabc.Callable[P, RT]:
    @tracker.wraps(func)
    def lazy_wrapper(*args: P.args, **kwargs: P.kwargs) -> RT:
        return func(tracker.get(func).tag, *args, **kwargs)

    return lazy_wrapper
