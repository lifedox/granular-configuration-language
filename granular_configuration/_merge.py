import typing as typ

from granular_configuration import Configuration, LazyLoadConfiguration, MutableConfiguration
from granular_configuration._build import _merge
from granular_configuration.yaml import LazyEval


def merge(
    configs: typ.Iterable[Configuration | LazyLoadConfiguration | LazyEval | typ.Any], *, mutable: bool = False
) -> Configuration:
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

    configuration_type = MutableConfiguration if mutable else Configuration
    base_config = configuration_type()
    return _merge(configuration_type, base_config, configuration_only(configs))
