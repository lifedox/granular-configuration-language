from __future__ import annotations

import dataclasses
import operator as op
import typing as typ
from collections import deque
from functools import cached_property, reduce
from threading import Lock
from weakref import WeakValueDictionary

from granular_configuration_language._build import build_configuration
from granular_configuration_language._configuration import Configuration
from granular_configuration_language._locations import Locations
from granular_configuration_language.base_path import BasePath, read_base_path


@dataclasses.dataclass(frozen=False, eq=False, kw_only=True)
class SharedConfigurationReference:
    _locations: Locations
    _mutable_config: bool
    __lock: Lock | None = dataclasses.field(repr=False, compare=False, init=False, default_factory=Lock)
    __notes: deque[NoteOfIntentToRead] = dataclasses.field(repr=False, compare=False, init=False, default_factory=deque)

    def register(self, note: NoteOfIntentToRead) -> None:
        self.__notes.append(note)

    def __clear_notes(self, caller: NoteOfIntentToRead) -> None:
        while self.__notes:
            note = self.__notes.pop()
            if note is not caller:
                note._config

    def build(self, caller: NoteOfIntentToRead) -> Configuration:
        # Making cached_property thread-safe
        if self.__lock:
            with self.__lock:
                self.__config
                self.__lock = None
                self.__clear_notes(caller)

        return self.__config

    @cached_property
    def __config(self) -> Configuration:
        return build_configuration(self._locations, self._mutable_config)


@dataclasses.dataclass(frozen=False, eq=False, kw_only=True)
class NoteOfIntentToRead:
    _base_path: BasePath
    _config_ref: SharedConfigurationReference

    def __post_init__(self) -> None:
        self._config_ref.register(self)

    @property
    def config(self) -> Configuration:
        config = self._config
        if isinstance(config, Exception):
            raise config
        else:
            return config

    @cached_property
    def _config(self) -> Configuration | Exception:
        config = self._config_ref.build(self)
        try:
            return reduce(op.getitem, self._base_path, config)
        except Exception as e:
            return e
        finally:
            del self._config_ref


store: typ.Final[WeakValueDictionary[Locations, SharedConfigurationReference]] = WeakValueDictionary()


def prepare_to_load_configuration(
    *, locations: Locations, base_path: str | typ.Sequence[str] | None, mutable_configuration: bool, disable_cache: bool
) -> NoteOfIntentToRead:
    if disable_cache or mutable_configuration:
        shared_config_ref = SharedConfigurationReference(_locations=locations, _mutable_config=mutable_configuration)
    elif locations not in store:
        shared_config_ref = SharedConfigurationReference(_locations=locations, _mutable_config=mutable_configuration)
        store[locations] = shared_config_ref
    else:
        shared_config_ref = store[locations]

    return NoteOfIntentToRead(_base_path=read_base_path(base_path), _config_ref=shared_config_ref)
