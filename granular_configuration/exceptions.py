class PlaceholderConfigurationError(Exception):
    pass


class IniKeyExistAsANonMapping(Exception):
    pass


class IniTryToReplaceExistingKey(Exception):
    pass


class GetConfigReadBeforeSetException(Exception):
    pass


class InvalidBasePathException(KeyError):
    pass


class ParseEnvParsingError(Exception):
    pass


class EnvironmentVaribleNotFound(KeyError):
    pass


class JSONPathOnlyWorksOnMappings(Exception):
    pass


class JSONPathMustStartFromRoot(Exception):
    pass


class JSONPathQueryFailed(KeyError):
    pass


class JSONPointerQueryFailed(KeyError):
    pass


class IniUnsupportedError(Exception):
    pass


class IsNotCallable(ValueError):
    pass


class IsNotAClass(ValueError):
    pass


class DoesNotExist(ValueError):
    pass


class ErrorWhileLoadingFileOccurred(ValueError):
    pass


class ErrorWhileLoadingTags(Exception):
    pass
