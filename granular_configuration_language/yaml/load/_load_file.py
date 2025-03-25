from __future__ import annotations

import typing as typ
from pathlib import Path

from granular_configuration_language.exceptions import (
    ErrorWhileLoadingFileOccurred,
    IniUnsupportedError,
    ParsingTriedToCreateALoop,
    ReservedFileExtension,
)
from granular_configuration_language.yaml.classes import LazyRoot, LoadOptions
from granular_configuration_language.yaml.file_ops.environment_variable import (
    ENV_VAR_FILE_EXTENSION,
    _EagerIOEnvariableVariable,
)
from granular_configuration_language.yaml.file_ops.text import EagerIOTextFile, read_text_data
from granular_configuration_language.yaml.load import loads as yaml_loader


def _load_file(
    *,
    filename: Path | EagerIOTextFile,
    mutable: bool,
    lazy_root: LazyRoot | None,
    previous_options: LoadOptions | None,
) -> typ.Any:
    try:
        return yaml_loader(
            read_text_data(filename),
            lazy_root=lazy_root,
            file_path=filename.path if isinstance(filename, EagerIOTextFile) else filename,
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
    filename: Path | EagerIOTextFile,
    *,
    mutable: bool,
    lazy_root: LazyRoot | None = None,
    previous_options: LoadOptions | None = None,
) -> typ.Any:
    suffix = filename.path.suffix if isinstance(filename, EagerIOTextFile) else filename.suffix
    if suffix == ".ini":
        raise IniUnsupportedError("INI support has been removed")
    elif (suffix == ENV_VAR_FILE_EXTENSION) and not isinstance(filename, _EagerIOEnvariableVariable):
        raise ReservedFileExtension(f"`{ENV_VAR_FILE_EXTENSION}` is a reserved internal file extension")
    else:
        return _load_file(
            filename=filename,
            mutable=mutable,
            lazy_root=lazy_root,
            previous_options=previous_options,
        )
