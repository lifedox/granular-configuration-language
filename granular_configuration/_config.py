from __future__ import annotations

import copy
import json
import sys
import typing as typ
import weakref
from itertools import starmap

from granular_configuration._s import setter_secret
from granular_configuration.base_path import BasePathPart
from granular_configuration.exceptions import InvalidBasePathException, PlaceholderConfigurationError
from granular_configuration.yaml import LazyEval, Placeholder

if sys.version_info >= (3, 11):
    from typing import Generic, TypedDict, Unpack
elif typ.TYPE_CHECKING:
    from typing_extensions import Generic, TypedDict, Unpack


_T = typ.TypeVar("_T")

if sys.version_info >= (3, 11) or typ.TYPE_CHECKING:

    class Kwords_typed_get(Generic[_T], TypedDict, total=False):
        default: _T
        predicate: typ.Callable[[typ.Any], typ.TypeGuard[_T]]


class AttributeName(typ.Iterable[str]):
    __slots__ = ("__prev", "__name", "__weakref__")

    def __init__(self, prev: AttributeName | typ.Iterable[str], name: typ.Any) -> None:
        self.__prev = prev
        self.__name = name

    @staticmethod
    def as_root() -> AttributeName:
        return AttributeName(tuple(), "$")

    def append_suffix(self, name: typ.Any) -> AttributeName:
        return AttributeName(weakref.proxy(self), name)

    def with_suffix(self, name: typ.Any) -> str:
        return ".".join(self._plus_one(name))

    def __iter__(self) -> typ.Iterator[str]:
        yield from self.__prev
        yield self.__name if isinstance(self.__name, str) else f"`{repr(self.__name)}`"

    def _plus_one(self, last: str) -> typ.Iterator[str]:
        yield from iter(self)
        yield last if isinstance(last, str) else f"`{repr(last)}`"

    def __str__(self) -> str:
        return ".".join(self)


