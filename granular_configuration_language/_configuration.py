from __future__ import annotations

import collections.abc as tabc
import copy
import json
import operator as op
import sys
import typing as typ
from itertools import starmap
from weakref import ReferenceType, ref

from granular_configuration_language._base_path import BasePathPart
from granular_configuration_language._s import setter_secret
from granular_configuration_language.exceptions import InvalidBasePathException, PlaceholderConfigurationError
from granular_configuration_language.yaml.classes import KT, RT, VT, LazyEval, P, Placeholder, T

if sys.version_info >= (3, 12):
    from typing import override
elif typ.TYPE_CHECKING:
    from typing_extensions import override
else:

    def override(func: typ.Callable[P, RT]) -> typ.Callable[P, RT]:
        return func


if sys.version_info >= (3, 11):
    from typing import Generic, TypedDict, Unpack, dataclass_transform

    class Kwords_typed_get(Generic[T], TypedDict, total=False):
        default: T
        predicate: tabc.Callable[[typ.Any], typ.TypeGuard[T]]

elif typ.TYPE_CHECKING:
    from typing import Generic

    from typing_extensions import TypedDict, Unpack, dataclass_transform

    class Kwords_typed_get(Generic[T], TypedDict, total=False):
        default: T
        predicate: tabc.Callable[[typ.Any], typ.TypeGuard[T]]

else:

    def dataclass_transform(**kwargs: typ.Any) -> typ.Callable[[typ.Callable[P, RT]], typ.Callable[P, RT]]:
        def identity(func: typ.Callable[P, RT]) -> typ.Callable[P, RT]:
            return func

        return identity


