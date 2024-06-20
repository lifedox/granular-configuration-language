import typing as typ

from granular_configuration.yaml_handler.decorators import CallableConstructorType
from granular_configuration.yaml_handler.yaml_tags import (
    del_,
    env,
    func_and_class,
    merge,
    parse_env,
    parse_file,
    placeholder,
    sub,
)

handlers: typ.Final[typ.Sequence[CallableConstructorType]] = (
    del_.handler,
    env.handler,
    func_and_class.class_handler,
    func_and_class.func_handler,
    merge.handler,
    parse_env.handler,
    parse_file.handler,
    parse_file.handler_optional,
    placeholder.handler,
    sub.handler,
)
