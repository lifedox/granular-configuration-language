import os
import re
import typing as typ

from granular_configuration.yaml.classes import Root
from granular_configuration.yaml.decorators import Tag, as_lazy_with_root, string_tag
from granular_configuration.yaml.ytags.ref import resolve_json_ref

SUB_PATTERN: typ.Pattern[str] = re.compile(r"(\$\{(?P<contents>.*?)\})")


def load_sub(root: Root, *, contents: str) -> str:
    if contents.startswith("$") or contents.startswith("/"):
        value = resolve_json_ref(contents, root)
        if isinstance(value, str):
            return value
        elif isinstance(value, (typ.Mapping, typ.Sequence)):
            return repr(value)
        else:
            return str(value)
    else:
        env_params = contents.split(":-", maxsplit=1)
        if len(env_params) > 1:
            return os.getenv(env_params[0], env_params[1])
        else:
            return os.environ[env_params[0]]


def interpolate(value: str, root: Root) -> str:
    return SUB_PATTERN.sub(lambda x: load_sub(root, **x.groupdict()), value)


@string_tag(Tag("!Sub"))
@as_lazy_with_root
def handler(value: str, root: Root) -> str:
    return interpolate(value, root)
