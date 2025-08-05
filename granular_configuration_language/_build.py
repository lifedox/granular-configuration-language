from __future__ import annotations

import collections.abc as tabc
import typing as typ
from functools import partial
from pathlib import Path

from granular_configuration_language import Configuration
from granular_configuration_language._configuration import C
from granular_configuration_language._s import setter_secret
from granular_configuration_language._utils import consume
from granular_configuration_language.yaml import LazyRoot
from granular_configuration_language.yaml.file_ops.text import load_text_file
from granular_configuration_language.yaml.load import load_file, obj_pairs_func


def _merge_into_base(configuration_type: type[C], base_dict: C, from_dict: C) -> None:
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


def _merge(configuration_type: type[C], base_config: C, configs: tabc.Iterable[C]) -> C:
    consume(map(partial(_merge_into_base, configuration_type, base_config), configs))
    return base_config


def _load_configs_from_locations(
    configuration_type: type[C], locations: tabc.Iterable[Path], lazy_root: LazyRoot, mutable: bool
) -> tabc.Iterator[C]:
    def configuration_only(
        configs: tabc.Iterable[C | typ.Any],
    ) -> tabc.Iterator[C]:
        for config in configs:
            if isinstance(config, configuration_type):
                yield config

    _load_file = partial(load_file, lazy_root=lazy_root, mutable=mutable)
    return configuration_only(map(_load_file, map(load_text_file, locations)))


def _inject_configs(
    configs: tabc.Iterator[C],
    *,
    before: Configuration | None,
    after: Configuration | None,
) -> tabc.Iterator[C]:
    if before and isinstance(before, Configuration):
        yield typ.cast(C, before)

    yield from configs

    if after and isinstance(after, Configuration):
        yield typ.cast(C, after)


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
