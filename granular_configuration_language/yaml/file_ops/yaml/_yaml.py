from __future__ import annotations

import typing as typ
from pathlib import Path

from granular_configuration_language.yaml.classes import LazyRoot, LoadOptions, Root
from granular_configuration_language.yaml.file_ops.text import EagerIOTextFile, read_text_data


def load_from_file(file: EagerIOTextFile | Path, /, options: LoadOptions, root: Root) -> typ.Any:
    """
    .. versionadded:: 2.3.0

    Load file from a Tag, using this library's loader (i.e. supports Tags).

    :param EagerIOTextFile | ~pathlib.Path file: File path.
    :param LoadOptions options: Options from the parent used to load the child.
    :param Root root: Root from the parent used to be the root of the child.
    :return: Parsed result
    :rtype: ~typing.Any
    """

    from granular_configuration_language.yaml.load import load_file

    lazy_root = LazyRoot.with_root(root)
    return load_file(file, lazy_root=lazy_root, mutable=options.mutable, previous_options=options)


def safe_load_from_file(file: EagerIOTextFile | Path, /) -> typ.Any:
    """
    .. versionadded:: 2.3.0

    Load file from a Tag, using a safe YAML loader (i.e. supports does not Tags).

    :param EagerIOTextFile | ~pathlib.Path file: File path.
    :return: Parsed result
    :rtype: ~typing.Any
    """

    from ruamel.yaml import YAML

    return YAML(typ="safe").load(read_text_data(file))
