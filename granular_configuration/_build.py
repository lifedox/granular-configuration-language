import typing as typ
from functools import partial
from pathlib import Path

from granular_configuration import Configuration
from granular_configuration._load import load_file
from granular_configuration.utils import consume
from granular_configuration.yaml_handler import LazyRoot


def build_configuration(locations: typ.Iterable[Path]) -> Configuration:
    lazy_root = LazyRoot()
    _load_file = partial(load_file, obj_pairs_hook=Configuration, lazy_root=lazy_root)
    available_configs = map(_load_file, locations)
    valid_configs = filter(lambda config: isinstance(config, Configuration), available_configs)

    merged_config = _merge(valid_configs)
    lazy_root._set_root(merged_config)

    return merged_config


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


def _merge(configs: typ.Iterable[Configuration]) -> Configuration:
    base_conf = Configuration()
    consume(map(partial(_merge_into_base, base_conf), configs))
    return base_conf
