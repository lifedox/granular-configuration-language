from __future__ import annotations

import dataclasses
from pathlib import Path


@dataclasses.dataclass(frozen=True)
class EagerIOTextFile:
    """
    Type: frozen :py:func:`dataclass <dataclasses.dataclass>`

    .. versionadded:: 2.3.0

    Encapsulates a file that has been read as text.
    """

    path: Path
    """
    File path
    """
    exists: bool
    """
    :py:data:`True`, if the file exists, else :py:data:`False`
    """
    data: str = dataclasses.field(repr=False, hash=False)
    """
    Contents of the file, if the file exists, else an empty :py:class:`str`
    """


def load_text_file(file: Path, /) -> EagerIOTextFile:
    """
    .. versionadded:: 2.3.0

    Load the text file as an :py:class:`.EagerIOTextFile` instance

    :param ~pathlib.Path file: file path
    :return: Constructed instance
    :rtype: EagerIOTextFile
    """
    exists = file.exists()
    if exists:
        return EagerIOTextFile(file, exists, file.read_text())
    else:
        return EagerIOTextFile(file, exists, "")


def read_text_data(filename: Path | EagerIOTextFile, /) -> str:
    """
    .. versionadded:: 2.3.0

    Read file contents.

    Whether it is already loaded (as an :py:class:`.EagerIOTextFile` instance) or as a :py:class:`~pathlib.Path`

    :param ~pathlib.Path | EagerIOTextFile filename: File path
    :raises FileNotFoundError: Errors if the file does not exist.
    :return: File contents.
    :rtype: str
    """

    if isinstance(filename, EagerIOTextFile):
        if filename.exists:
            return filename.data
        else:
            raise FileNotFoundError(f"[Errno 2] No such file or directory: '{filename.path}'")
    else:
        return filename.read_text()
