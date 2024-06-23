import operator as op
import os
import re
import typing as typ

import jsonpath

from granular_configuration.exceptions import JSONPathOnlyWorksOnMappings
from granular_configuration.yaml.decorators import LazyEval, Root, Tag, make_lazy_root, string_tag
from granular_configuration.yaml.ytags.merge import handler as merge_handler

SUB_PATTERN: typ.Pattern[str] = re.compile(r"(\$\{(?P<contents>.*?)\})")

merge_tag = getattr(merge_handler, "_yaml_tag")


def load_sub(root: Root, *, contents: str) -> str:
    if contents.startswith("$"):
        if isinstance(root, LazyEval) and root.tag == merge_tag:
            raise RecursionError(
                f"JSONPath `{contents}` attempted recursion. Please check your configuration for a self-referencing loop."
            )
        elif not isinstance(root, typ.Mapping):
            raise JSONPathOnlyWorksOnMappings(f"JSONPath `{contents}` was tried on `{repr(root)}`")

        try:
            result = list(map(op.attrgetter("value"), jsonpath.finditer(contents, root)))
            if len(result) == 1:
                return str(result[0])
            elif len(result) == 0:
                raise KeyError(contents)
            else:
                return repr(result)
        except RecursionError:
            raise RecursionError(
                (
                    f"JSONPath `{contents}` caused a recursion error. Please check your configuration for a self-referencing loop."
                )
            ) from None
    else:
        env_params = contents.split(":-", maxsplit=1)
        if len(env_params) > 1:
            return os.getenv(env_params[0], env_params[1])
        else:
            return os.environ[env_params[0]]


def interpolate(value: str, root: Root) -> str:
    return SUB_PATTERN.sub(lambda x: load_sub(root, **x.groupdict()), value)


@string_tag(Tag("!Sub"))
@make_lazy_root
def handler(value: str, root: Root) -> str:
    return interpolate(value, root)
