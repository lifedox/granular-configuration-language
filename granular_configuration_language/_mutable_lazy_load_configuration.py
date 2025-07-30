from __future__ import annotations

import collections.abc as tabc
import sys
import typing as typ
from collections.abc import MutableMapping

from granular_configuration_language import LazyLoadConfiguration, MutableConfiguration
from granular_configuration_language._configuration import C
from granular_configuration_language._locations import PathOrStr

if sys.version_info >= (3, 12):
    from typing import override
elif typ.TYPE_CHECKING:
    from typing_extensions import override
else:

    def override(func: tabc.Callable) -> tabc.Callable:
        return func

# Refactored out of _lazy_load_configuration.py just because spell checking plugin doesn't like something.


class MutableLazyLoadConfiguration(LazyLoadConfiguration, MutableMapping):
    r"""
    Used to define a **mutable** Configuration from file paths
    that lazily loads on first access.

    **Options:**
        -  Using ``env_location_var_name``, you can enable pulling locations
           from an environment variable.

    .. tip::

        Consider using an immutable configuration with
        :py:class:`.LazyLoadConfiguration` in you code to reduce unexpected
        side-effects.

    .. admonition:: Classes used for mutability
        :class: note
        :collapsible: closed

        - :py:class:`.MutableConfiguration` for mappings
        - :py:class:`list` for sequences

    :param ~pathlib.Path | str | os.PathLike \*load_order_location:
            File path to configuration file
    :param str | ~collections.abc.Sequence[str], optional base_path:
        Defines the subsection of the configuration file to use.
        See Examples for usage options.
    :param bool, optional use_env_location:
        - Enabled to use the default environment variable location.
        - Setting to :py:data:`True` is only required if you don't change
          ``env_location_var_name`` from its default value.
    :param str, optional env_location_var_name:
        - Specify what environment variable to check for additional file paths.
        - The Environment Variable is read as a comma-delimited list of
          configuration path that will be appended to ``load_order_location``
          list.
        - Setting the Environment Variable is always optional.
        - *Default*: ``G_CONFIG_LOCATION``

          - Setting ``use_env_location=True`` is required to use the default
            value.

    :examples:
        .. code-block:: python

            # Base Path - Single Key
            MutableLazyLoadConfiguration(..., base_path="base_path")
            # Base Path - JSON Pointer (strings only)
            MutableLazyLoadConfiguration(..., base_path="/base/path")
            # Base Path - List of keys
            MutableLazyLoadConfiguration(..., base_path=("base", "path"))

            # Use Environment Variable: "CONFIG_LOC"
            MutableLazyLoadConfiguration(..., env_location_var_name="CONFIG_LOC")

            # Use default Environment Variable: "G_CONFIG_LOCATION"
            MutableLazyLoadConfiguration(..., use_env_location=True)
    """

    def __init__(
        self,
        *load_order_location: PathOrStr,
        base_path: str | tabc.Sequence[str] | None = None,
        use_env_location: bool = False,
        env_location_var_name: str = "G_CONFIG_LOCATION",
    ) -> None:
        super().__init__(
            *load_order_location,
            base_path=base_path,
            use_env_location=use_env_location,
            env_location_var_name=env_location_var_name,
            inject_before=None,
            inject_after=None,
            disable_caching=True,
            _mutable_configuration=True,
        )

    @property
    @override
    def config(self) -> MutableConfiguration:
        """
        Load and fetch the configuration. Configuration is cached for
        subsequent calls.

        .. admonition:: Thread-safe
            :class: tip
            :collapsible: closed

            Loading the configuration is thread-safe and locks while the
            configuration is loaded to prevent duplicative processing and data

        """
        return typ.cast(MutableConfiguration, super().config)

    @override
    def __delitem__(self, key: typ.Any) -> None:
        del self.config[key]

    @override
    def __setitem__(self, key: typ.Any, value: typ.Any) -> None:
        self.config[key] = value

    @override
    def as_typed(self, typed_base: type[C]) -> typ.NoReturn:
        """
        Not supported for :py:class:`MutableLazyLoadConfiguration`.
        Use :py:class:`LazyLoadConfiguration`.
        """
        raise NotImplementedError(
            "`as_typed` is not supported for `MutableLazyLoadConfiguration`. Use `LazyLoadConfiguration`."
        )

    @override
    def eager_load(self, typed_base: type[C]) -> typ.NoReturn:
        """
        Not supported for :py:class:`MutableLazyLoadConfiguration`.
        Use :py:class:`LazyLoadConfiguration`.
        """
        raise NotImplementedError(
            "`eager_load` is not supported for `MutableLazyLoadConfiguration`. Use `LazyLoadConfiguration`."
        )
