from __future__ import annotations

import copy
import json
import sys
import typing as typ
from itertools import starmap
from weakref import ReferenceType, ref

from granular_configuration_language._s import setter_secret
from granular_configuration_language.base_path import BasePathPart
from granular_configuration_language.exceptions import InvalidBasePathException, PlaceholderConfigurationError
from granular_configuration_language.yaml import LazyEval, Placeholder

if sys.version_info >= (3, 11):
    from typing import Generic, TypedDict, Unpack
elif typ.TYPE_CHECKING:
    from typing_extensions import Generic, TypedDict, Unpack


T = typ.TypeVar("T")

if sys.version_info >= (3, 11) or typ.TYPE_CHECKING:

    class Kwords_typed_get(Generic[T], TypedDict, total=False):
        default: T
        predicate: typ.Callable[[typ.Any], typ.TypeGuard[T]]


class AttributeName(typ.Iterable[str]):
    __slots__ = ("__prev", "__explicit_prev", "__name", "__weakref__")

    def __init__(
        self,
        name: typ.Any,
        *,
        prev: ReferenceType[AttributeName] | None = None,
        explicit_prev: typ.Iterable[str] = tuple(),
    ) -> None:
        self.__prev = prev
        self.__explicit_prev = explicit_prev
        self.__name = name

    @staticmethod
    def as_root() -> AttributeName:
        return AttributeName("$", explicit_prev=tuple())

    def append_suffix(self, name: typ.Any) -> AttributeName:
        return AttributeName(name, prev=ref(self))

    def with_suffix(self, name: typ.Any) -> str:
        return ".".join(self._plus_one(name))

    def __iter__(self) -> typ.Iterator[str]:
        if self.__prev:
            yield from self.__prev() or tuple()
        else:
            yield from self.__explicit_prev
        yield self.__name if isinstance(self.__name, str) else f"`{repr(self.__name)}`"

    def _plus_one(self, last: str) -> typ.Iterator[str]:
        yield from self
        yield last if isinstance(last, str) else f"`{repr(last)}`"

    def __str__(self) -> str:
        return ".".join(self)


class Configuration(typ.Mapping[typ.Any, typ.Any]):
    """
    This class represents an immutable mapping of the configuration.
    """

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
                f'!Placeholder at `{self.__attribute_name.with_suffix(name)}` was not overwritten. Message: "{value}"'
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
        """
        Return the value for key if key is in the :class:`Configuration`, else default.

        Args:
            key (Any): Key being fetched
            default (Any, optional): Default value. Defaults to None.

        Returns:
            Any: Value
        """
        return self[key] if self.exists(key) else default

    #################################################################
    # Required behavior overrides
    #################################################################

    def __getattr__(self, name: str) -> typ.Any:
        """
        Provides potentially cleaner path as an alternative to `__getitem__`.
        Throws AttributeError instead of KeyError, as compared to `__getitem__` when an attribute is not present.

        Args:
            name (str): Attribute name

        Raises:
            AttributeError: When an attribute is not present.

        Returns:
            Any: Value
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
        Checks that a key exists and is not a :class:`Placeholder`

        Args:
            key (Any): key to be checked

        Returns:
            bool: Returns True if the key exists and is not a :class:`Placeholder`
        """
        return (key in self) and not isinstance(self.__data[key], Placeholder)

    def evaluate_all(self) -> None:
        """
        Evaluates all lazy tag functions and throws an exception on Placeholders
        """

        for value in self.values():
            if isinstance(value, Configuration):
                value.evaluate_all()

    def as_dict(self) -> dict[typ.Any, typ.Any]:
        """
        Returns this :class:`Configuration` as standard Python :class:`dict`.
        Nested :class:`Configuration` objects will also be converted.

        > Note: This will evaluated all lazy tag functions and throw an exception
        on :class:`Placeholder` objects.

        Returns:
            dict: The shallow :class:`dict` copy.
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
        (`granular_configuration_language.json_default`).

        > Note: This will evaluated all lazy tag functions and throw an exception
        on Placeholders.

        Args:
            default (Callable[[Any], Any] | None, optional): Replacement `default` factory. Defaults to None.
            **kwds (Any): Argments to be passed into `json.dumps`

        Returns:
            str: JSON-format string
        """
        from granular_configuration_language import json_default

        return json.dumps(self, default=default or json_default, **kwds)

    @typ.overload
    def typed_get(self, type: typ.Type[T], key: typ.Any) -> T:
        """
        Provides a typed-checked `get` option

        Args:
            type (Type[T]): Wanted typed
            key (Any): Key for wanted value

        Raises:
            TypeError: If the real type is not an instance of the expected type

        Returns:
            T: Value stored under the key
        """
        ...

    @typ.overload
    def typed_get(self, type: typ.Type[T], key: typ.Any, *, default: T) -> T:
        """
        Provides a typed-checked `get` option

        Args:
            type (Type[T]): Wanted typed
            key (Any): Key for wanted value
            default (T): Provides a default value like `dict.get`

        Raises:
            TypeError: If the real type is not an instance of the expected type

        Returns:
            T: Value stored under the key
        """
        ...

    @typ.overload
    def typed_get(self, type: typ.Type[T], key: typ.Any, *, predicate: typ.Callable[[typ.Any], typ.TypeGuard[T]]) -> T:
        """
        Provides a typed-checked `get` option

        Args:
            type (Type[T]): Wanted typed
            key (Any): Key for wanted value
            predicate (Callable[[Any], TypeGuard[T]]):  Replaces the `isinstance(value, type)` check with a custom method `predicate(value) -> bool`

        Raises:
            TypeError: If the real type is not an instance of the expected type

        Returns:
            T: Value stored under the key
        """
        ...

    @typ.overload
    def typed_get(
        self, type: typ.Type[T], key: typ.Any, *, default: T, predicate: typ.Callable[[typ.Any], typ.TypeGuard[T]]
    ) -> T:
        """
        Provides a typed-checked `get` option

        Args:
            type (Type[T]): Wanted typed
            key (Any): Key for wanted value
            default (T): Provides a default value like `dict.get`
            predicate (Callable[[Any], TypeGuard[T]]):  Replaces the `isinstance(value, type)` check with a custom method `predicate(value) -> bool`

        Raises:
            TypeError: If the real type is not an instance of the expected type

        Returns:
            T: Value stored under the key
        """
        ...

    def typed_get(self, type: typ.Type[T], key: typ.Any, **kwds: Unpack[Kwords_typed_get[T]]) -> T:
        """
        Provides a typed-checked `get` option

        Args:
            type (Type[T]): Wanted typed
            key (Any): Key for wanted value
            default (T, optional): Provides a default value like `dict.get`
            predicate (Callable[[Any], TypeGuard[T]], optional):  Replaces the `isinstance(value, type)` check with a custom method `predicate(value) -> bool`

        Raises:
            TypeError: If the real type is not an instance of the expected type

        Returns:
            T: Value stored under the key
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
            raise TypeError(f"Incorrect type. Got: `{repr(value)}`. Wanted: `{repr(type)}`")


class MutableConfiguration(typ.MutableMapping[typ.Any, typ.Any], Configuration):
    """
    This class represents an mutable mapping of the configuration. Inherits from `Configuration`
    """

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