class AttributeName(tabc.Iterable[str]):
    __slots__ = ("__prev", "__explicit_prev", "__name", "__weakref__")

    def __init__(
        self,
        name: typ.Any,
        *,
        prev: ReferenceType[AttributeName] | None = None,
        explicit_prev: tabc.Iterable[str] = tuple(),
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

    @override
    def __iter__(self) -> tabc.Iterator[str]:
        if self.__prev:
            yield from self.__prev() or tuple()
        else:
            yield from self.__explicit_prev
        yield self.__name if isinstance(self.__name, str) else f"`{repr(self.__name)}`"

    def _plus_one(self, last: str) -> tabc.Iterator[str]:
        yield from self
        yield last if isinstance(last, str) else f"`{repr(last)}`"

    @override
    def __str__(self) -> str:
        return ".".join(self)


@dataclass_transform(frozen_default=True, eq_default=True, kw_only_default=True)
class Configuration(typ.Generic[KT, VT], tabc.Mapping[KT, VT]):
    r"""
    This class represents an immutable :py:class:`~collections.abc.Mapping` of
    configuration.

    You can create type annotated subclasses of :py:class:`Configuration` to
    enable type checking and code completion, as if your subclass was a
    :py:func:`dataclass <dataclasses.dataclass>` [#f1]_.

    With you typed class, you can cast a general :py:class:`.Configuration` to
    your subclass via :py:meth:`Configuration.as_typed`.

    .. admonition:: :py:meth:`!as_typed` Example
        :class: hint
        :collapsible: closed

        .. code-block:: python

            class SubConfig(Configuration):
                c: str


            class Config(Configuration):
                a: int
                b: SubConfig


            config = ...  # A Configuration instance
            typed = config.as_typed(Config)

            assert typed.a == 101
            assert typed.b.c == "test me"
            assert typed["a"] == 101

            # Or loading with LazyLoadConfiguration

            typed = LazyLoadConfiguration("config.yaml").as_typed(Config)

        .. admonition:: Advisement
            :class: tip

            Consider using :py:meth:`LazyLoadConfiguration.as_typed` to load your
            entire configuration as a typed :py:class:`.Configuration`.

    .. admonition:: Footnotes
        :collapsible: closed

        .. [#f1]

            See :py:func:`~typing.dataclass_transform` → "on base class" for
            implementation details

    .. admonition:: Changes
        :collapsible: closed

        .. versionchanged:: 2.3.0
            Added Generic Type Parameters, which default to :py:data:`~typing.Any`.

    :param ~collections.abc.Mapping[KT, VT] mapping:
        Constructs a :py:class:`.Configuration` by shallow copying initiating mapping.
    :param ~collections.abc.Iterable[tuple[KT, VT]] iterable:
        Constructs a :py:class:`.Configuration` from an iterable of key-value pairs.
    :param VT \*\*kwargs:
        Constructs a :py:class:`.Configuration` via keyword arguments.
        (Due to a limitation of defaults, :py:class:`.KT` is inferred to be
        :py:data:`~typing.Any`, instead of :py:class:`str`.)
    """

    @typ.overload
    def __init__(self) -> None: ...

    @typ.overload
    def __init__(self, mapping: tabc.Mapping[KT, VT], /) -> None: ...

    @typ.overload
    def __init__(self, iterable: tabc.Iterable[tuple[KT, VT]], /) -> None: ...

    @typ.overload
    def __init__(self, **kwargs: VT) -> None: ...

    def __init__(self, *arg: tabc.Mapping[KT, VT] | tabc.Iterable[tuple[KT, VT]], **kwargs: VT) -> None:
        self.__data: dict[typ.Any, typ.Any] = dict(*arg, **kwargs)
        self.__attribute_name = AttributeName.as_root()

    #################################################################
    # Required for Mapping
    #################################################################

    @override
    def __iter__(self) -> tabc.Iterator[KT]:
        return iter(self.__data)

    @override
    def __len__(self) -> int:
        return len(self.__data)

    @override
    def __getitem__(self, name: KT) -> VT:
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

        if isinstance(value, LazyEval):
            try:
                value = value.result
                self._private_set(name, value, setter_secret)
            except RecursionError as e:
                raise RecursionError(
                    f"{value.tag} at `{self.__attribute_name.with_suffix(name)}` caused a recursion error: {e}"
                ) from None

        if isinstance(value, Placeholder):
            raise PlaceholderConfigurationError(
                f'!Placeholder at `{self.__attribute_name.with_suffix(name)}` was not overwritten. Message: "{value}"'
            )

        if isinstance(value, Configuration):
            value.__attribute_name = self.__attribute_name.append_suffix(name)
            return value  # type: ignore  # instead of casting
        else:
            return value

    #################################################################
    # Overridden Mapping methods
    #################################################################

    @override
    def __contains__(self, key: typ.Any) -> bool:
        return key in self.__data

    @typ.overload
    def get(self, key: KT, /) -> VT | None: ...

    @typ.overload
    def get(self, key: KT, /, default: VT | T) -> VT | T: ...

    @override
    def get(self, key: KT, default: VT | T | None = None) -> VT | T | None:
        """
        Return the value for key if key is in the :py:class:`Configuration`, else default.

        .. versionchanged:: 2.3.0
            Added typing overload. ``key`` is typed as positional.

        :param (KT) key: Key being fetched
        :param (VT | T)  default: Default value. Defaults to :py:data:`None`.
        :return: Fetched value or default
        :rtype:  VT | T | None
        """
        return self[key] if self.exists(key) else default

    #################################################################
    # Required behavior overrides
    #################################################################

    @override
    def __repr__(self) -> str:
        return repr(self.__data)

    def __deepcopy__(self, memo: dict[int, typ.Any]) -> Configuration[KT, VT]:
        other: Configuration[KT, VT] = Configuration()
        memo[id(self)] = other
        other.__data = copy.deepcopy(self.__data, memo=memo)
        return other

    def __copy__(self) -> Configuration[KT, VT]:
        other: Configuration[KT, VT] = Configuration()
        other.__data = copy.copy(self.__data)
        return other

    copy = __copy__
    """
    Returns a shallow copy of this instance. (Matches :py:meth:`dict.copy` interface.)

    .. caution::

        :py:class:`.LazyEval` do not make copies. If you have not evaluated all tags,
        you should called :py:meth:`evaluate_all` before calling this method.

    .. tip::

        :py:class:`.Configuration` is immutable, so you do not need to make a copy to protect it.

    """

    #################################################################
    # Internal methods
    #################################################################

    def _private_set(self, key: typ.Any, value: typ.Any, secret: object) -> None:
        if secret is setter_secret:
            self.__data[key] = value
        else:
            raise TypeError("`_private_set` is private and not for external use")

    def _raw_items(self) -> tabc.Iterator[tuple[typ.Any, typ.Any]]:
        return map(lambda key: (key, self.__data[key]), self)

    #################################################################
    # Public interface methods
    #################################################################

    def __getattr__(self, name: str) -> VT:
        """
        Provides a potentially cleaner path as an alternative to :py:meth:`~object.__getitem__`.

        .. admonition:: Comparing to :py:meth:`~object.__getitem__`

            - Three less characters
            - Only accepts :py:class:`str`
            - Throws :py:exc:`AttributeError` instead of :py:exc:`KeyError`

        :example:
            .. code-block:: python

                config.a.b.c          # Using `__getattr__`
                config["a"]["b"]["c"] # Using `__getitem__`
        :param str name: Attribute name
        :return: Fetched value
        :rtype:  VT
        :raises AttributeError: When an attribute is not present.
        """
        if name not in self:
            raise AttributeError(f"Request attribute `{self.__attribute_name.with_suffix(name)}` does not exist")

        return self[name]  # type: ignore  # instead of casting

    def exists(self, key: typ.Any) -> bool:
        """
        Checks that a key exists and is not a :py:class:`~.Placeholder`

        Parameters:
            key (~typing.Any): key to be checked

        Returns:
            bool: Returns :py:data:`True` if the key exists and is not a :py:class:`~.Placeholder`
        """
        return (key in self) and not isinstance(self.__data[key], Placeholder)

    def evaluate_all(self) -> None:
        """
        Evaluates all lazy tag functions and throws an exception on :py:class:`~.Placeholder` instances
        """

        for value in self.values():
            if isinstance(value, Configuration):
                value.evaluate_all()

    def as_dict(self) -> dict[KT, VT]:
        """
        Returns this :py:class:`Configuration` as standard Python :py:class:`dict`.
        Nested :class:`Configuration` objects will also be converted.

        .. admonition:: Evaluation Notice
            :class: note
            :collapsible: closed

            This will evaluate all lazy tag functions and throw an exception on :py:class:`~.Placeholder` objects.

        :return: A shallow :py:class:`dict` copy
        :rtype: dict
        """
        evalute_item: tabc.Callable[[tuple[KT, VT]], tuple[KT, VT]]
        evalute_item = lambda key, value: (  # type: ignore   # instead of casting
            key,
            value.as_dict() if isinstance(value, Configuration) else value,
        )
        return dict(starmap(evalute_item, self.items()))

    def as_json_string(self, *, default: tabc.Callable[[typ.Any], typ.Any] | None = None, **kwds: typ.Any) -> str:
        r"""
        Returns this :py:class:`Configuration` as a JSON string, using standard :py:mod:`json`
        library and (as default) the default factory provided by this library
        (:py:func:`granular_configuration_language.json_default`).

        .. admonition:: Evaluation Notice
            :class: note
            :collapsible: closed

            This will evaluate all lazy tag functions and throw an exception on :py:class:`~.Placeholder` objects.

        :param \~typing.Callable[[\~typing.Any], \~typing.Any], optional default: Replacement ``default`` factory. Defaults to :py:func:`~granular_configuration_language.json_default`.
        :param ~typing.Any \*\*kwds: Arguments to be passed into :py:func:`json.dumps`
        :return: JSON-format string
        :rtype: str
        """
        from granular_configuration_language import json_default

        return json.dumps(self, default=default or json_default, **kwds)

    @typ.overload
    def typed_get(self, type: type[T], key: typ.Any) -> T: ...

    @typ.overload
    def typed_get(self, type: type[T], key: typ.Any, *, default: T) -> T: ...

    @typ.overload
    def typed_get(self, type: type[T], key: typ.Any, *, predicate: tabc.Callable[[typ.Any], typ.TypeGuard[T]]) -> T: ...

    @typ.overload
    def typed_get(
        self, type: type[T], key: typ.Any, *, default: T, predicate: tabc.Callable[[typ.Any], typ.TypeGuard[T]]
    ) -> T: ...

    def typed_get(self, type: type[T], key: typ.Any, **kwds: Unpack[Kwords_typed_get[T]]) -> T:
        r"""
        Provides a typed-checked :py:meth:`get` option

        Parameters:
            type (type[T]): Wanted typed
            key (~typing.Any): Key for wanted value
            default (T, optional): Provides a default value like :py:meth:`dict.get`
            predicate (\~typing.Callable[[~typing.Any], ~typing.TypeGuard[T]], optional):
                Replaces the ``isinstance(value, type)`` check with a custom
                method ``predicate(value: Any) -> bool``

        Returns:
            T: Value stored under the key

        Raises:
            TypeError: If the real type is not an instance of the expected type
        """

        try:
            value: typ.Any = self[key]
        except KeyError:
            if "default" in kwds:
                return kwds["default"]
            else:
                raise

        if (("predicate" in kwds) and kwds["predicate"](value)) or isinstance(value, type):
            return value
        else:
            raise TypeError(f"Incorrect type. Got: `{repr(value)}`. Wanted: `{repr(type)}`")

    def as_typed(self, typed_base: type[C]) -> C:
        """
        Cast this :py:class:`Configuration` instance into subclass of :py:class:`Configuration` with typed annotated attributes

        .. admonition:: Advisement
            :class: tip

            Consider using :py:meth:`LazyLoadConfiguration.as_typed` to load your
            entire configuration as a typed :py:class:`.Configuration`, instead of
            just a section with this version.

        .. admonition:: No runtime type checking
            :class: note
            :collapsible: closed

            This method uses :py:func:`typing.cast` to return this instance, unmodified,
            as the requested :py:class:`Configuration` subclass.
            This enables typing checking and typed attributes with minimal a runtime cost.
            It is limited to just improving developer experience.

            Use ``Pydantic``, or some like it, if you require runtime type checking.

        :param type[C] typed_base: Subclass of :py:class:`Configuration` to assume
        :return: This instance
        :rtype: C
        """
        return typ.cast(C, self)


_private_data_getter: tabc.Callable[[Configuration], dict[typ.Any, typ.Any]] = op.attrgetter("_Configuration__data")


class MutableConfiguration(typ.Generic[KT, VT], tabc.MutableMapping[KT, VT], Configuration[KT, VT]):
    r"""
    This class represents an :py:class:`~collections.abc.MutableMapping` of the
    configuration. Inherits from :py:class:`Configuration`

    .. tip::

        Consider using :py:class:`Configuration` in you code to reduce
        unexpected side-effects.

    :param ~collections.abc.Mapping[KT, VT] mapping:
        Constructs a :py:class:`.MutableConfiguration` by shallow copying initiating mapping.
    :param ~collections.abc.Iterable[tuple[KT, VT]] iterable:
        Constructs a :py:class:`.MutableConfiguration` from an iterable of key-value pairs.
    :param VT \*\*kwargs:
        Constructs a :py:class:`.MutableConfiguration` via keyword arguments.
        (Due to a limitation of defaults, :py:class:`.KT` is inferred to be
        :py:data:`~typing.Any`, instead of :py:class:`str`.)
    """

    if typ.TYPE_CHECKING:
        # For Pylance and sphinx.

        @typ.overload
        def __init__(self) -> None: ...

        @typ.overload
        def __init__(self, mapping: tabc.Mapping[KT, VT], /) -> None: ...

        @typ.overload
        def __init__(self, iterable: tabc.Iterable[tuple[KT, VT]], /) -> None: ...

        @typ.overload
        def __init__(self, **kwargs: VT) -> None: ...

        def __init__(self, *arg: tabc.Mapping[KT, VT] | tabc.Iterable[tuple[KT, VT]], **kwargs: VT) -> None:
            super().__init__(*arg, **kwargs)

        @typ.overload
        def typed_get(self, type: type[T], key: typ.Any) -> T: ...

        @typ.overload
        def typed_get(self, type: type[T], key: typ.Any, *, default: T) -> T: ...

        @typ.overload
        def typed_get(
            self, type: type[T], key: typ.Any, *, predicate: tabc.Callable[[typ.Any], typ.TypeGuard[T]]
        ) -> T: ...

        @typ.overload
        def typed_get(
            self, type: type[T], key: typ.Any, *, default: T, predicate: tabc.Callable[[typ.Any], typ.TypeGuard[T]]
        ) -> T: ...

        @override
        def typed_get(self, type: type[T], key: typ.Any, **kwds: Unpack[Kwords_typed_get[T]]) -> T:
            return super().typed_get(type, key, **kwds)

    # Remember `Configuration.__data` is really `Configuration._Configuration__data`
    # Type checkers do ignore this fact, because this is something to be avoided.
    # I want to continue to use self.__data to avoid people being tempted to reach in.

    @override
    def __delitem__(self, key: typ.Any) -> None:
        del _private_data_getter(self)[key]

    @override
    def __setitem__(self, key: KT, value: VT) -> None:
        _private_data_getter(self)[key] = value

    @override
    def __deepcopy__(self, memo: dict[int, typ.Any]) -> MutableConfiguration:
        other: MutableConfiguration[KT, VT] = MutableConfiguration()
        memo[id(self)] = other
        # Use setattr to avoid mypy and pylance being confused
        setattr(other, "_Configuration__data", copy.deepcopy(_private_data_getter(self), memo=memo))  # noqa: B010
        return other

    @override
    def __copy__(self) -> MutableConfiguration:
        other: MutableConfiguration[KT, VT] = MutableConfiguration()
        # Use setattr to avoid mypy and pylance being confused
        setattr(other, "_Configuration__data", copy.copy(_private_data_getter(self)))  # noqa: B010
        return other

    copy = __copy__
    """
    Returns a shallow copy of this instance. (Matches :py:meth:`dict.copy` interface.)

    .. caution::

        :py:class:`.LazyEval` do not make copies. If you have not evaluated all tags,
        you should called :py:meth:`evaluate_all` before calling this method.
    """


C = typ.TypeVar("C", bound=Configuration)
"""
Generic Type that must be :py:class:`.Configuration` or a subclass
"""
