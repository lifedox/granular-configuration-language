from __future__ import annotations

import typing as typ
from pathlib import Path

from granular_configuration_language.exceptions import (
    ErrorWhileLoadingFileOccurred,
    IniUnsupportedError,
    ParsingTriedToCreateALoop,
    ReservedFileExtension,
)
from granular_configuration_language.yaml import LazyRoot, loads
from granular_configuration_language.yaml._parsing import FILE_EXTENSION
from granular_configuration_language.yaml.classes import LoadOptions


def load_file(
    filename: Path,
    *,
    mutable: bool,
    lazy_root: typ.Optional[LazyRoot] = None,
    previous_options: LoadOptions | None = None,
) -> typ.Any:
    try:
        if filename.suffix == ".ini":
            raise IniUnsupportedError("INI support has been removed")
        elif filename.suffix == FILE_EXTENSION:
            raise ReservedFileExtension(f"`{FILE_EXTENSION}` is a reserved internal file extension")
        else:
            loader = loads

        return loader(
            filename.read_text(),
            lazy_root=lazy_root,
            file_path=filename,
            mutable=mutable,
            previous_options=previous_options,
        )
    except (IniUnsupportedError, ParsingTriedToCreateALoop, ReservedFileExtension):
        raise
    except FileNotFoundError as e:
        raise FileNotFoundError(e) from None
    except Exception as e:
        raise ErrorWhileLoadingFileOccurred(f'Problem in file "{filename}": ({e.__class__.__name__}) {e}')
