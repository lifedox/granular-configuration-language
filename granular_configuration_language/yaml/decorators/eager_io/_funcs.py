from __future__ import annotations

from granular_configuration_language.yaml.decorators import LoadOptions, Tag
from granular_configuration_language.yaml.decorators.interpolate import interpolate_value_eager_io
from granular_configuration_language.yaml.file_ops import as_file_path
from granular_configuration_language.yaml.file_ops.binary import EagerIOBinaryFile, load_binary_file
from granular_configuration_language.yaml.file_ops.text import EagerIOTextFile, load_text_file


def eager_io_text_loader(value: str, tag: Tag, options: LoadOptions) -> EagerIOTextFile:
    """
    .. versionadded:: 2.3.0

    Used by EagerIO Decorators to eagerly load a text file.

    - Reads the YAML string value as the relative file path.
    - Loads file as an :py:class:`.EagerIOTextFile`.

    .. admonition:: Available EagerIO Decorators
        :class: caution

        - :py:func:`.as_eager_io`
        - :py:func:`.as_eager_io_with_root_and_load_options`

    :param str value: YAML string, read as a relative file path
    :param Tag tag: Tag doing this, used for error reporting.
    :param LoadOptions options: options from the Tag doing this action, used for tracking chains.
    :return: Loaded File
    :rtype: EagerIOTextFile
    """

    return load_text_file(as_file_path(tag, value, options))


@interpolate_value_eager_io
def eager_io_text_loader_interpolates(value: str, tag: Tag, options: LoadOptions) -> EagerIOTextFile:
    """
    .. versionadded:: 2.3.0

    Used by EagerIO Decorators to eagerly load a text file.

    Same as :py:func:`eager_io_text_loader`, except `value` interpolated first.

    - Interpolates the YAML string
    - Reads the value as the relative file path.
    - Loads file as an :py:class:`.EagerIOTextFile`.

    .. admonition:: Available EagerIO Decorators
        :class: caution

        - :py:func:`.as_eager_io`
        - :py:func:`.as_eager_io_with_root_and_load_options`

    :param str value: YAML string, read as a relative file path, after interpolation
    :param Tag tag: Tag doing this, used for error reporting.
    :param LoadOptions options: options from the Tag doing this action, used for tracking chains.
    :return: Loaded File
    :rtype: EagerIOTextFile
    """
    return eager_io_text_loader(value, tag, options)


def eager_io_binary_loader(value: str, tag: Tag, options: LoadOptions) -> EagerIOBinaryFile:
    """
    .. versionadded:: 2.3.0

    Used by EagerIO Decorators to eagerly load a binary file.

    - Reads the YAML string value as the relative file path.
    - Loads file as an :py:class:`.EagerIOBinaryFile`.

    .. admonition:: Available EagerIO Decorators
        :class: caution

        - :py:func:`.as_eager_io`
        - :py:func:`.as_eager_io_with_root_and_load_options`

    :param str value: YAML string, read as a relative file path
    :param Tag tag: Tag doing this, used for error reporting.
    :param LoadOptions options: options from the Tag doing this action, used for tracking chains.
    :return: Loaded File
    :rtype: EagerIOBinaryFile
    """

    return load_binary_file(as_file_path(tag, value, options))


@interpolate_value_eager_io
def eager_io_binary_loader_interpolates(value: str, tag: Tag, options: LoadOptions) -> EagerIOBinaryFile:
    """
    .. versionadded:: 2.3.0

    Used by EagerIO Decorators to eagerly load a binary file.

    Same as :py:func:`eager_io_binary_loader`, except `value` interpolated first.

    - Interpolates the YAML string
    - Reads the value as the relative file path.
    - Loads file as an :py:class:`.EagerIOBinaryFile`.

    .. admonition:: Available EagerIO Decorators
        :class: caution

        - :py:func:`.as_eager_io`
        - :py:func:`.as_eager_io_with_root_and_load_options`

    :param str value: YAML string, read as a relative file path, after interpolation
    :param Tag tag: Tag doing this, used for error reporting.
    :param LoadOptions options: options from the Tag doing this action, used for tracking chains.
    :return: Loaded File
    :rtype: EagerIOBinaryFile
    """
    return eager_io_binary_loader(value, tag, options)
