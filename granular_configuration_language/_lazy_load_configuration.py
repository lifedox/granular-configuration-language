from __future__ import annotations

import os
import typing as typ
from collections.abc import Mapping, MutableMapping
from functools import cached_property
from itertools import chain

from granular_configuration_language._cache import NoteOfIntentToRead, prepare_to_load_configuration
from granular_configuration_language._configuration import Configuration, MutableConfiguration
from granular_configuration_language._locations import Locations, PathOrStr
from granular_configuration_language.exceptions import ErrorWhileLoadingConfig


def _read_locations(
    load_order_location: typ.Iterable[PathOrStr],
    use_env_location: bool,
    env_location_var_name: str,
) -> Locations:
    if (use_env_location or (env_location_var_name != "G_CONFIG_LOCATION")) and (env_location_var_name in os.environ):
        env_locs = os.environ[env_location_var_name].split(",")
        load_order_location = chain(load_order_location, env_locs)
    return Locations(load_order_location)


class LazyLoadConfiguration(Mapping):
    """
    Provides a lazy interface for loading Configuration from file paths on first access.
    """

    def __init__(
        self,
        *load_order_location: PathOrStr,
        base_path: str | typ.Sequence[str] | None = None,
        use_env_location: bool = False,
        env_location_var_name: str = "G_CONFIG_LOCATION",
        disable_caching: bool = False,
        **kwargs: typ.Any,
    ) -> None:
        """
        :param load_order_location: File path to configuration file
        :type load_order_location: ~pathlib.Path | str | os.PathLike
        :param base_path:
            Defines the subsection of the configuration file to use.
            Can be provided as a single key, JSON Pointer of strings, or
            list of keys. See Examples.
        :type base_path: str | ~collections.abc.Sequence[str] | None, optional
        :param use_env_location:
            When enabled, if environment variable named by :code:`env_location_var_name`
            exists, it will be read a comma-delimited list of configuration path
            that will be appended to :code:`load_order_location` list.
        :type use_env_location: bool, optional
        :param env_location_var_name:
            Defaults to :code:`"G_CONFIG_LOCATION"`.
            Used when :code:`use_env_location` is :code:`True`.

            > Changing from the default value will set :code:`use_env_location` to :code:`True`.
        :type env_location_var_name: str, optional
        :param disable_caching: When `True`, caching of "identical immutable configurations" is disabled.
        :type disable_caching: bool, optional
        :examples:
            .. code:: python

                # Base Path Examples
                LazyLoadConfiguration(..., base_path="base_path")  # Single Key
                LazyLoadConfiguration(..., base_path="/base/path")  # JSON Pointer (strings only)
                LazyLoadConfiguration(..., base_path=("base", "path"))  # List of keys
        """

        self.__receipt: NoteOfIntentToRead | None = prepare_to_load_configuration(
            locations=_read_locations(load_order_location, use_env_location, env_location_var_name),
            base_path=base_path,
            mutable_configuration=kwargs.get("_mutable_configuration", False),
            disable_cache=disable_caching,
        )

    def __getattr__(self, name: str) -> typ.Any:
        """
        Loads (if not loaded) and fetches from the underlying `Configuration` object

        :note: This also exposes the methods of :py:class:`Configuration` (except dunders).
        :param name: Attribute name
        :type name: str
        :return: Result
        :rtype: ~typing.Any
        """
        return getattr(self.config, name)

    @property
    def config(self) -> Configuration:
        """
        Load and fetch the configuration.
        Configuration is cached for subsequent calls.

        :return: Defined configuration
        :rtype: Configuration
        :note:
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
        """
        Force load the configuration.
        """
        # load_configuration existed prior to config, being a cached_property.
        # Now that logic is in the cached_property, so this legacy/clear code just calls the property
        self.config

    def __getitem__(self, key: typ.Any) -> typ.Any:
        return self.config[key]

    def __iter__(self) -> typ.Iterator[typ.Any]:
        return iter(self.config)

    def __len__(self) -> int:
        return len(self.config)


class MutableLazyLoadConfiguration(LazyLoadConfiguration, MutableMapping):
    """
    Provides a lazy interface for loading Configuration from file paths on first access.

    Uses: ::py:class:`.MutableConfiguration` for mappings and :py:class:`list` for sequences.
    """

    def __init__(
        self,
        *load_order_location: PathOrStr,
        base_path: str | typ.Sequence[str] | None = None,
        use_env_location: bool = False,
        env_location_var_name: str = "G_CONFIG_LOCATION",
    ) -> None:
        """
        :param load_order_location: File path to configuration file
        :type load_order_location: ~pathlib.Path | str | os.PathLike
        :param base_path:
            Defines the subsection of the configuration file to use.
            Can be provided as a single key, JSON Pointer of strings, or
            list of keys. See Examples.
        :type base_path: str | ~collections.abc.Sequence[str] | None, optional
        :param use_env_location:
            When enabled, if environment variable named by :code:`env_location_var_name`
            exists, it will be read a comma-delimited list of configuration path
            that will be appended to :code:`load_order_location` list.
        :type use_env_location: bool, optional
        :param env_location_var_name:
            Defaults to :code:`"G_CONFIG_LOCATION"`.
            Used when :code:`use_env_location` is :code:`True`.

            > Changing from the default value will set :code:`use_env_location` to :code:`True`.
        :type env_location_var_name: str, optional
        :examples:
            .. code:: python

                # Base Path Examples
                MutableLazyLoadConfiguration(..., base_path="base_path")  # Single Key
                MutableLazyLoadConfiguration(..., base_path="/base/path")  # JSON Pointer (strings only)
                MutableLazyLoadConfiguration(..., base_path=("base", "path"))  # List of keys
        """
        super().__init__(
            *load_order_location,
            base_path=base_path,
            use_env_location=use_env_location,
            env_location_var_name=env_location_var_name,
            disable_caching=True,
            _mutable_configuration=True,
        )

    @property
    def config(self) -> MutableConfiguration:
        """
        Load and fetch the configuration. Configuration is cached for subsequent calls.

        :return: Defined configuration
        :rtype: MutableConfiguration
        :note: Loading the configuration is thread-safe and locks while the configuration is loaded to prevent duplicative processing and data
        """
        return typ.cast(MutableConfiguration, super().config)

    def __delitem__(self, key: typ.Any) -> None:
        del self.config[key]

    def __setitem__(self, key: typ.Any, value: typ.Any) -> None:
        self.config[key] = value
