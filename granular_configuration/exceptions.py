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
