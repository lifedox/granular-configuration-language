from granular_configuration import LazyLoadConfiguration
from granular_configuration.exceptions import GetConfigReadBeforeSetException
from itertools import chain

_SET_CONFIG_META = None


def set_config(*load_order_location):
    global _SET_CONFIG_META
    _SET_CONFIG_META = load_order_location


def clear_config():
    global _SET_CONFIG_META
    _SET_CONFIG_META = None


def get_config(*load_order_location, **kwargs):
    if kwargs.pop("requires_set", True) and (_SET_CONFIG_META is None):
        raise GetConfigReadBeforeSetException("get_config requires that set_config before called before use.")

    if _SET_CONFIG_META:
        return LazyLoadConfiguration(*chain(load_order_location, _SET_CONFIG_META), **kwargs)
    else:
        return LazyLoadConfiguration(*load_order_location, **kwargs)
