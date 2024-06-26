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


class ParseEnvError(Exception):
    pass


class ParseEnvEnvironmentVaribleNotFound(KeyError):
    pass


class JSONPathOnlyWorksOnMappings(Exception):
    pass


class JSONPathMustStartFromRoot(Exception):
    pass


class JSONPathMustPointToASingleValue(KeyError):
    pass


class JSONPathQueryMatchFailed(KeyError):
    pass


class IniUnsupportedError(Exception):
    pass
