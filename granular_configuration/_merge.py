import typing as typ

from granular_configuration import Configuration, LazyLoadConfiguration
from granular_configuration._build import _merge
from granular_configuration.yaml import LazyEval


def merge(configs: typ.Iterable[Configuration | LazyLoadConfiguration | LazyEval | typ.Any]) -> Configuration:
    def configuration_only(
        configs: typ.Iterable[Configuration | LazyLoadConfiguration | LazyEval | typ.Any],
    ) -> typ.Iterator[Configuration]:
        for config in configs:
            if isinstance(config, LazyEval):
                config = config.result

            if isinstance(config, Configuration):
                yield config
            elif isinstance(config, LazyLoadConfiguration):
                yield config.config

    base_config = Configuration()
    return _merge(base_config, configuration_only(configs))
