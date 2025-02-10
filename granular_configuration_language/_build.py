from __future__ import annotations

import collections.abc as tabc
import typing as typ
from functools import partial
from itertools import chain
from pathlib import Path

from granular_configuration_language import Configuration
from granular_configuration_language._load import load_file
from granular_configuration_language._s import setter_secret
from granular_configuration_language._utils import consume
from granular_configuration_language.yaml import LazyRoot
from granular_configuration_language.yaml.load import obj_pairs_func

_C = typ.TypeVar("_C", bound=Configuration)


def _merge_into_base(configuration_type: typ.Type[_C], base_dict: _C, from_dict: _C) -> None:
    for key, value in from_dict._raw_items():
        if isinstance(value, configuration_type) and (key in base_dict):
            if base_dict.exists(key):
                new_dict = base_dict[key]
            else:  # If Placeholder
                new_dict = configuration_type()

            if isinstance(new_dict, configuration_type):
                _merge_into_base(configuration_type, new_dict, value)
                value = new_dict

        base_dict._private_set(key, value, setter_secret)


def _merge(configuration_type: typ.Type[_C], base_config: _C, configs: tabc.Iterable[_C]) -> _C:
    consume(map(partial(_merge_into_base, configuration_type, base_config), configs))
    return base_config


def _load_configs_from_locations(
    configuration_type: typ.Type[_C], locations: tabc.Iterable[Path], lazy_root: LazyRoot, mutable: bool
) -> tabc.Iterator[_C]:
    def configuration_only(
        configs: tabc.Iterable[_C | typ.Any],
    ) -> tabc.Iterator[_C]:
        for config in configs:
            if isinstance(config, configuration_type):
                yield config

    _load_file = partial(load_file, lazy_root=lazy_root, mutable=mutable)
    return configuration_only(map(_load_file, locations))


def _inject(*new: Configuration, configs: tabc.Iterator[_C], in_front: bool) -> tabc.Iterator[_C]:
    cast = typ.cast(_C, new)
    if in_front:
        return chain(cast, configs)
    else:
        return chain(configs, cast)


def _inject_configs(
    configs: tabc.Iterator[_C],
    *,
    before: Configuration | None,
    after: Configuration | None,
) -> tabc.Iterator[_C]:
    if before and isinstance(before, Configuration):
        configs = _inject(before, configs=configs, in_front=True)

    if after and isinstance(after, Configuration):
        configs = _inject(after, configs=configs, in_front=False)

    return configs


def build_configuration(
    locations: tabc.Iterable[Path],
    mutable: bool,
    *,
    inject_before: Configuration | None,
    inject_after: Configuration | None,
) -> Configuration:
    configuration_type = obj_pairs_func(mutable)
    base_config = configuration_type()
    lazy_root = LazyRoot.with_root(base_config)

    valid_configs = _inject_configs(
        _load_configs_from_locations(configuration_type, locations, lazy_root, mutable),
        before=inject_before,
        after=inject_after,
    )
    merged_config = _merge(configuration_type, base_config, valid_configs)

    return merged_config
