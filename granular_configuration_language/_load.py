from __future__ import annotations

import typing as typ
from pathlib import Path

from granular_configuration_language.exceptions import (
    ErrorWhileLoadingFileOccurred,
    IniUnsupportedError,
    ParsingTriedToCreateALoop,
    ReservedFileExtension,
)
from granular_configuration_language.yaml import LazyRoot
from granular_configuration_language.yaml import loads as yaml_loader
from granular_configuration_language.yaml._parsing import FILE_EXTENSION
from granular_configuration_language.yaml.classes import LoadOptions


def _load_file(
    *,
    filename: Path,
    mutable: bool,
    lazy_root: LazyRoot | None,
    previous_options: LoadOptions | None,
) -> typ.Any:
    try:
        return yaml_loader(
            filename.read_text(),
            lazy_root=lazy_root,
            file_path=filename,
            mutable=mutable,
            previous_options=previous_options,
        )
    except ParsingTriedToCreateALoop:
        raise
    except FileNotFoundError as e:
        raise FileNotFoundError(e) from None
    except Exception as e:
        raise ErrorWhileLoadingFileOccurred(f'Problem in file "{filename}": ({e.__class__.__name__}) {e}') from None


def load_file(
    filename: Path,
    *,
    mutable: bool,
    lazy_root: LazyRoot | None = None,
    previous_options: LoadOptions | None = None,
) -> typ.Any:
    if filename.suffix == ".ini":
        raise IniUnsupportedError("INI support has been removed")
    elif filename.suffix == FILE_EXTENSION:
        raise ReservedFileExtension(f"`{FILE_EXTENSION}` is a reserved internal file extension")
    else:
        return _load_file(
            filename=filename,
            mutable=mutable,
            lazy_root=lazy_root,
            previous_options=previous_options,
        )
