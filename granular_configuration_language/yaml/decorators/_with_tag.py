from __future__ import annotations

import collections.abc as tabc
import typing as typ

from granular_configuration_language.yaml.classes import RT, P, Tag
from granular_configuration_language.yaml.decorators._tag_tracker import tracker


def with_tag(func: tabc.Callable[typ.Concatenate[Tag, P], RT]) -> tabc.Callable[P, RT]:
    """
    .. versionadded:: 2.3.0

    Injects your tag as the first parameter to your "Tag" Function

    The wrapped function has the :py:class:`.Tag` parameter removed.

    :param ~collections.abc.Callable[~typing.Concatenate[Tag, P], RT] func: Function to be wrapped
    :return: Wrapped Function
    :rtype: ~collections.abc.Callable[P, RT]

    :example:
        .. code-block:: python

            @string_tag(Tag("!Tag"))
            @as_lazy
            @interpolate_value_without_ref
            @with_tag
            def tag(tag: Tag, value: str) -> Any:
                ...
    """

    @tracker.wraps(func)
    def lazy_wrapper(*args: P.args, **kwargs: P.kwargs) -> RT:
        return func(tracker.get(func).tag, *args, **kwargs)

    return lazy_wrapper
