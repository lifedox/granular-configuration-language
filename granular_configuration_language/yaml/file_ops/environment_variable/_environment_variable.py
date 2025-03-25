from __future__ import annotations

import os
from pathlib import Path

from granular_configuration_language.yaml.classes import LoadOptions, Tag
from granular_configuration_language.yaml.file_ops._chain import ENV_VAR_FILE_EXTENSION, is_in_chain, make_chain_message
from granular_configuration_language.yaml.file_ops.text import EagerIOTextFile


def create_environment_variable_path(env_var: str) -> Path:
    return Path(env_var + ENV_VAR_FILE_EXTENSION)


def as_environment_variable_path(tag: Tag, variable_name: str, options: LoadOptions) -> Path:
    """
    Converts the environment variable to a :py:class:`~pathlib.Path` and checks if it has already been loaded.

    .. note::

        Uses a reversed file extension.

    :param Tag tag: Tag doing this, used for error reporting.
    :param str variable_name: Name of the environment variable being loaded
    :param LoadOptions options: options from the Tag doing this action, used for tracking chains.
    :return: Path instance
    :rtype: ~pathlib.Path
    """

    file_path = create_environment_variable_path(variable_name)

    if is_in_chain(file_path, options):
        raise make_chain_message(tag, variable_name, options)

    return file_path


class _EagerIOEnvariableVariable(EagerIOTextFile):
    pass


def load_as_file(tag: Tag, variable_name: str, options: LoadOptions) -> EagerIOTextFile:
    """
    Load the environment variable, as if it were an already loaded file.

    (A missing environment variable follows the conventions of a missing file, setting the `exists` flag to :py:data:`False`)

    :param Tag tag: Tag doing this, used for error reporting.
    :param str variable_name: Name of the environment variable being loaded
    :param LoadOptions options: options from the Tag doing this action, used for tracking chains.
    :return: Constructed instance
    :rtype: EagerIOTextFile
    """

    return _EagerIOEnvariableVariable(
        as_environment_variable_path(tag, variable_name, options),
        variable_name in os.environ,
        os.environ.get(variable_name, ""),
    )
