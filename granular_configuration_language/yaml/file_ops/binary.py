from __future__ import annotations

import dataclasses
from pathlib import Path


@dataclasses.dataclass(frozen=True)
class EagerIOBinaryFile:
    """
    .. versionadded:: 2.3.0

    Encapsulates a file that has been read as binary.
    """

    path: Path
    """
    File path
    """
    exists: bool
    """
    :py:data:`True`, if the file exists, else :py:data:`False`
    """
    data: bytes = dataclasses.field(repr=False, hash=False)
    """
    Contents of the file, if the file exists, else an empty :py:class:`bytes`
    """


def load_binary_file(file: Path, /) -> EagerIOBinaryFile:
    """
    .. versionadded:: 2.3.0

    Load the binary file as an :py:class:`.EagerIOBinaryFile` instance

    :param ~pathlib.Path file: file path
    :return: Constructed instance
    :rtype: EagerIOBinaryFile
    """
    exists = file.exists()
    if exists:
        return EagerIOBinaryFile(file, exists, file.read_bytes())
    else:
        return EagerIOBinaryFile(file, exists, b"")


def read_binary_data(filename: Path | EagerIOBinaryFile, /) -> bytes:
    """
    .. versionadded:: 2.3.0

    Read file contents.

    Whether it is already loaded (as an :py:class:`.EagerIOBinaryFile` instance) or as a :py:class:`~pathlib.Path`

    :param ~pathlib.Path | EagerIOTextFile filename: File path
    :raises FileNotFoundError: Errors if the file does not exist.
    :return: File contents.
    :rtype: bytes
    """
    if isinstance(filename, EagerIOBinaryFile):
        if filename.exists:
            return filename.data
        else:
            raise FileNotFoundError(f"[Errno 2] No such file or directory: '{filename.path}'")
    else:
        return filename.read_bytes()
