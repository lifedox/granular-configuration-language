from __future__ import annotations

import dataclasses
import operator as op
import typing as typ
from functools import cached_property, reduce
from threading import Lock
from weakref import WeakValueDictionary

from granular_configuration._build import build_configuration
from granular_configuration._config import Configuration
from granular_configuration._locations import Locations
from granular_configuration.base_path import BasePath, read_base_path
from granular_configuration.exceptions import InvalidBasePathException


@dataclasses.dataclass(frozen=False, eq=False, kw_only=True)
class SharedConfigurationReference:
    _locations: Locations
    _mutable_config: bool
    __lock: Lock | None = dataclasses.field(repr=False, compare=False, init=False, default_factory=Lock)

    @property
    def config(self) -> Configuration:
        # Making cached_property thread-safe
        if self.__lock:
            with self.__lock:
                self.__config
                self.__lock = None

        return self.__config

    @cached_property
    def __config(self) -> Configuration:
        return build_configuration(self._locations, self._mutable_config)


@dataclasses.dataclass(frozen=False, eq=False, kw_only=True)
class NoteOfIntentToRead:
    _base_path: BasePath
    _config_ref: SharedConfigurationReference

    @cached_property
    def config(self) -> Configuration:
        try:
            return reduce(op.getitem, self._base_path, self._config_ref.config)
        except KeyError as e:
            if e.__class__ is KeyError:
                message = str(e)
                raise InvalidBasePathException(message[1 : len(message) - 1])
            else:
                raise
        finally:
            del self._config_ref


store: typ.Final[WeakValueDictionary[Locations, SharedConfigurationReference]] = WeakValueDictionary()


def prepare_to_load_configuration(
    *, locations: Locations, base_path: str | typ.Sequence[str] | None, mutable_configuration: bool, disable_cache: bool
) -> NoteOfIntentToRead:
    if disable_cache:
        shared_config_ref = SharedConfigurationReference(_locations=locations, _mutable_config=mutable_configuration)
    elif locations not in store:
        shared_config_ref = SharedConfigurationReference(_locations=locations, _mutable_config=mutable_configuration)
        store[locations] = shared_config_ref
    else:
        shared_config_ref = store[locations]

    return NoteOfIntentToRead(_base_path=read_base_path(base_path), _config_ref=shared_config_ref)
