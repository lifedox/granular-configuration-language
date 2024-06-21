import typing as typ

from granular_configuration import Configuration, LazyLoadConfiguration
from granular_configuration._build import _merge
from granular_configuration.yaml_handler import LazyEval


def merge(configs: typ.Iterable[Configuration | LazyLoadConfiguration | typ.Any]) -> Configuration:
    def configuration_only(
        configs: typ.Iterable[Configuration | LazyLoadConfiguration | typ.Any],
    ) -> typ.Iterator[Configuration]:
        for config in configs:
            while isinstance(config, LazyEval):
                config = config.run()

            if isinstance(config, Configuration):
                yield config
            elif isinstance(config, LazyLoadConfiguration):
                yield config.config

    base_config = Configuration()
    return _merge(base_config, configuration_only(configs))
