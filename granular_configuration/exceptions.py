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


class JSONPathOnlyWorksOnMappings(Exception):
    pass


class IniUnsupported(Exception):
    pass
