from __future__ import annotations

import collections.abc as tabc
import copy
import sys
import typing as typ
from collections.abc import Mapping
from functools import cached_property

import granular_configuration_language  # Avoid circular imports in type signatures
from granular_configuration_language import Configuration
from granular_configuration_language._simple_future import SimpleFuture

if sys.version_info >= (3, 12):
    from typing import override
elif typ.TYPE_CHECKING:
    from typing_extensions import override
else:

    def override(func: tabc.Callable) -> tabc.Callable:
        return func


@Configuration.register  # pyright: ignore
class SafeConfigurationProxy(Mapping):
    """
    Wraps a :py:class:`.LazyLoadConfiguration` instance to proxy all method and
    attribute calls to its :py:class:`.Configuration` instance.

    Passes ``isinstance( ... , Configuration)`` checks, as this class is
    :py:meth:`~abc.ABCMeta.register`-ed as a subclass of
    :py:class:`.Configuration`.

    .. admonition:: Implementation Reasoning

        Wrapping :py:class:`.LazyLoadConfiguration` maintains all laziness
        build into :py:class:`.LazyLoadConfiguration`, while exposing all
        of :py:class:`.Configuration`

        This class is used behind a :py:func:`typing.cast` in
        :py:meth:`.LazyLoadConfiguration.as_typed`, so it is not exposed
        explicitly.

    :param LazyLoadConfiguration llc:
        :py:class:`.LazyLoadConfiguration` instance to be wrapped
    """

    __slots__ = ("__llc",)

    def __init__(self, llc: granular_configuration_language.LazyLoadConfiguration) -> None:
        self.__llc = llc

    def __getattr__(self, name: str) -> typ.Any:
        return getattr(self.__llc.config, name)

    @override
    def __getitem__(self, key: typ.Any) -> typ.Any:
        return self.__llc.config[key]

    @override
    def __iter__(self) -> tabc.Iterator[typ.Any]:
        return iter(self.__llc.config)

    @override
    def __len__(self) -> int:
        return len(self.__llc.config)

    @override
    def __contains__(self, key: typ.Any) -> bool:
        return key in self.__llc.config

    def __deepcopy__(self, memo: dict[int, typ.Any]) -> Configuration:
        return copy.deepcopy(self.__llc.config, memo=memo)

    def __copy__(self) -> Configuration:
        return copy.copy(self.__llc.config)

    copy = __copy__

    @override
    def __repr__(self) -> str:
        return repr(self.__llc.config)


def _eagerio_load(llc: granular_configuration_language.LazyLoadConfiguration) -> Configuration:
    return llc.config


@Configuration.register  # pyright: ignore
class EagerIOConfigurationProxy(Mapping):
    """
    .. versionadded:: 2.3.0

    Wraps a :py:class:`.LazyLoadConfiguration` instance to proxy all method and
    attribute calls to its :py:class:`.Configuration` instance.

    Passes ``isinstance( ... , Configuration)`` checks, as this class is
    :py:meth:`~abc.ABCMeta.register`-ed as a subclass of
    :py:class:`.Configuration`.

    .. admonition:: Part of the EagerIO feature set
        :class: caution

        This immediately spawns a thread to load and build the Configuration in
        the background, so that future calls are non-/minimally blocking.

        This class is used behind a :py:func:`typing.cast` in
        :py:meth:`.LazyLoadConfiguration.eager_load`, so it is not exposed
        explicitly.

    :param LazyLoadConfiguration llc:
        :py:class:`.LazyLoadConfiguration` instance to be wrapped
    """

    def __init__(self, llc: granular_configuration_language.LazyLoadConfiguration) -> None:
        self.__future = SimpleFuture(_eagerio_load, llc)

    @cached_property
    def __config(self) -> Configuration:
        try:
            return self.__future.result
        finally:
            del self.__future

    def __getattr__(self, name: str) -> typ.Any:
        return getattr(self.__config, name)

    @override
    def __getitem__(self, key: typ.Any) -> typ.Any:
        return self.__config[key]

    @override
    def __iter__(self) -> tabc.Iterator[typ.Any]:
        return iter(self.__config)

    @override
    def __len__(self) -> int:
        return len(self.__config)

    @override
    def __contains__(self, key: typ.Any) -> bool:
        return key in self.__config

    def __deepcopy__(self, memo: dict[int, typ.Any]) -> Configuration:
        return copy.deepcopy(self.__config, memo=memo)

    def __copy__(self) -> Configuration:
        return copy.copy(self.__config)

    copy = __copy__

    @override
    def __repr__(self) -> str:
        return repr(self.__config)
