from __future__ import annotations

import abc
import collections.abc as tabc
import typing as typ
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from threading import RLock

P = typ.ParamSpec("P")
T = typ.TypeVar("T")
RT = typ.TypeVar("RT")

RootType = typ.NewType("RootType", tabc.Mapping)
"""
:py:class:`~typing.NewType` used to type the configuration root.

Aliases :py:class:`~collections.abc.Mapping` as root has to be a mapping for it to be used and no Tag should mutate it.
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

        :return: Result of the lazy evaluation
        :rtype: RT
        :Note: Caching does not occur within this method
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

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.tag}>"

    def __deepcopy__(self, memo: dict[int, typ.Any]) -> LazyEval:
        # Don't copy LazyEval's
        return self

    def __copy__(self) -> LazyEval:
        # Don't copy LazyEval's
        return self


@dataclass(frozen=True, kw_only=True, slots=True)
class LoadOptions:
    """
    Type: frozen :py:func:`dataclass <dataclasses.dataclass>`

    Holds the parameters used when loading the configuration file.
    """

    obj_pairs_func: type[tabc.Mapping]
    """
    Type being used for YAML mappings
    """
    sequence_func: type[tabc.Sequence]
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
