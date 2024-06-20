import typing as typ
from pathlib import Path

from granular_configuration.yaml_handler import LazyRoot
from granular_configuration.yaml_handler import loads as yaml_loads


def load_file(
    filename: Path,
    *,
    obj_pairs_hook: typ.Optional[typ.Type[typ.MutableMapping]] = None,
    lazy_root: typ.Optional[LazyRoot] = None,
) -> typ.Any:
    try:
        loader = yaml_loads

        return loader(filename.read_text(), obj_pairs_hook=obj_pairs_hook, lazy_root=lazy_root, file_path=filename)
    except Exception as e:
        raise ValueError('Problem in file "{}": {}'.format(filename, e))
