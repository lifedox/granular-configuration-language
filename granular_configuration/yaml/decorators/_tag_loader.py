import importlib
import inspect
import typing as typ

from granular_configuration.yaml.decorators._decorators import TagConstructor


def is_TagConstructor(obj: typ.Any) -> typ.TypeGuard[TagConstructor]:
    return isinstance(obj, TagConstructor)


def get_tags(module_name: str) -> typ.Iterator[TagConstructor]:
    module = importlib.import_module(module_name)
    for _, member in inspect.getmembers(module, is_TagConstructor):
        yield member
