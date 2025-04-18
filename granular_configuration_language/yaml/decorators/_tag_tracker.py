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

    def wrapped(self, func: tabc.Callable, wrapped_func: tabc.Callable) -> None:
        self.__data[id(wrapped_func)] = self.__data[id(func)]

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
        needs_root_condition: tabc.Callable | None = None,
        eager_io: tabc.Callable | None = None,
        **attributes: typ.Literal[True],
    ) -> tabc.Callable[[tabc.Callable[P, RT]], tabc.Callable[P, RT]]:
        attrs = self.get(func)

        if attributes.pop("fake_tag", None):
            attrs.set_tag(Tag("!Faker"))

        for attribute in attributes:
            setattr(attrs, attribute, True)

        if needs_root_condition:
            attrs.needs_root_condition = needs_root_condition

        if eager_io:
            attrs.eager_io = eager_io

            if self.get(eager_io).is_without_ref:
                attrs.is_without_ref = True
            else:  # pragma: no cover
                pass

        def wrapper(wrapper_func: tabc.Callable[P, RT]) -> tabc.Callable[P, RT]:
            self.wrapped(func, wrapper_func)
            return real_wraps(func)(wrapper_func)

        return wrapper


tracker: typ.Final = HandlerTracker()
