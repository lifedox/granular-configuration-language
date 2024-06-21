import os
import typing as typ

from granular_configuration._yaml_classes import _OPH, LazyRoot
from granular_configuration.exceptions import ParseEnvError
from granular_configuration.yaml_handler.decorators import (
    LazyEval,
    Root,
    StateOptions,
    StringOrTwopleType,
    make_lazy_root_with_state,
    string_or_twople_tag,
)


def parse_env(obj_pair_hook: _OPH, root: Root, env_var: str, *default: typ.Any) -> typ.Any:
    from granular_configuration.yaml_handler import loads

    env_var = str(env_var)
    env_missing = env_var not in os.environ

    if env_missing and (len(default) > 0):
        return default[0]
    elif env_missing:
        raise KeyError(env_var)
    else:
        try:
            lazy_root = LazyRoot()
            lazy_root._set_root(root)
            value = loads(os.environ[env_var], obj_pairs_hook=obj_pair_hook, lazy_root=lazy_root)
        except Exception as e:
            raise ParseEnvError("Error while parsing Environment Variable ({}): {}".format(env_var, e))
        if isinstance(value, LazyEval):
            return value.run()
        else:
            return value


@string_or_twople_tag("!ParseEnv")
@make_lazy_root_with_state
def handler(value: StringOrTwopleType, options: StateOptions, root: Root) -> typ.Any:
    if isinstance(value, str):
        return parse_env(options.obj_pairs_func, root, value)
    else:
        return parse_env(options.obj_pairs_func, root, *value)
