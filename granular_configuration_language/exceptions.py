from __future__ import annotations


class DoesNotExist(ValueError):
    pass


class EnvironmentVaribleNotFound(KeyError):
    pass


class ErrorWhileLoadingFileOccurred(ValueError):
    pass


class ErrorWhileLoadingConfig(Exception):
    pass


class ErrorWhileLoadingTags(Exception):
    pass


class InterpolationWarning(Warning):
    pass


class InterpolationSyntaxError(Exception):
    pass


class IniUnsupportedError(Exception):
    pass


class InvalidBasePathException(KeyError):
    pass


class IsNotAClass(ValueError):
    pass


class IsNotCallable(ValueError):
    pass


class JSONPathOnlyWorksOnMappings(Exception):
    """
    .. deprecated:: 2.3.2
        Use :py:class:`.ReferencingRootOnlyWorksOnMappings`
    """

    pass


class JSONPathQueryFailed(KeyError):
    pass


class JSONPointerQueryFailed(KeyError):
    pass


class ParseEnvParsingError(Exception):
    pass


class ParsingTriedToCreateALoop(Exception):
    pass


class PlaceholderConfigurationError(Exception):
    pass


class RefMustStartFromRoot(Exception):
    pass


class ReferencingRootOnlyWorksOnMappings(JSONPathOnlyWorksOnMappings):
    """
    .. versionadded:: 2.4.0
    """

    pass


class ReservedFileExtension(Exception):
    pass


class TagHadUnsupportArgument(ValueError):
    """
    .. versionadded:: 2.3.0
    """

    pass
