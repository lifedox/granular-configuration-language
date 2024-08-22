import typing as typ
from pathlib import Path

from granular_configuration.exceptions import ErrorWhileLoadingFileOccurred, IniUnsupportedError
from granular_configuration.yaml import LazyRoot, loads


def load_file(
    filename: Path,
    *,
    mutable: bool,
    lazy_root: typ.Optional[LazyRoot] = None,
) -> typ.Any:
    try:
        if filename.suffix == ".ini":
            raise IniUnsupportedError("INI support has been removed")
        else:
            loader = loads

        return loader(filename.read_text(), lazy_root=lazy_root, file_path=filename, mutable=mutable)
    except IniUnsupportedError:
        raise
    except FileNotFoundError as e:
        raise FileNotFoundError(e) from None
    except Exception as e:
        raise ErrorWhileLoadingFileOccurred('Problem in file "{}": {}'.format(filename, e))
