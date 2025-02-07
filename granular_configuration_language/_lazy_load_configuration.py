from __future__ import annotations

import collections.abc as tabc
import copy
import os
import typing as typ
from collections.abc import Mapping, MutableMapping
from functools import cached_property
from itertools import chain

from granular_configuration_language._cache import NoteOfIntentToRead, prepare_to_load_configuration
from granular_configuration_language._configuration import C, Configuration, MutableConfiguration
from granular_configuration_language._locations import Locations, PathOrStr
from granular_configuration_language.exceptions import ErrorWhileLoadingConfig


def _read_locations(
    load_order_location: tabc.Iterable[PathOrStr],
    use_env_location: bool,
    env_location_var_name: str,
) -> Locations:
    if (use_env_location or (env_location_var_name != "G_CONFIG_LOCATION")) and (env_location_var_name in os.environ):
        env_locs = os.environ[env_location_var_name].split(",")
        load_order_location = chain(load_order_location, env_locs)
    return Locations(load_order_location)


class SafeConfigurationProxy(Mapping):
    """
    Wraps a :py:class:`.LazyLoadConfiguration` instance to proxy all method and
    attribute calls to its :py:class:`.Configuration` instance.

    :param LazyLoadConfiguration llc:
        :py:class:`.LazyLoadConfiguration` instance to be wrapped
    :note:
        Wrapping :py:class:`.LazyLoadConfiguration` maintains all laziness build
        into :py:class:`.LazyLoadConfiguration`.
    """

    __slots__ = ("__llc",)

    def __init__(self, llc: LazyLoadConfiguration) -> None:
        self.__llc = llc

    def __getattr__(self, name: str) -> typ.Any:
        return getattr(self.__llc.config, name)

    def __getitem__(self, key: typ.Any) -> typ.Any:
        return self.__llc.config[key]

    def __iter__(self) -> tabc.Iterator[typ.Any]:
        return iter(self.__llc.config)

    def __len__(self) -> int:
        return len(self.__llc.config)

    def __contains__(self, key: typ.Any) -> bool:
        return key in self.__llc.config

    def __deepcopy__(self, memo: dict[int, typ.Any]) -> Configuration:
        return copy.deepcopy(self.__llc.config, memo=memo)

    def __copy__(self) -> Configuration:
        return copy.copy(self.__llc.config)

    copy = __copy__

    def __repr__(self) -> str:
        return repr(self.__llc.config)


