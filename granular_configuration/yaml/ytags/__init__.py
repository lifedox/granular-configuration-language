import typing as typ

from granular_configuration.yaml.decorators import CallableConstructorType
from granular_configuration.yaml.ytags import (
    del_,
    env,
    func_and_class,
    mask,
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
    mask.handler,
    merge.handler,
    parse_env.handler,
    parse_env.handler_safe,
    parse_file.handler,
    parse_file.handler_optional,
    placeholder.handler,
    sub.handler,
)