class Configuration(typ.Mapping[typ.Any, typ.Any]):
    def __init__(self, *arg: typ.Mapping | typ.Iterable[tuple[typ.Any, typ.Any]], **kwargs: typ.Any) -> None:
        self.__data: dict[typ.Any, typ.Any] = dict(*arg, **kwargs)
        self.__attribute_name = AttributeName.as_root()

    #################################################################
    # Required for Mapping
    #################################################################

    def __iter__(self) -> typ.Iterator:
        return iter(self.__data)

    def __len__(self) -> int:
        return len(self.__data)

    def __getitem__(self, name: typ.Any) -> typ.Any:
        try:
            value = self.__data[name]
        except KeyError:
            # Start the stack trace here
            if isinstance(name, BasePathPart):
                raise InvalidBasePathException(
                    f"Base Path `{self.__attribute_name.with_suffix(name)}` does not exist."
                ) from None
            else:
                raise KeyError(repr(name)) from None

        if isinstance(value, Placeholder):
            raise PlaceholderConfigurationError(
                f'Placeholder `{self.__attribute_name.with_suffix(name)}` was not overwritten. Message: "{value}"'
            )
        elif isinstance(value, LazyEval):
            try:
                value = value.result
                self._private_set(name, value, setter_secret)
            except RecursionError:
                raise RecursionError(
                    f"{value.tag} at `{self.__attribute_name.with_suffix(name)}` caused a recursion error. Please check your configuration for a self-referencing loop."
                ) from None

        if isinstance(value, Configuration):
            value.__attribute_name = self.__attribute_name.append_suffix(name)
            return value
        else:
            return value

    #################################################################
    # Overridden Mapping methods
    #################################################################

    def __contains__(self, key: typ.Any) -> bool:
        return key in self.__data

    def get(self, key: typ.Any, default: typ.Any = None) -> typ.Any:
        return self[key] if self.exists(key) else default

    #################################################################
    # Required behavior overrides
    #################################################################

    def __getattr__(self, name: str) -> typ.Any:
        """
        Provides potentially cleaner path as an alternative to __getitem__.
        Throws AttributeError instead of KeyError, as compared to __getitem__ when an attribute is not present.
        """
        if name not in self:
            raise AttributeError(f"Request attribute `{self.__attribute_name.with_suffix(name)}` does not exist")

        return self[name]

    def __repr__(self) -> str:
        return repr(self.__data)

    def __deepcopy__(self, memo: dict[int, typ.Any]) -> Configuration:
        other = Configuration()
        memo[id(self)] = other
        other.__data = copy.deepcopy(self.__data, memo=memo)
        return other

    def __copy__(self) -> Configuration:
        other = Configuration()
        other.__data = copy.copy(self.__data)
        return other

    copy = __copy__

    #################################################################
    # Internal methods
    #################################################################

    def _private_set(self, key: typ.Any, value: typ.Any, secret: object) -> None:
        if secret is setter_secret:
            self.__data[key] = value
        else:
            raise TypeError("`_private_set` is private and not for external use")

    def _raw_items(self) -> typ.Iterator[tuple[typ.Any, typ.Any]]:
        return map(lambda key: (key, self.__data[key]), self)

    #################################################################
    # Public interface methods
    #################################################################

    def exists(self, key: typ.Any) -> bool:
        """
        Checks that a key exists and is not a Placeholder
        """
        return (key in self) and not isinstance(self.__data[key], Placeholder)

    def as_dict(self) -> dict[typ.Any, typ.Any]:
        """
        Returns this `Configuration` as standard Python `dict`.
        Nested `Configuration` objects will also be converted.

        Note: This will evaluated all lazy tag functions and throw an exception
        on Placeholders.
        """
        return dict(
            starmap(
                lambda key, value: (key, value.as_dict() if isinstance(value, Configuration) else value),
                self.items(),
            )
        )

    def as_json_string(self, *, default: typ.Callable[[typ.Any], typ.Any] | None = None, **kwds: typ.Any) -> str:
        """
        Returns this `Configuration` as a JSON string, using standard `json`
        library and (as default) the default factory provided by this library
        (`granular_configuration.json_default`).

        Note: This will evaluated all lazy tag functions and throw an exception
        on Placeholders.
        """
        from granular_configuration import json_default

        return json.dumps(self, default=default or json_default, **kwds)

    @typ.overload
    def typed_get(self, type: typ.Type[_T], key: typ.Any) -> _T:
        """
        Provides a typed-checked `get` option

        - `type`: Wanted typed
        - `key`: Key for wanted value
        """
        ...

    @typ.overload
    def typed_get(self, type: typ.Type[_T], key: typ.Any, *, default: _T) -> _T:
        """
        Provides a typed-checked `get` option

        - `type`: Wanted typed
        - `key`: Key for wanted value

        Options:
        - `default`: Provides a default value like `dict.get`
        """
        ...

    @typ.overload
    def typed_get(
        self, type: typ.Type[_T], key: typ.Any, *, predicate: typ.Callable[[typ.Any], typ.TypeGuard[_T]]
    ) -> _T:
        """
        Provides a typed-checked `get` option

        - `type`: Wanted typed
        - `key`: Key for wanted value

        Options:
        - `predicate`: Replaces the `isinstance(value, type)` check with a custom method `predicate(value) -> bool`
        """
        ...

    @typ.overload
    def typed_get(
        self, type: typ.Type[_T], key: typ.Any, *, default: _T, predicate: typ.Callable[[typ.Any], typ.TypeGuard[_T]]
    ) -> _T:
        """
        Provides a typed-checked `get` option

        - `type`: Wanted typed
        - `key`: Key for wanted value

        Options:
        - `default`: Provides a default value like `dict.get`
        - `predicate`: Replaces the `isinstance(value, type)` check with a custom method `predicate(value) -> bool`

        """
        ...

    def typed_get(self, type: typ.Type[_T], key: typ.Any, **kwds: Unpack[Kwords_typed_get[_T]]) -> _T:
        """
        Provides a typed-checked `get` option

        - `type`: Wanted typed
        - `key`: Key for wanted value

        Options:
        - `default`: Provides a default value like `dict.get`
        - `predicate`: Replaces the `isinstance(value, type)` check with a custom method `predicate(value) -> bool`
        """
        try:
            value = self[key]
        except KeyError:
            if "default" in kwds:
                return kwds["default"]
            else:
                raise

        if (("predicate" in kwds) and kwds["predicate"](value)) or isinstance(value, type):
            return value
        else:
            raise ValueError(f"Incorrect type. Got: `{repr(value)}`. Wanted: `{repr(type)}`")


class MutableConfiguration(typ.MutableMapping[typ.Any, typ.Any], Configuration):
    # Remember `Configuration.__data` is really `Configuration._Configuration__data`
    # Type checkers do ignore this fact, because this is something to be avoided.
    # I want to continue to use self.__data to avoid people being tempted to reach in.

    def __delitem__(self, key: typ.Any) -> None:
        del self._Configuration__data[key]

    def __setitem__(self, key: typ.Any, value: typ.Any) -> None:
        self._Configuration__data[key] = value

    def __deepcopy__(self, memo: dict[int, typ.Any]) -> MutableConfiguration:
        other = MutableConfiguration()
        memo[id(self)] = other
        # Use setattr to avoid mypy and pylance being confused
        setattr(other, "_Configuration__data", copy.deepcopy(self._Configuration__data, memo=memo))
        return other

    def __copy__(self) -> MutableConfiguration:
        other = MutableConfiguration()
        # Use setattr to avoid mypy and pylance being confused
        setattr(other, "_Configuration__data", copy.copy(self._Configuration__data))
        return other

    copy = __copy__
