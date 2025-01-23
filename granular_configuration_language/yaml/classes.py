from __future__ import annotations

import abc
import typing as typ
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from threading import RLock

RT = typ.TypeVar("RT")

RootType = typ.NewType("RootType", typ.Mapping)
"""
Type used to type the configuration root.

Aliases :py:class:`~collections.abc.Mapping` as root has to be a mapping for it to be used.
"""

Root = RootType | None
"""
Type used by type checking to identify the configuration root if it exists.
"""

Tag = typ.NewType("Tag", str)
"""
:py:class:`~typing.NewType` used to type tag strings.
"""


class Masked(str):
    """
    Used to keep secrets from printing to screen when running tests.

    Does not alter text or prevent :py:func:`print` from display the string value.

    Inherits for :py:class:`str`. Replaces the :py:meth:`~object.__repr__` with the constant :code:`"'<****>'"`.

    Used by :code:`!Mask` tag
    """

    def __repr__(self) -> str:
        return "'<****>'"


class Placeholder:
    """
    Representation of :code:`!Placeholder` tag.

    Holds the :code:`!Placeholder` message.
    """

    __slot__ = ("message",)

    def __init__(self, message: str) -> None:
        self.message: typ.Final = message

    def __str__(self) -> str:
        return str(self.message)


class LazyRoot:
    __slots__ = "__root"

    def __init__(self) -> None:
        self.__root: Root = None

    def _set_root(self, root: typ.Any) -> None:
        self.__root = root

    @property
    def root(self) -> Root:
        return self.__root

    @staticmethod
    def with_root(root: typ.Mapping | Root) -> "LazyRoot":
        lazy_root = LazyRoot()
        lazy_root._set_root(root)
        return lazy_root


class LazyEval(abc.ABC, typ.Generic[RT]):
    """
    Base class for handling the output of a Tag that needs to be run just-in-time.
    """

    def __init__(self, tag: Tag) -> None:
        self.tag = tag
        self.done = False
        self.__lock = RLock()

    @abc.abstractmethod
    def _run(self) -> RT: ...

    @cached_property
    def __result(self) -> RT:
        return self._run()

    def __run(self) -> RT:
        if self.done:
            return self.__result
        else:
            with self.__lock:
                result = self.__result
                self.done = True

            del self.__lock
            return result

    @cached_property
    def result(self) -> RT | typ.Any:
        """
        Result of the lazy evaluation, completing any chains
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


@dataclass(frozen=True, kw_only=True)
class LoadOptions:
    """
    Holds the parameters used when loading the configuration file
    """

    obj_pairs_func: typ.Type[typ.Mapping]
    """
    Type being used for YAML mappings
    """
    sequence_func: typ.Type[typ.Sequence]
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


@dataclass(frozen=True, kw_only=True)
class StateHolder:
    options: LoadOptions
    lazy_root_obj: LazyRoot
