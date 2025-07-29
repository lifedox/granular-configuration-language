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

    .. admonition:: Why does this exist?
        :class: tip

        - To enable merging a framework configuration with a library-specific configuration.

          - The explicit case was for a ``pytest`` sub-plugin that was a part of a framework plugin.
          - Using :py:func:`.merge` allows users to set settings in the framework configuration without requiring
            the framework configuration needing to know about the sub-plugin.

            - ``base_path`` is required to ensure safety.

    .. caution::

        Don't use :py:func:`.merge` as a replacement for :py:class:`.LazyLoadConfiguration`.
        It is less efficient and creates :ref:`Load Boundaries <load-boundary-limitations>` on each configuration.

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

            match config:
                case Configuration():
                    yield config
                case LazyLoadConfiguration():
                    yield config.config
                case PathLike():
                    if mutable:
                        yield MutableLazyLoadConfiguration(config).config
                    else:
                        yield LazyLoadConfiguration(config).config
                case _:
                    continue

    configuration_type = obj_pairs_func(mutable)
    base_config = configuration_type()
    return _merge(configuration_type, base_config, configuration_only(configs))
