import typing as typ

from granular_configuration_language.yaml.decorators._tag_loader import load_tags

handlers: typ.Final = load_tags()
