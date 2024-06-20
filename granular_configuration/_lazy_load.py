import os
import typing as typ
from collections.abc import MutableMapping
from functools import reduce
from itertools import chain
from pathlib import Path

from granular_configuration._build import build_configuration
from granular_configuration._config import Configuration
from granular_configuration._locations import ConfigurationLocations, get_all_unique_locations, parse_location
from granular_configuration.exceptions import InvalidBasePathException


class LazyLoadConfiguration(MutableMapping):
    """
    Provides a lazy interface for loading Configuration from ConfigurationLocations definitions on first access.
    """

    def __init__(
        self,
        *load_order_location: typ.Union[str, ConfigurationLocations, Path],
        base_path: typ.Optional[typ.Union[str, typ.Sequence[str]]] = None,
        use_env_location: bool = False,
    ) -> None:
        self.__base_path: typ.Optional[typ.Sequence[str]]
        if isinstance(base_path, str):
            self.__base_path = [base_path]
        elif base_path:
            self.__base_path = base_path
        else:
            self.__base_path = []

        if use_env_location and ("G_CONFIG_LOCATION" in os.environ):
            env_locs = os.environ["G_CONFIG_LOCATION"].split(",")
            if env_locs:
                load_order_location = tuple(chain(load_order_location, env_locs))
        self._config: typ.Optional[Configuration] = None
        self.__locations: typ.Optional[typ.Sequence[ConfigurationLocations]] = tuple(
            map(parse_location, load_order_location)
        )

    def __getattr__(self, name: str) -> typ.Any:
        """
        Loads (if not loaded) and fetches from the underlying Configuration object.
        This also exposes the methods of Configuration (except dunders).
        """
        return getattr(self.config, name)

    def load_configuration(self) -> None:
        """
        Force load the configuration.
        """
        if self._config is None and self.__base_path is not None and self.__locations is not None:
            config = build_configuration(get_all_unique_locations(self.__locations))
            try:
                self._config = reduce(lambda dic, key: dic[key], self.__base_path, config)
            except KeyError as e:
                message = str(e)
                raise InvalidBasePathException(message[1 : len(message) - 1])
            self.__locations = None
            self.__base_path = None

    @property
    def config(self) -> Configuration:
        """
        Loads and fetches the underlying Configuration object
        """
        if self._config is None:
            self.load_configuration()

        if self._config is None:  # pragma: no cover
            raise TypeError("LazyLoadConfiguration loaded null")
        else:
            return self._config

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
