import typing as typ
from pathlib import Path

from granular_configuration.exceptions import ErrorWhileLoadingFileOccurred, IniUnsupportedError
from granular_configuration.yaml import LazyRoot, loads
from granular_configuration.yaml.classes import _OPH


def load_file(
    filename: Path,
    *,
    obj_pairs_hook: _OPH = None,
    lazy_root: typ.Optional[LazyRoot] = None,
) -> typ.Any:
    try:
        if filename.suffix == ".ini":
            raise IniUnsupportedError("INI support has been removed")
        else:
            loader = loads

        return loader(filename.read_text(), obj_pairs_hook=obj_pairs_hook, lazy_root=lazy_root, file_path=filename)
    except IniUnsupportedError:
        raise
    except FileNotFoundError as e:
        raise FileNotFoundError(e) from None
    except Exception as e:
        raise ErrorWhileLoadingFileOccurred('Problem in file "{}": {}'.format(filename, e))
