import os
import re
import typing as typ

from granular_configuration.yaml_handler.decorators import make_lazy, string_tag

ENV_PATTERN: typ.Pattern[str] = re.compile(r"(\{\{\s*(?P<env_name>[A-Za-z0-9-_]+)\s*(?:\:(?P<default>.*?))?\}\})")


def load_env(env_name: str, default: typ.Optional[str] = None) -> str:
    if default is None:
        return os.environ[env_name]
    else:
        return os.getenv(env_name, default)


@string_tag("!Env")
@make_lazy
def handler(value: str) -> str:
    return ENV_PATTERN.sub(lambda x: load_env(**x.groupdict()), value)
