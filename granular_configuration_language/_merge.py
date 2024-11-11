import typing as typ

from granular_configuration_language import Configuration, LazyLoadConfiguration
from granular_configuration_language._build import _merge
from granular_configuration_language.yaml import LazyEval
from granular_configuration_language.yaml.load import obj_pairs_func


def merge(
    configs: typ.Iterable[Configuration | LazyLoadConfiguration | LazyEval | typ.Any], *, mutable: bool = False
) -> Configuration:
    """
    Merges the provided configurations into a single configuration.

    Filters out non-`Configuration` object. Extracts `Configuration` from `LazyEval` and `LazyLoadConfiguration`

    Args:
        configs (Iterable[Configuration  |  LazyLoadConfiguration  |  LazyEval  |  Any]):
            Configurations to be merged
        mutable (bool, optional):
            If `True`, `MutableConfiguration` is used, else `Configuration` is used.
           _description_. Defaults to False.

    Returns:
        Configuration: Merged Configuration. Empty if nothing was mergable.
    """

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

    configuration_type = obj_pairs_func(mutable)
    base_config = configuration_type()
    return _merge(configuration_type, base_config, configuration_only(configs))
