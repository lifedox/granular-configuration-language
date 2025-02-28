from __future__ import annotations

import collections.abc as tabc
import typing as typ
from os import PathLike

from granular_configuration_language import Configuration, LazyLoadConfiguration, MutableLazyLoadConfiguration
from granular_configuration_language._build import _merge
from granular_configuration_language.yaml import LazyEval
from granular_configuration_language.yaml.load import obj_pairs_func


def merge(
    configs: tabc.Iterable[Configuration | LazyLoadConfiguration | LazyEval | PathLike | typ.Any],
    *,
    mutable: bool = False,
) -> Configuration:
    """Merges the provided configurations into a single configuration.

    - Filters out non-:py:class:`.Configuration` objects.
    - Extracts :py:class:`.Configuration` from :py:class:`.LazyEval` and :py:class:`.LazyLoadConfiguration`.
    - Any :py:class:`os.PathLike` objects are loaded via individual :py:class:`.LazyLoadConfiguration` instances.

    .. caution::

        Don't use :py:func:`.merge` as a replacement for :py:class:`.LazyLoadConfiguration`. It is less efficient and creates Load Boundaries on each configuration.

    .. admonition:: Attention
        :class: error

        - :py:class:`dict` does not act as :py:class:`.Configuration`.
        - :py:class:`dict` instances are values that do not merge.

    :param ~collections.abc.Iterable[Configuration | LazyLoadConfiguration | LazyEval | ~os.PathLike | ~typing.Any] configs: Configurations
        to be merged
    :param bool, optional mutable: If :py:data:`True`, :py:class:`.MutableConfiguration` is used, else
        :py:class:`.Configuration` is used. Defaults to :py:data:`False`.

    :returns: Merged configuration. Empty if nothing was mergeable.
    :rtype: Configuration

    """

    def configuration_only(
        configs: tabc.Iterable[Configuration | LazyLoadConfiguration | LazyEval | PathLike | typ.Any],
    ) -> tabc.Iterator[Configuration]:
        for config in configs:
            if isinstance(config, LazyEval):
                config = config.result

            if isinstance(config, Configuration):
                yield config
            elif isinstance(config, LazyLoadConfiguration):
                yield config.config
            elif isinstance(config, PathLike):
                if mutable:
                    yield MutableLazyLoadConfiguration(config).config
                else:
                    yield LazyLoadConfiguration(config).config

    configuration_type = obj_pairs_func(mutable)
    base_config = configuration_type()
    return _merge(configuration_type, base_config, configuration_only(configs))
