from __future__ import annotations

import collections.abc as tabc
import copy
import os
import sys
import typing as typ
from collections.abc import Mapping, MutableMapping
from functools import cached_property
from itertools import chain

from granular_configuration_language._cache import NoteOfIntentToRead, prepare_to_load_configuration
from granular_configuration_language._configuration import C, Configuration, MutableConfiguration
from granular_configuration_language._locations import Locations, PathOrStr
from granular_configuration_language._simple_future import SimpleFuture
from granular_configuration_language.exceptions import ErrorWhileLoadingConfig

if sys.version_info >= (3, 12):
    from typing import override
elif typ.TYPE_CHECKING:
    from typing_extensions import override
else:

    def override(func: tabc.Callable) -> tabc.Callable:
        return func


def _read_locations(
    load_order_location: tabc.Iterable[PathOrStr],
    use_env_location: bool,
    env_location_var_name: str,
) -> Locations:
    if (use_env_location or (env_location_var_name != "G_CONFIG_LOCATION")) and (env_location_var_name in os.environ):
        env_locs = os.environ[env_location_var_name].split(",")
        load_order_location = chain(load_order_location, env_locs)
    return Locations(load_order_location)


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

    def __init__(self, llc: LazyLoadConfiguration) -> None:
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


def _eagerio_load(llc: LazyLoadConfiguration) -> Configuration:
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

    def __init__(self, llc: LazyLoadConfiguration) -> None:
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


