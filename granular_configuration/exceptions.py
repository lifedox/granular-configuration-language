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


class GetConfigReadBeforeSetException(Exception):
    pass


class InterpolationWarning(Warning):
    pass


class InterpolationSyntaxError(Exception):
    pass


class IniKeyExistAsANonMapping(Exception):
    pass


class IniTryToReplaceExistingKey(Exception):
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
    pass


class JSONPathQueryFailed(KeyError):
    pass


class JSONPointerQueryFailed(KeyError):
    pass


class ParseEnvParsingError(Exception):
    pass


class PlaceholderConfigurationError(Exception):
    pass


class RefMustStartFromRoot(Exception):
    pass
