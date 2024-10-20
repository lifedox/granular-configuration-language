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
    if use_env_location and (env_location_var_name in os.environ):
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
        mutable_configuration: bool = False,
        disable_caching: bool = False,
    ) -> None:
        """
        parameters:
        - `*load_order_location`: file path to configuration file
        - `base_path`: defines the subsection of the configuration file to use
            - Can be defined as:
            - A single key: `base_path="base_path"`
            - JSON Pointer (strings only): `base_path="/base/path"`
            - A list of keys: `base_path=("base", "path")`
        - `use_env_location`: When enabled, if environment variable named by `env_location_var_name`
            exists, it will be read a comma-delimited list of configuration path that will be appended
            to `load_order_location` list.
        - `env_location_var_name`: Used when `use_env_location` is True.
        - `mutable_configuration`:
            - When `False`: `Configuration` is used for mappings. `tuple` is used for sequences.
            - When `True`: `MutableConfiguration` is used for mappings. `list` is used for sequences.
        - `disable_caching`: When `True` (or `mutable_configuration=True`), caching of
            "identical immutable configurations" is disabled.
        """
        self.__receipt: NoteOfIntentToRead | None = prepare_to_load_configuration(
            locations=_read_locations(load_order_location, use_env_location, env_location_var_name),
            base_path=base_path,
            mutable_configuration=mutable_configuration,
            disable_cache=disable_caching,
        )

    def __getattr__(self, name: str) -> typ.Any:
        """
        Loads (if not loaded) and fetches from the underlying Configuration object.
        This also exposes the methods of Configuration (except dunders).
        """
        return getattr(self.config, name)

    @property
    def config(self) -> Configuration:
        """
        Load and fetch the configuration

        This call is thread-safe and locks while the configuration is loaded to prevent duplicative processing and data
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

    Uses: `MutableConfiguration` for mappings and `list` for sequences.
    """

    def __init__(
        self,
        *load_order_location: PathOrStr,
        base_path: str | typ.Sequence[str] | None = None,
        use_env_location: bool = False,
        env_location_var_name: str = "G_CONFIG_LOCATION",
    ) -> None:
        """
        parameters:
        - `*load_order_location`: file path to configuration file
        - `base_path`: defines the subsection of the configuration file to use
            - Can be defined as:
            - A single key: `base_path="base_path"`
            - JSON Pointer (strings only): `base_path="/base/path"`
            - A list of keys: `base_path=("base", "path")`
        - `use_env_location`: When enabled, if environment variable named by `env_location_var_name`
            exists, it will be read a comma-delimited list of configuration path that will be appended
            to `load_order_location` list.
        - `env_location_var_name`: Used when `use_env_location` is True.
        """
        super().__init__(
            *load_order_location,
            base_path=base_path,
            use_env_location=use_env_location,
            env_location_var_name=env_location_var_name,
            disable_caching=True,
            mutable_configuration=True,
        )

    @property
    def config(self) -> MutableConfiguration:
        return typ.cast(MutableConfiguration, super().config)

    def __delitem__(self, key: typ.Any) -> None:
        del self.config[key]

    def __setitem__(self, key: typ.Any, value: typ.Any) -> None:
        self.config[key] = value
