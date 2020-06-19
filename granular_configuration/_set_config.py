import typing as typ
from itertools import chain

from granular_configuration._config import LazyLoadConfiguration
from granular_configuration.exceptions import GetConfigReadBeforeSetException

_SET_CONFIG_META: typ.Optional[typ.Tuple[str, ...]] = None


def set_config(*load_order_location: str) -> None:
    global _SET_CONFIG_META
    _SET_CONFIG_META = load_order_location


def clear_config() -> None:
    global _SET_CONFIG_META
    _SET_CONFIG_META = None


def get_config(
    *load_order_location: str,
    base_path: typ.Optional[typ.Union[str, typ.Sequence[str]]] = None,
    use_env_location: bool = False,
    requires_set: bool = True,
) -> LazyLoadConfiguration:
    if requires_set and (_SET_CONFIG_META is None):
        raise GetConfigReadBeforeSetException("get_config requires that set_config before called before use.")

    if _SET_CONFIG_META:
        return LazyLoadConfiguration(
            *chain(load_order_location, _SET_CONFIG_META), base_path=base_path, use_env_location=use_env_location
        )
    else:
        return LazyLoadConfiguration(*load_order_location, base_path=base_path, use_env_location=use_env_location)
