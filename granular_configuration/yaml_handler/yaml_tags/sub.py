import operator as op
import os
import re
import typing as typ

import jsonpath

from granular_configuration.yaml_handler.decorators import Root, make_lazy_root, string_only_tag

SUB_PATTERN: typ.Pattern[str] = re.compile(r"(\$\{(?P<contents>.*?)\})")


def load_sub(root: typ.Any, *, contents: str) -> str:
    if contents.startswith("$"):
        result = list(map(op.attrgetter("value"), jsonpath.finditer(contents, root)))
        if len(result) == 1:
            return str(result[0])
        elif len(result) == 0:
            raise KeyError(contents)
        else:
            return repr(result)
    else:
        env_params = contents.split(":-", maxsplit=1)
        if len(env_params) > 1:
            return os.getenv(env_params[0], env_params[1])
        else:
            return os.environ[env_params[0]]


@string_only_tag("!Sub")
@make_lazy_root
def handler(value: str, root: Root) -> str:
    return SUB_PATTERN.sub(lambda x: load_sub(root, **x.groupdict()), value)
