import typing as typ
from granular_configuration import LazyLoadConfiguration

_SET_CONFIG_META: typ.Optional[typ.Sequence[str]]

def set_config(*load_order_location: str) -> None: ...
def clear_config() -> None: ...
def get_config(
    *load_order_location: str, base_path: typ.Union[str, typ.Sequence[str]], requires_set: bool = True
) -> LazyLoadConfiguration: ...
