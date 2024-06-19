import typing as typ

from granular_configuration import Configuration, LazyLoadConfiguration
from granular_configuration._build import _merge


def merge(configs: typ.Iterable[Configuration | LazyLoadConfiguration | typ.Any]) -> Configuration:
    def _generator(
        configs: typ.Iterable[Configuration | LazyLoadConfiguration | typ.Any],
    ) -> typ.Iterator[Configuration]:
        for config in configs:
            if isinstance(config, Configuration):
                yield config
            elif isinstance(config, LazyLoadConfiguration):
                yield config.config

    return _merge(_generator(configs))
