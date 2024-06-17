import os
import typing as typ

from granular_configuration.exceptions import ParseEnvError
from granular_configuration.yaml_handler.classes import _OPH
from granular_configuration.yaml_handler.decorators import (
    LazyEval,
    StateHolder,
    StringOrTwopleType,
    make_lazy_with_state,
    string_or_twople_tag,
)


def parse_env(obj_pair_hook: _OPH, env_var: str, *default: typ.Any) -> typ.Any:
    from granular_configuration.yaml_handler import loads

    env_var = str(env_var)
    env_missing = env_var not in os.environ

    if env_missing and (len(default) > 0):
        return default[0]
    elif env_missing:
        raise KeyError(env_var)
    else:
        try:
            value = loads(os.environ[env_var], obj_pairs_hook=obj_pair_hook)
        except Exception as e:
            raise ParseEnvError("Error while parsing Environment Variable ({}): {}".format(env_var, e))
        if isinstance(value, LazyEval):
            return value.run()
        else:
            return value


@string_or_twople_tag("!ParseEnv")
@make_lazy_with_state
def handler(value: StringOrTwopleType, state: StateHolder) -> typ.Any:
    if isinstance(value, str):
        return parse_env(state.obj_pairs_func, value)
    else:
        return parse_env(state.obj_pairs_func, *value)
