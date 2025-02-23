from __future__ import annotations

import collections.abc as tabc
import typing as typ
from collections import OrderedDict

from granular_configuration_language.exceptions import ErrorWhileLoadingTags
from granular_configuration_language.yaml.decorators._base import Tag, TagConstructor


class TagSet(tabc.Iterable[TagConstructor], typ.Container[str]):
    def __init__(self, tags: tabc.Iterable[TagConstructor]) -> None:
        self.__state: OrderedDict[Tag, TagConstructor] = OrderedDict()

        for tc in tags:
            tag = tc.tag
            if tag in self.__state:
                raise ErrorWhileLoadingTags(
                    f"Tag is already defined. `{repr(tc)}` attempted to replace `{repr(self.__state[tag])}`"
                )
            else:
                self.__state[tag] = tc

    def __contains__(self, x: typ.Any) -> bool:
        return x in self.__state

    def __iter__(self) -> tabc.Iterator[TagConstructor]:
        return iter(self.__state.values())

    def __repr__(self) -> str:
        return f"TagSet{{{','.join(sorted(self.__state.keys()))}}}"

    def has_tags(self, *tags: Tag | str) -> bool:
        return all(map(self.__contains__, tags))

    def does_not_have_tags(self, *tags: Tag | str) -> bool:
        return not any(map(self.__contains__, tags))

    def get_subset(self, *select: str) -> TagSet:
        def subset() -> tabc.Iterator[TagConstructor]:
            for tag in self:
                if tag.tag in select:
                    yield tag

        return TagSet(subset())
