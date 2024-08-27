import os
import typing as typ
from collections.abc import Mapping, MutableMapping
from functools import cached_property
from itertools import chain

from granular_configuration._cache import NoteOfIntentToRead, prepare_to_load_configuration
from granular_configuration._config import Configuration, MutableConfiguration
from granular_configuration._locations import Locations, PathOrStr
from granular_configuration.exceptions import ErrorWhileLoadingConfig


def _read_locations(load_order_location: typ.Iterable[PathOrStr], use_env_location: bool) -> Locations:
    if use_env_location and ("G_CONFIG_LOCATION" in os.environ):
        env_locs = os.environ["G_CONFIG_LOCATION"].split(",")
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
        mutable_configuration: bool = False,
        disable_caching: bool = False,
    ) -> None:
        self.__shared_config_recipt: NoteOfIntentToRead | None = prepare_to_load_configuration(
            locations=_read_locations(load_order_location, use_env_location),
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
        # Note: This is to hide the setter behavior cached_property
        return self.__config

    @cached_property
    def __config(self) -> Configuration:
        if self.__shared_config_recipt:
            config = self.__shared_config_recipt.config
            self.__shared_config_recipt = None
            return config
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
    def __init__(
        self,
        *load_order_location: PathOrStr,
        base_path: str | typ.Sequence[str] | None = None,
        use_env_location: bool = False,
        disable_caching: bool = True,
    ) -> None:
        super().__init__(
            *load_order_location,
            base_path=base_path,
            use_env_location=use_env_location,
            disable_caching=disable_caching,
            mutable_configuration=True,
        )

    @property
    def config(self) -> MutableConfiguration:
        return typ.cast(MutableConfiguration, super().config)

    def __delitem__(self, key: typ.Any) -> None:
        del self.config[key]

    def __setitem__(self, key: typ.Any, value: typ.Any) -> None:
        self.config[key] = value