class LazyLoadConfiguration(Mapping):
    r"""
    The entry point for defining an immutable Configuration from file paths that lazily loads on first access.

    **Options:**
        -  Using ``env_location_var_name``, you can enable pulling locations from an environment variable.
        -  See :py:meth:`LazyLoadConfiguration.as_typed` for type annotated usage.
        -  ``inject_before`` and ``inject_after`` allow you to inject Python-created settings into you configuration without use a file.

    .. admonition:: :py:meth:`!as_typed` Example
        :class: hint
        :collapsible: closed

        .. code-block:: python

            class SubConfig(Configuration):
                c: str


            class Config(Configuration):
                a: int
                b: SubConfig


            typed = LazyLoadConfiguration("config.yaml").as_typed(Config)

            assert typed.a == 101
            assert typed.b.c == "test me"
            assert typed["a"] == 101

    .. admonition:: Injection Rules and Example
        :class: hint
        :collapsible: closed

          - Injections must use :py:class:`.Configuration` for all mappings.

            - Otherwise, they will be treated as a normal value and not merged.
          - Injection occurs before ``base_path`` is applied.

            - I.e. You must include the ``base_path`` in the injected :py:class:`.Configuration`.
          - Using injections disables "identical immutable configurations" caching.
          - This is only available for :py:class:`.LazyLoadConfiguration`

            - As :py:class:`.MutableLazyLoadConfiguration` doesn't required this.
          - Examples:

            - You might want to have a setting the is the current date.
            - You want to provide substitution options via ``!Sub``.

        .. code-block:: yaml

            # "config.yaml"
            app:
                data:
                    key1: !Sub ${$.LOOKUP_KEY}
                    key2: !Sub ${$.LOOKUP_KEY}

        .. code-block:: python

            CONFIG = LazyLoadConfiguration(
                "config.yaml",
                base_path="app",
                inject_after=Configuration(
                    app=Configuration(
                        today=date.today().isoformat(),
                    ),
                    LOOKUP_KEY="value made available to `!Sub`",
                ),
            )

            CONFIG.today  # Today's date as a constant string.
            CONFIG.data.as_dict()  # Data defined with a reusable library defined value.

        .. admonition:: Attention
            :class: error

            - :py:class:`dict` does not act as :py:class:`.Configuration`.
            - :py:class:`dict` instances are values that do not merge.

    :param ~pathlib.Path | str | os.PathLike \*load_order_location:
            File path to configuration file
    :param str | ~collections.abc.Sequence[str], optional base_path:
        Defines the subsection of the configuration file to use. See Examples for usage options.
    :param bool, optional use_env_location:
        - Enabled to use the default environment variable location.
        - Setting to :py:data:`True` is only required if you don't change
          ``env_location_var_name`` from its default value.
    :param str, optional env_location_var_name:
        - Specify what environment variable to check for additional file paths.
        - The Environment Variable is read as a comma-delimited list of
          configuration path that will be appended to ``load_order_location`` list.
        - Setting the Environment Variable is always optional.
        - *Default*: ``G_CONFIG_LOCATION``

          - Setting ``use_env_location=True`` is required to use the default value.
    :param Configuration, optional inject_before:
        Inject a runtime :py:class:`.Configuration` instance, as if it were the first loaded file.
    :param Configuration, optional inject_after:
        Inject a runtime :py:class:`.Configuration` instance, as if it were the last loaded file.
    :param bool, optional disable_caching:
        When :py:data:`True`, this instance will not participate in the caching of "identical immutable configurations".
    :param ~typing.Any \*\*kwargs: There are no public-facing supported extra parameters.

    :examples:
        .. code-block:: python

            # Base Path - Single Key
            LazyLoadConfiguration(..., base_path="base_path")
            # Base Path - JSON Pointer (strings only)
            LazyLoadConfiguration(..., base_path="/base/path")
            # Base Path - List of keys
            LazyLoadConfiguration(..., base_path=("base", "path"))

            # Use Environment Variable: "CONFIG_LOC"
            LazyLoadConfiguration(..., env_location_var_name="CONFIG_LOC")

            # Use default Environment Variable: "G_CONFIG_LOCATION"
            LazyLoadConfiguration(..., use_env_location=True)

            # With a typed `Configuration`
            LazyLoadConfiguration(...).as_typed(TypedConfig)
    """

    def __init__(
        self,
        *load_order_location: PathOrStr,
        base_path: str | tabc.Sequence[str] | None = None,
        use_env_location: bool = False,
        env_location_var_name: str = "G_CONFIG_LOCATION",
        inject_before: Configuration | None = None,
        inject_after: Configuration | None = None,
        disable_caching: bool = False,
        **kwargs: typ.Any,
    ) -> None:
        self.__receipt: NoteOfIntentToRead | None = prepare_to_load_configuration(
            locations=_read_locations(load_order_location, use_env_location, env_location_var_name),
            base_path=base_path,
            mutable_configuration=kwargs.get("_mutable_configuration", False),
            inject_before=inject_before,
            inject_after=inject_after,
            disable_cache=disable_caching,
        )

    def __getattr__(self, name: str) -> typ.Any:
        """Loads (if not loaded) and fetches from the underlying `Configuration` object

        *This also exposes the methods of* :py:class:`Configuration` *(except dunders).*

        :param str name: Attribute name

        :returns: Result
        :rtype: ~typing.Any
        """
        return getattr(self.config, name)

    @property
    def config(self) -> Configuration:
        """Load and fetch the configuration. Configuration is cached for subsequent calls.

        .. admonition:: Thread-safe
            :class: tip
            :collapsible: closed

            Loading the configuration is thread-safe and locks while the
            configuration is loaded to prevent duplicative processing and data

        """
        config = self.__config
        self.__receipt = None  # self.__config is cached
        return config

    @cached_property
    def __config(self) -> Configuration:
        if self.__receipt:
            return self.__receipt.config
        else:
            raise ErrorWhileLoadingConfig(
                "Config reference was lost before `cached_property` cached it."
            )  # pragma: no cover

    def load_configuration(self) -> None:
        """Loads the configuration."""
        # load_configuration existed prior to config, being a cached_property.
        # Now that logic is in the cached_property, so this legacy/clear code just calls the property
        self.config  # noqa: B018

    @override
    def __getitem__(self, key: typ.Any) -> typ.Any:
        return self.config[key]

    @override
    def __iter__(self) -> tabc.Iterator[typ.Any]:
        return iter(self.config)

    @override
    def __len__(self) -> int:
        return len(self.config)

    def as_typed(self, typed_base: type[C]) -> C:
        """
        Create a proxy that is cast to provide :py:class:`Configuration`
        subclass with typed annotated attributes.

        This proxy ensures laziness is preserved and is fully compatible with
        :py:class:`Configuration`.

        .. admonition:: Example
            :class: hint
            :collapsible: closed

            .. code-block:: python

                class SubConfig(Configuration):
                    c: str


                class Config(Configuration):
                    a: int
                    b: SubConfig


                typed = LazyLoadConfiguration("config.yaml").as_typed(Config)

                assert typed.a == 101
                assert typed.b.c == "test me"
                assert typed["a"] == 101

        .. admonition:: No runtime type checking
            :class: note
            :collapsible: closed

            This method uses :py:func:`typing.cast` to return a
            :py:class:`.SafeConfigurationProxy` of this instance
            as the requested :py:class:`Configuration` subclass.

            This enables typing checking and typed attributes with minimal
            runtime cost, but it is limited to just improving developer
            experience.

            Use ``Pydantic``, or some like it, if you require runtime type
            checking.

        :param type[C] typed_base:
            Subclass of :py:class:`Configuration` to assume
        :return:
            :py:class:`.SafeConfigurationProxy` instance that has been cast to
            the provided type.
        :rtype: C
        """
        return typ.cast(C, SafeConfigurationProxy(self))

    def eager_load(self, typed_base: type[C]) -> C:
        """
        .. versionadded:: 2.3.0

        This will eagerly load this instance, so that there is minimum IO load
        on future.

        This is intended to play well with :py:mod:`asyncio`, by avoiding
        blocking the main thread/event loop on IO calls, without introducing an ``await``
        paradigm just for a few one-time calls.

        .. admonition:: Part of the EagerIO feature set
            :class: caution

            Using :py:meth:`eager_load` causes immediate loading of this
            instance in a background thread, so that future calls are
            non-/minimally blocking.

        Behaves like :py:meth:`.as_typed` otherwise.

        :param type[C] typed_base:
            Subclass of :py:class:`Configuration` to assume
        :return:
            :py:class:`.EagerIOConfigurationProxy` instance that has been cast
            to the provided type.
        :rtype: C
        """
        return typ.cast(C, EagerIOConfigurationProxy(self))


