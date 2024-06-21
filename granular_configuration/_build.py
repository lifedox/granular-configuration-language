import typing as typ
from functools import partial
from pathlib import Path

from granular_configuration import Configuration
from granular_configuration._load import load_file
from granular_configuration.utils import consume
from granular_configuration.yaml_handler import LazyEval, LazyRoot


def _merge_into_base(base_dict: Configuration, from_dict: Configuration) -> None:
    for key, value in from_dict._raw_items():
        if isinstance(value, Configuration) and (key in base_dict):
            if not base_dict.exists(key):
                base_dict[key] = Configuration()
            elif not isinstance(base_dict[key], Configuration):
                continue

            new_dict = base_dict[key]
            _merge_into_base(new_dict, value)
            value = new_dict

        base_dict[key] = value


def _merge(base_config: Configuration, configs: typ.Iterable[Configuration]) -> Configuration:
    consume(map(partial(_merge_into_base, base_config), configs))
    return base_config


def _load_configs_from_locations(locations: typ.Iterable[Path], lazy_root: LazyRoot) -> typ.Iterator[Configuration]:
    def configuration_only(
        configs: typ.Iterable[Configuration | typ.Any],
    ) -> typ.Iterator[Configuration]:
        for config in configs:
            while isinstance(config, LazyEval):
                config = config.run()

            if isinstance(config, Configuration):
                yield config

    _load_file = partial(load_file, obj_pairs_hook=Configuration, lazy_root=lazy_root)
    return configuration_only(map(_load_file, locations))


def build_configuration(locations: typ.Iterable[Path]) -> Configuration:
    lazy_root = LazyRoot()
    base_config = Configuration()
    lazy_root._set_root(base_config)

    valid_configs = _load_configs_from_locations(locations, lazy_root)
    merged_config = _merge(base_config, valid_configs)

    return merged_config
