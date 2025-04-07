from __future__ import annotations

import abc
import collections.abc as tabc
import sys
import typing as typ
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from threading import RLock

if sys.version_info >= (3, 12):
    from typing import override
elif typ.TYPE_CHECKING:
    from typing_extensions import override
else:

    def override(func: tabc.Callable) -> tabc.Callable:
        return func


if sys.version_info >= (3, 13):
    from typing import TypeVar

    KT = TypeVar("KT", default=typ.Any)
    VT = TypeVar("VT", default=typ.Any)
elif typ.TYPE_CHECKING:
    from typing_extensions import TypeVar

    KT = TypeVar("KT", default=typ.Any)
    VT = TypeVar("VT", default=typ.Any)
else:
    from typing import TypeVar

    KT = TypeVar("KT")
    VT = TypeVar("VT")


P = typ.ParamSpec("P")
T = TypeVar("T")
"""
Generic Type
"""
RT = TypeVar("RT")
"""
Generic Return Type
"""
IT = TypeVar("IT")
"""
Generic Intermediate Type
"""

RootType = typ.NewType("RootType", tabc.Mapping)
"""
:py:class:`~typing.NewType` used to type the configuration root.

Aliases :py:class:`~collections.abc.Mapping` as root has to be a mapping for it to be used, and no Tag should mutate it.
"""

Root = RootType | None
"""
:py:data:`~typing.TypeAlias` used by type checking to identify the configuration root if it exists.
"""

Tag = typ.NewType("Tag", str)
"""
:py:class:`~typing.NewType` used to type tag strings. Must begin with ``!``.
"""


class Masked(str):
    """
    Used to keep secrets from printing to screen when running tests.

    - Inherits from :py:class:`str`.
    - Replaces the standard :py:meth:`~object.__repr__` result with the
      constant literal ``'<****>'``.
    - Used by :ref:`tag-mask` tag

    Note:
        Does not alter text or prevent :py:func:`print` from display the string value.
    """

    @override
    def __repr__(self) -> str:
        return "'<****>'"


class Placeholder:
    """
    Representation of :ref:`tag-placeholder` tag.

    Holds the ``!Placeholder`` message.
    """

    __slot__ = ("message",)

    def __init__(self, message: str) -> None:
        self.message: typ.Final = message

    @override
    def __str__(self) -> str:
        return str(self.message)


class LazyRoot:
    """
    Allows the Root reference to be defined outside loading. (Since it cannot be defined during Loading)
    """

    __slots__ = "__root"

    def __init__(self) -> None:
        self.__root: Root = None

    def _set_root(self, root: typ.Any) -> None:
        self.__root = root

    @property
    def root(self) -> Root:
        """
        Fetch the Root.
        """
        return self.__root

    @staticmethod
    def with_root(root: tabc.Mapping | Root) -> "LazyRoot":
        lazy_root = LazyRoot()
        lazy_root._set_root(root)
        return lazy_root


class LazyEval(abc.ABC, typ.Generic[RT]):
    """
    Base class for handling the output of a Tag that needs to be run just-in-time.
    """

    tag: typ.Final[Tag]
    """
    Tag that created this instance
    """

    def __init__(self, tag: Tag) -> None:
        self.tag = tag
        self.__done = False
        self.__lock = RLock()

    @abc.abstractmethod
    def _run(self) -> RT:
        """
        Run the Tag Logic.

        .. admonition:: Implementation Note
            :class: caution
            :collapsible: closed

            Caching is handled by this base class and not by this method.

        :return: Result of the lazy evaluation
        :rtype: RT
        """
        ...

    @cached_property
    def __result(self) -> RT:
        return self._run()

    def __run(self) -> RT:
        if self.__done:
            return self.__result
        else:
            with self.__lock:
                result = self.__result
                self.__done = True

            del self.__lock
            return result

    @cached_property
    def result(self) -> RT | typ.Any:
        """
        Result of the lazy evaluation, completing any chains. (Cached)
        """
        result = self.__run()
        while isinstance(result, LazyEval):
            result = result.__run()
        return result

    @override
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.tag}>"

    def __deepcopy__(self, memo: dict[int, typ.Any]) -> LazyEval:
        # Don't copy `LazyEval` instances
        return self

    def __copy__(self) -> LazyEval:
        # Don't copy `LazyEval` instances
        return self


@dataclass(frozen=True, kw_only=True, slots=True)
class LoadOptions:
    """
    Type: frozen :py:func:`dataclass <dataclasses.dataclass>`

    Holds the parameters used when loading the configuration file.
    """

    obj_pairs_func: type[tabc.Mapping[typ.Any, typ.Any]]
    """
    Type being used for YAML mappings
    """
    sequence_func: type[tuple[typ.Any] | list[typ.Any]]
    """
    Type being used for YAML sequences
    """
    mutable: bool
    """
    Value of the mutable flag
    """
    file_location: Path | None
    """
    Path of the file being loaded
    """
    relative_to_directory: Path
    """
    Path for making relative file paths
    """
    previous: LoadOptions | None
    """
    Pointer to previous options, if this file was loaded by another
    """


@dataclass(frozen=True, kw_only=True, slots=True)
class StateHolder:
    """
    Type: frozen :py:func:`dataclass <dataclasses.dataclass>`

    Used to pass state define while Loading configuration files into Tags.
    """

    options: LoadOptions
    """
    Options from Loading
    """
    lazy_root_obj: LazyRoot
    """
    Shared reference to the final root configuration
    """
