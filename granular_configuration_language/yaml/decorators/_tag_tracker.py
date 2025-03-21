from __future__ import annotations

import collections.abc as tabc
import dataclasses
import itertools
import operator as op
import typing as typ
from functools import wraps as real_wraps

from granular_configuration_language.yaml.classes import RT, P, Tag


@dataclasses.dataclass
class HandlerAttributes:
    func: tabc.Callable
    is_not_lazy: bool = False
    is_eager: bool = False
    is_without_ref = False
    is_with_ref = False
    needs_root_condition: tabc.Callable | None = None
    eager_io: tabc.Callable | None = None
    tag: Tag = Tag("")

    def set_tag(self, tag: Tag) -> None:
        self.tag = tag


class HandlerTracker(tabc.Iterable[HandlerAttributes]):
    def __init__(self) -> None:
        self.__data: dict[int, HandlerAttributes] = dict()

    def __iter__(self) -> tabc.Iterator[HandlerAttributes]:
        return map(
            next,
            map(
                op.itemgetter(1),
                itertools.groupby(
                    sorted(
                        self.__data.values(),
                        key=op.attrgetter("tag"),
                    ),
                    op.attrgetter("tag"),
                ),
            ),
        )

    def wrapped(self, wrapped_func: tabc.Callable, func: tabc.Callable) -> None:
        id_wf = id(wrapped_func)
        id_f = id(func)

        if id_f in self.__data:
            self.__data[id_wf] = self.__data[id_wf]
        elif id_wf in self.__data:
            self.__data[id_f] = self.__data[id_wf]
        else:
            attributes = HandlerAttributes(func)
            self.__data[id_f] = attributes
            self.__data[id_wf] = attributes

    def get(self, func: tabc.Callable) -> HandlerAttributes:
        id_f = id(func)
        if id_f in self.__data:
            return self.__data[id_f]
        else:
            attributes = HandlerAttributes(func)
            self.__data[id_f] = attributes
            return attributes

    def wraps(
        self,
        func: tabc.Callable,
        /,
        *,
        track_needs_root_condition: tabc.Callable | None = None,
        track_eager_io: tabc.Callable | None = None,
    ) -> tabc.Callable[[tabc.Callable[P, RT]], tabc.Callable[P, RT]]:
        if track_needs_root_condition:
            self.get(func).needs_root_condition = track_needs_root_condition

        if track_eager_io:
            self.get(func).eager_io = track_eager_io

            if self.get(track_eager_io).is_without_ref:
                self.track_as_without_ref(func)

        def wrapper(wrapper_func: tabc.Callable[P, RT]) -> tabc.Callable[P, RT]:
            self.wrapped(func, wrapper_func)
            return real_wraps(func)(wrapper_func)

        return wrapper

    def track_as_not_lazy(self, func: tabc.Callable) -> None:
        self.get(func).is_not_lazy = True

    def track_as_with_ref(self, func: tabc.Callable) -> None:
        self.get(func).is_with_ref = True

    def track_as_without_ref(self, func: tabc.Callable) -> None:
        self.get(func).is_without_ref = True


tracker: typ.Final = HandlerTracker()
