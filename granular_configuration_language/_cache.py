from __future__ import annotations

import collections.abc as tabc
import dataclasses
import operator as op
import typing as typ
from collections import deque
from functools import cached_property, reduce
from threading import Lock
from weakref import WeakValueDictionary

from granular_configuration_language._base_path import BasePath, read_base_path
from granular_configuration_language._build import build_configuration
from granular_configuration_language._configuration import Configuration
from granular_configuration_language._locations import Locations


@dataclasses.dataclass(frozen=False, eq=False, kw_only=True)
class SharedConfigurationReference:
    _locations: Locations
    _mutable_config: bool
    _inject_before: Configuration | None = None
    _inject_after: Configuration | None = None
    __lock: Lock | None = dataclasses.field(repr=False, compare=False, init=False, default_factory=Lock)
    __notes: deque[NoteOfIntentToRead] = dataclasses.field(repr=False, compare=False, init=False, default_factory=deque)

    def register(self, note: NoteOfIntentToRead) -> None:
        self.__notes.append(note)

    def __clear_notes(self, caller: NoteOfIntentToRead) -> None:
        while self.__notes:
            note = self.__notes.pop()
            if note is not caller:
                note._config  # noqa: B018

    def build(self, caller: NoteOfIntentToRead) -> Configuration:
        # Making cached_property thread-safe
        if self.__lock:
            with self.__lock:
                self.__config  # noqa: B018
                self.__lock = None
                self.__clear_notes(caller)

        return self.__config

    @cached_property
    def __config(self) -> Configuration:
        return build_configuration(
            self._locations, self._mutable_config, inject_after=self._inject_after, inject_before=self._inject_before
        )


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
    *,
    locations: Locations,
    base_path: str | tabc.Sequence[str] | None,
    mutable_configuration: bool,
    disable_cache: bool,
    inject_before: Configuration | None,
    inject_after: Configuration | None,
) -> NoteOfIntentToRead:
    if disable_cache or mutable_configuration or inject_after or inject_before:
        shared_config_ref = SharedConfigurationReference(
            _locations=locations,
            _mutable_config=mutable_configuration,
            _inject_after=inject_after,
            _inject_before=inject_before,
        )
    elif locations not in store:
        shared_config_ref = SharedConfigurationReference(_locations=locations, _mutable_config=mutable_configuration)
        store[locations] = shared_config_ref
    else:
        shared_config_ref = store[locations]

    return NoteOfIntentToRead(_base_path=read_base_path(base_path), _config_ref=shared_config_ref)
