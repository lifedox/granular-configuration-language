import typing as typ

from granular_configuration.yaml_handler.yaml_tags import del_, env, func_and_class, parse_env, placeholder, sub

handlers: typ.Final = (
    del_.handler,
    env.handler,
    func_and_class.class_handler,
    func_and_class.func_handler,
    parse_env.handler,
    placeholder.handler,
    sub.handler,
)
