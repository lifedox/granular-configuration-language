import re
import typing as typ

from granular_configuration._utils import get_environment_variable
from granular_configuration.yaml._tags._ref import resolve_json_ref
from granular_configuration.yaml.decorators import Root, Tag, as_lazy_with_root, string_tag

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
        return get_environment_variable(*contents.split(":-", maxsplit=1))


def interpolate(value: str, root: Root) -> str:
    return SUB_PATTERN.sub(lambda x: load_sub(root, **x.groupdict()), value)


@string_tag(Tag("!Sub"))
@as_lazy_with_root
def handler(value: str, root: Root) -> str:
    return interpolate(value, root)
