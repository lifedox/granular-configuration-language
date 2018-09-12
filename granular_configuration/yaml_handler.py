from __future__ import print_function
import yaml
import importlib
import os
import re
import sys
from yaml import ScalarNode, MappingNode, SafeLoader
from functools import partial
from collections import MutableMapping, deque

consume = partial(deque, maxlen=0)

ENV_PATTERN = re.compile(r"(\{\{\s*(?P<env_name>[A-Za-z0-9-_]+)\s*(?:\:(?P<default>.*?))?\}\})")


class Placeholder(object):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return str(self.message)


class LazyEval(object):
    def __init__(self, value):
        assert callable(value)
        self.value = value

    def run(self):
        return self.value()


def load_env(env_name, default=None):
    if default is None:
        return os.environ[env_name]
    else:
        return os.getenv(env_name, default)


def add_cwd_to_path():
    cwd = os.getcwd()
    if sys.path[0] != cwd:
        sys.path.insert(0, cwd)


def get_func(func_path):
    add_cwd_to_path()
    mod_name, func = func_path.rsplit(".", 1)
    try:
        return getattr(importlib.import_module(mod_name), func)
    except (ImportError, AttributeError):
        raise ValueError("Could not load {}".format(func_path))


def handle_env(loader, node):
    if isinstance(node, ScalarNode):
        value = loader.construct_scalar(node)
        return LazyEval(lambda: ENV_PATTERN.sub(lambda x: load_env(**x.groupdict()), value))
    else:
        raise ValueError("Only strings are supported by !Env")


def handle_placeholder(loader, node):
    if isinstance(node, ScalarNode):
        value = loader.construct_scalar(node)
        return Placeholder(value)
    else:
        raise ValueError("Only strings are supported by !Placeholder")


def handle_class(value):
    class_type = get_func(value)
    try:
        if not issubclass(class_type, object):
            raise ValueError("Classes loaded by !Class must subclass object")  # pragma: no cover
        else:
            return class_type
    except TypeError:
        raise ValueError("Classes loaded by !Class must subclass object")


def handle_func(value):
    func = get_func(value)
    if not callable(func):
        raise ValueError("Functions loaded by !Func must be callable")
    else:
        return func


def string_check(func, loader, node):
    if isinstance(node, ScalarNode):
        return LazyEval(lambda: func(loader.construct_scalar(node)))
    else:
        raise ValueError("Only strings are supported by !{}".format(node.tag))


def construct_mapping(cls, loader, node):
    node.value = [pair for pair in node.value if pair[1].tag != "!Del"]
    loader.flatten_mapping(node)
    return cls(loader.construct_pairs(node, deep=True))


def loads(yaml_str, obj_pairs_hook=None):
    class ExtendSafeLoader(SafeLoader):  # pylint: disable=too-many-ancestors
        pass

    if obj_pairs_hook and issubclass(obj_pairs_hook, MutableMapping):
        ExtendSafeLoader.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, partial(construct_mapping, obj_pairs_hook)
        )

    ExtendSafeLoader.add_constructor("!Env", handle_env)
    ExtendSafeLoader.add_constructor("!Func", partial(string_check, handle_func))
    ExtendSafeLoader.add_constructor("!Class", partial(string_check, handle_class))
    ExtendSafeLoader.add_constructor("!Placeholder", handle_placeholder)

    return yaml.load(yaml_str, Loader=ExtendSafeLoader)  # nosec  # ExtendSafeLoader is a subclass of SafeLoader