class LazyLoadConfiguration(Mapping):
    r"""
    Provides a lazy interface for loading Configuration from file paths on first access.

    You can optionally enable pull locations from an environment variable.

    See :py:meth:`LazyLoadConfiguration.as_typed` for type annotated usage.

    :param ~pathlib.Path | str | os.PathLike load_order_location:
            File path to configuration file
    :param str | ~collections.abc.Sequence[str], optional base_path:
        Defines the subsection of the configuration file to use. See Examples for usage options.
    :param bool, optional use_env_location:
        Enabled to use the default environment variable location.
    :param str, optional env_location_var_name:
        Specify what environment variable to check for additional file paths.
    :param Configuration, optional inject_before:
        Inject a runtime :py:class:`.Configuration` instance as if it were the first load file.
    :param Configuration, optional inject_after:
        Inject a runtime :py:class:`.Configuration` instance as if it were the last load file.
    :param bool, optional disable_caching:
        When :py:data:`True`, caching of "identical immutable configurations" is disabled.

    :examples:
        .. code-block:: python

            # Base Path Examples
            LazyLoadConfiguration(..., base_path="base_path")  # Single Key
            LazyLoadConfiguration(..., base_path="/base/path")  # JSON Pointer (strings only)
            LazyLoadConfiguration(..., base_path=("base", "path"))  # List of keys

            # Use Environment Variable: "CONFIG_LOC"
            LazyLoadConfiguration(..., env_location_var_name="CONFIG_LOC")

            # Use default Environment Variable: "G_CONFIG_LOCATION"
            LazyLoadConfiguration(..., use_env_location=True)

            # With a typed `Configuration`
            LazyLoadConfiguration( ... ).as_typed(TypedConfig)

    :note:
        - The Environment Variable is read as a comma-delimited list of configuration path that will be appended to ``load_order_location`` list.
        - Setting the Environment Variable is always optional.
        - Setting ``use_env_location`` to :py:data:`True` is only required if you don't change ``env_location_var_name`` from its default value of ``G_CONFIG_LOCATION``.
        - ``inject_before`` and ``inject_after`` allow you to introduce dynamic settings into you configuration.

          - These injections must use :py:class:`.Configuration` for all mappings. Otherwise, they will be treated as a normal value and not merged.
          - This is only available for :py:class:`.LazyLoadConfiguration`, as :py:class:`.MutableLazyLoadConfiguration` doesn't required this.
          - Examples:

            - You might want to have a setting the is the current date. ``CONFIG.today``
            - You want to provide substitution options via ``!Sub``.  ``!Sub ${$.VALUE_DYNAMICALLY_SET_BY_LIBRARY}``
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

        :param str name: Attribute name

        :returns: Result
        :rtype: ~typing.Any

        :note: This also exposes the methods of :py:class:`Configuration` (except dunders).

        """
        return getattr(self.config, name)

    @property
    def config(self) -> Configuration:
        """Load and fetch the configuration. Configuration is cached for subsequent calls.

        :note: Loading the configuration is thread-safe and locks while the configuration is loaded to prevent
            duplicative processing and data

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
        """Force load the configuration."""
        # load_configuration existed prior to config, being a cached_property.
        # Now that logic is in the cached_property, so this legacy/clear code just calls the property
        self.config

    def __getitem__(self, key: typ.Any) -> typ.Any:
        return self.config[key]

    def __iter__(self) -> tabc.Iterator[typ.Any]:
        return iter(self.config)

    def __len__(self) -> int:
        return len(self.config)

    def as_typed(self, typed_base: typ.Type[C]) -> C:
        """
        Create a proxy that is cast to provide :py:class:`Configuration` subclass with typed annotated attribute.

        This proxy ensures laziness is preserved and is fully compatible with :py:class:`Configuration`.

        .. admonition:: Use as
            :class: hint

            .. code-block:: python

                    CONFIG = LazyLoadConfiguration("config.yaml").as_typed(Config)


        :param ~typing.Type[C] typed_base: Subclass of :py:class:`Configuration` to assume
        :return: :py:class:`.SafeConfigurationProxy` instance that has been cast to the provided type.
        :rtype: C
        :note: No runtime typing check occurs.
        """
        return typ.cast(C, SafeConfigurationProxy(self))


class MutableLazyLoadConfiguration(LazyLoadConfiguration, MutableMapping):
    r"""
    Provides a lazy interface for loading Configuration from file paths on first access.

    :py:class:`.MutableLazyLoadConfiguration` uses: :py:class:`.MutableConfiguration` for mappings and :py:class:`list` for sequences.

    You can optionally enable pull locations from an environment variable.

    :param ~pathlib.Path | str | os.PathLike load_order_location:
            File path to configuration file
    :param str | ~collections.abc.Sequence[str], optional base_path:
        Defines the subsection of the configuration file to use. See Examples for usage options.
    :param bool, optional use_env_location:
        Enabled to use the default environment variable location. (O)
    :param str, optional env_location_var_name:
        Specify what environment variable to check for additional file paths.

    :examples:
        .. code-block:: python

            # Base Path Examples
            MutableLazyLoadConfiguration(..., base_path="base_path")  # Single Key
            MutableLazyLoadConfiguration(..., base_path="/base/path")  # JSON Pointer (strings only)
            MutableLazyLoadConfiguration(..., base_path=("base", "path"))  # List of keys

            # Use Environment Variable: "CONFIG_LOC"
            MutableLazyLoadConfiguration(..., env_location_var_name="CONFIG_LOC")

            # Use default Environment Variable: "G_CONFIG_LOCATION"
            MutableLazyLoadConfiguration(..., use_env_location=True)

    :note:
        - The Environment Variable is read as a comma-delimited list of configuration path that will be appended to ``load_order_location`` list.
        - Setting the Environment Variable is always optional.
        - Setting ``use_env_location`` to :py:data:`True` is only required if you don't change ``env_location_var_name`` from its default value of ``G_CONFIG_LOCATION``.
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
    def config(self) -> MutableConfiguration:
        """Load and fetch the configuration. Configuration is cached for subsequent calls.

        :note: Loading the configuration is thread-safe and locks while the configuration is loaded to prevent
            duplicative processing and data

        """
        return typ.cast(MutableConfiguration, super().config)

    def __delitem__(self, key: typ.Any) -> None:
        del self.config[key]

    def __setitem__(self, key: typ.Any, value: typ.Any) -> None:
        self.config[key] = value

    def as_typed(self, typed_base: type[C]) -> typ.NoReturn:
        """
        :py:meth:`as_typed` is not supported for :py:class:`MutableLazyLoadConfiguration`.
        Use :py:class:`LazyLoadConfiguration`.
        """
        raise NotImplementedError(
            "`as_typed` is not supported for `MutableLazyLoadConfiguration`. Use `LazyLoadConfiguration`."
        )
