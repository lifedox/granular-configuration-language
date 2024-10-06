import typing as typ
from functools import partial
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
            if not base_dict.exists(key):
                base_dict._private_set(key, configuration_type(), setter_secret)
            elif not isinstance(base_dict[key], configuration_type):
                continue

            new_dict = base_dict[key]
            _merge_into_base(configuration_type, new_dict, value)
            value = new_dict

        base_dict._private_set(key, value, setter_secret)


def _merge(configuration_type: typ.Type[_C], base_config: _C, configs: typ.Iterable[_C]) -> _C:
    consume(map(partial(_merge_into_base, configuration_type, base_config), configs))
    return base_config


def _load_configs_from_locations(
    configuration_type: typ.Type[_C], locations: typ.Iterable[Path], lazy_root: LazyRoot, mutable: bool
) -> typ.Iterator[_C]:
    def configuration_only(
        configs: typ.Iterable[_C | typ.Any],
    ) -> typ.Iterator[_C]:
        for config in configs:
            if isinstance(config, configuration_type):
                yield config

    _load_file = partial(load_file, lazy_root=lazy_root, mutable=mutable)
    return configuration_only(map(_load_file, locations))


def build_configuration(locations: typ.Iterable[Path], mutable: bool) -> Configuration:
    configuration_type = obj_pairs_func(mutable)
    base_config = configuration_type()
    lazy_root = LazyRoot.with_root(base_config)

    valid_configs = _load_configs_from_locations(configuration_type, locations, lazy_root, mutable)
    merged_config = _merge(configuration_type, base_config, valid_configs)

    return merged_config