class MutableLazyLoadConfiguration(LazyLoadConfiguration, MutableMapping):
    r"""
    Used to define a **mutable** Configuration from file paths
    that lazily loads on first access.

    **Options:**
        -  Using ``env_location_var_name``, you can enable pulling locations
           from an environment variable.

    .. tip::

        Consider using an immutable configuration with
        :py:class:`.LazyLoadConfiguration` in you code to reduce unexpected
        side-effects.

    .. admonition:: Classes used for mutability
        :class: note
        :collapsible: closed

        - :py:class:`.MutableConfiguration` for mappings
        - :py:class:`list` for sequences

    :param ~pathlib.Path | str | os.PathLike \*load_order_location:
            File path to configuration file
    :param str | ~collections.abc.Sequence[str], optional base_path:
        Defines the subsection of the configuration file to use.
        See Examples for usage options.
    :param bool, optional use_env_location:
        - Enabled to use the default environment variable location.
        - Setting to :py:data:`True` is only required if you don't change
          ``env_location_var_name`` from its default value.
    :param str, optional env_location_var_name:
        - Specify what environment variable to check for additional file paths.
        - The Environment Variable is read as a comma-delimited list of
          configuration path that will be appended to ``load_order_location``
          list.
        - Setting the Environment Variable is always optional.
        - *Default*: ``G_CONFIG_LOCATION``

          - Setting ``use_env_location=True`` is required to use the default
            value.

    :examples:
        .. code-block:: python

            # Base Path - Single Key
            MutableLazyLoadConfiguration(..., base_path="base_path")
            # Base Path - JSON Pointer (strings only)
            MutableLazyLoadConfiguration(..., base_path="/base/path")
            # Base Path - List of keys
            MutableLazyLoadConfiguration(..., base_path=("base", "path"))

            # Use Environment Variable: "CONFIG_LOC"
            MutableLazyLoadConfiguration(..., env_location_var_name="CONFIG_LOC")

            # Use default Environment Variable: "G_CONFIG_LOCATION"
            MutableLazyLoadConfiguration(..., use_env_location=True)
    """

    def __init__(
        self,
        *load_order_location: PathOrStr,
        base_path: str | tabc.Sequence[str] | None = None,
        use_env_location: bool = False,
        env_location_var_name: str = "G_CONFIG_LOCATION",
    ) -> None:
        super().__init__(
            *load_order_location,
            base_path=base_path,
            use_env_location=use_env_location,
            env_location_var_name=env_location_var_name,
            inject_before=None,
            inject_after=None,
            disable_caching=True,
            _mutable_configuration=True,
        )

    @property
    @override
    def config(self) -> MutableConfiguration:
        """
        Load and fetch the configuration. Configuration is cached for
        subsequent calls.

        .. admonition:: Thread-safe
            :class: tip
            :collapsible: closed

            Loading the configuration is thread-safe and locks while the
            configuration is loaded to prevent duplicative processing and data

        """
        return typ.cast(MutableConfiguration, super().config)

    @override
    def __delitem__(self, key: typ.Any) -> None:
        del self.config[key]

    @override
    def __setitem__(self, key: typ.Any, value: typ.Any) -> None:
        self.config[key] = value

    @override
    def as_typed(self, typed_base: type[C]) -> typ.NoReturn:
        """
        Not supported for :py:class:`MutableLazyLoadConfiguration`.
        Use :py:class:`LazyLoadConfiguration`.
        """
        raise NotImplementedError(
            "`as_typed` is not supported for `MutableLazyLoadConfiguration`. Use `LazyLoadConfiguration`."
        )

    @override
    def eager_load(self, typed_base: type[C]) -> typ.NoReturn:
        """
        Not supported for :py:class:`MutableLazyLoadConfiguration`.
        Use :py:class:`LazyLoadConfiguration`.
        """
        raise NotImplementedError(
            "`eager_load` is not supported for `MutableLazyLoadConfiguration`. Use `LazyLoadConfiguration`."
        )
