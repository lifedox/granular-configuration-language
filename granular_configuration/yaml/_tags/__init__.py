import typing as typ

from granular_configuration.yaml._tags import (
    _date,
    _del,
    _env,
    _func_and_class,
    _mask,
    _merge,
    _parse_env,
    _parse_file,
    _placeholder,
    _ref,
    _sub,
    _uuid,
)

handlers: typ.Final = frozenset(
    (
        _date.date_handler,
        _date.datetime_handler,
        _del.handler,
        _env.handler,
        _func_and_class.class_handler,
        _func_and_class.func_handler,
        _mask.handler,
        _merge.handler,
        _parse_env.handler,
        _parse_env.handler_safe,
        _parse_file.handler,
        _parse_file.handler_optional,
        _placeholder.handler,
        _ref.handler,
        _sub.handler,
        _uuid.handler,
    )
)
