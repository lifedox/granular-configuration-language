import typing as typ
from pathlib import Path

from granular_configuration._config import Configuration
from granular_configuration.yaml.classes import _OPH, LazyEval, LazyRoot
from granular_configuration.yaml.load._handler import internal


def external(
    config_str: str,
    obj_pairs_hook: _OPH = Configuration,
    *,
    lazy_root: typ.Optional[LazyRoot] = None,
    file_path: typ.Optional[Path] = None,
) -> typ.Any:
    result = internal(config_str, obj_pairs_hook=obj_pairs_hook, lazy_root=lazy_root, file_path=file_path)
    if isinstance(result, LazyEval):
        return result.result
    else:
        return result
