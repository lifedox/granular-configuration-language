import operator as op
import os
import typing as typ
from collections.abc import MutableMapping
from functools import cached_property, reduce
from itertools import chain
from threading import Lock

from granular_configuration._build import build_configuration
from granular_configuration._config import Configuration
from granular_configuration._locations import Locations, PathOrStr
from granular_configuration.exceptions import InvalidBasePathException


def _read_base_path(base_path: str | typ.Sequence[str] | None) -> typ.Sequence[str]:
    if isinstance(base_path, str):
        return (base_path,)
    elif base_path:
        return base_path
    else:
        return tuple()


def _read_locations(load_order_location: typ.Iterable[PathOrStr], use_env_location: bool) -> Locations:
    if use_env_location and ("G_CONFIG_LOCATION" in os.environ):
        env_locs = os.environ["G_CONFIG_LOCATION"].split(",")
        load_order_location = chain(load_order_location, env_locs)
    return Locations(load_order_location)


class LazyLoadConfiguration(MutableMapping):
    """
    Provides a lazy interface for loading Configuration from file paths on first access.
    """

    def __init__(
        self,
        *load_order_location: PathOrStr,
        base_path: str | typ.Sequence[str] | None = None,
        use_env_location: bool = False,
    ) -> None:
        self.__base_path = _read_base_path(base_path)
        self.__locations = _read_locations(load_order_location, use_env_location)

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
        if not self.__locations:
            return self.__config
        else:
            with Lock():
                config = self.__config
                self.__locations = Locations(tuple())
                self.__base_path = tuple()
                return config

    @cached_property
    def __config(self) -> Configuration:
        config = build_configuration(self.__locations)
        try:
            config = reduce(op.getitem, self.__base_path, config)
        except KeyError as e:
            if e.__class__ is KeyError:
                message = str(e)
                raise InvalidBasePathException(message[1 : len(message) - 1])
            else:
                raise
        return config

    def load_configuration(self) -> None:
        """
        Force load the configuration.
        """
        # load_configuration existed prior to config, being a cached_property.
        # Now that logic is in the cached_property, so this legacy/clear code just calls the property
        self.config

    def __delitem__(self, key: typ.Any) -> None:
        del self.config[key]

    def __getitem__(self, key: typ.Any) -> typ.Any:
        return self.config[key]

    def __iter__(self) -> typ.Iterator[typ.Any]:
        return iter(self.config)

    def __len__(self) -> int:
        return len(self.config)

    def __setitem__(self, key: typ.Any, value: typ.Any) -> None:
        self.config[key] = value
