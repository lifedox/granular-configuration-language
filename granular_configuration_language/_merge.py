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

    Filters out non-:py:class:`.Configuration` object. Extracts :py:class:`.Configuration` from :py:class:`.LazyEval` and :py:class:`.LazyLoadConfiguration`

    :param configs: Configurations to be merged
    :type configs: ~collections.abc.Iterable[Configuration | LazyLoadConfiguration | LazyEval | ~typing.Any]
    :param mutable: If :py:data:`True`, :py:class:`.MutableConfiguration` is used, else :py:class:`.Configuration` is used.  Defaults to :py:data:`False`.
    :type mutable: bool, optional
    :return: Merged configuration. Empty if nothing was mergable.
    :rtype: Configuration
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
