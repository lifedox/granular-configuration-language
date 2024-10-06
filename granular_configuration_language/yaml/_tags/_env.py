import re
import typing as typ

from granular_configuration_language._utils import get_environment_variable
from granular_configuration_language.yaml.decorators import Tag, as_lazy, string_tag

ENV_PATTERN: typ.Pattern[str] = re.compile(r"(\{\{\s*(?P<env_name>[A-Za-z0-9-_]+)\s*(?:\:(?P<default>.*?))?\}\})")


def load_env(env_name: str, default: typ.Optional[str] = None) -> str:
    return get_environment_variable(env_name, default)


@string_tag(Tag("!Env"))
@as_lazy
def handler(value: str) -> str:
    return ENV_PATTERN.sub(lambda x: load_env(**x.groupdict()), value)
