from __future__ import annotations

import re

from granular_configuration_language._utils import get_environment_variable
from granular_configuration_language.yaml.decorators import Tag, as_lazy, string_tag

ENV_PATTERN: re.Pattern[str] = re.compile(r"(\{\{\s*(?P<env_name>[A-Za-z0-9-_]+)\s*(?:\:(?P<default>.*?))?\}\})")


def load_env(env_name: str, default: str | None = None) -> str:
    return get_environment_variable(env_name, default)


@string_tag(Tag("!Env"), "Formatter")
@as_lazy
def tag(value: str) -> str:
    return ENV_PATTERN.sub(lambda x: load_env(**x.groupdict()), value)
