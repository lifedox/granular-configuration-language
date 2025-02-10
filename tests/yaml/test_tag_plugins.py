from __future__ import annotations

import collections.abc as tabc
import os
from unittest.mock import patch

import pytest

from granular_configuration_language.exceptions import ErrorWhileLoadingTags
from granular_configuration_language.yaml._tags import handlers
from granular_configuration_language.yaml.decorators._tag_loader import TagConstructor, TagSet, load_tags


def test_singletonness() -> None:
    assert tuple(load_tags()) == tuple(load_tags())


def test_disabling_official_extra_tags_removes_Func_and_Class() -> None:
    assert load_tags().has_tags("!Func", "!Class")
    assert load_tags(disable_plugins={"official_extra"}).does_not_have_tags("!Func", "!Class")

    with patch.dict(os.environ, values={"G_CONFIG_DISABLE_PLUGINS": ""}):
        assert load_tags().has_tags("!Func", "!Class")
    with patch.dict(os.environ, values={"G_CONFIG_DISABLE_PLUGINS": ","}):
        assert load_tags().has_tags("!Func", "!Class")

    with patch.dict(os.environ, values={"G_CONFIG_DISABLE_PLUGINS": "official_extra"}):
        assert load_tags().does_not_have_tags("!Func", "!Class")

    with patch.dict(os.environ, values={"G_CONFIG_DISABLE_PLUGINS": "official_extra,"}):
        assert load_tags().does_not_have_tags("!Func", "!Class")

    with patch.dict(os.environ, values={"G_CONFIG_DISABLE_PLUGINS": ",official_extra,"}):
        assert load_tags().does_not_have_tags("!Func", "!Class")

    with patch.dict(os.environ, values={"G_CONFIG_DISABLE_PLUGINS": "official_extra "}):
        assert load_tags().does_not_have_tags("!Func", "!Class")


def test_disabling_tags_removes_those_tags() -> None:
    assert load_tags().has_tags("!Func", "!Class")
    assert load_tags(disable_tags={"!Func", "!Class"}).does_not_have_tags("!Func", "!Class")

    with patch.dict(os.environ, values={"G_CONFIG_DISABLE_TAGS": ""}):
        assert load_tags().has_tags("!Func", "!Class")
    with patch.dict(os.environ, values={"G_CONFIG_DISABLE_TAGS": ","}):
        assert load_tags().has_tags("!Func", "!Class")

    with patch.dict(os.environ, values={"G_CONFIG_DISABLE_TAGS": "!Func,!Class"}):
        assert load_tags().does_not_have_tags("!Func", "!Class")

    with patch.dict(os.environ, values={"G_CONFIG_DISABLE_TAGS": "!Func,"}):
        assert load_tags().does_not_have_tags("!Func")
        assert load_tags().has_tags("!Class")

    with patch.dict(os.environ, values={"G_CONFIG_DISABLE_TAGS": ",!Func,!Class,"}):
        assert load_tags().does_not_have_tags("!Func", "!Class")

    with patch.dict(os.environ, values={"G_CONFIG_DISABLE_TAGS": "!Func, !Class "}):
        assert load_tags().does_not_have_tags("!Func", "!Class")


def test_trying_to_override_a_tag_errors() -> None:
    tag = next(iter(handlers))
    with pytest.raises(ErrorWhileLoadingTags):
        TagSet((tag, tag))


def test_pretty() -> None:
    select = ("!Del", "!UUID", "!Merge", "!Sub")

    def subset(tags: tabc.Iterable[TagConstructor]) -> tabc.Iterator[TagConstructor]:
        for tag in tags:
            if tag.tag in select:
                yield tag

    tags = TagSet(subset(handlers))

    print(tags.pretty())
    print("---")
    print(tags.pretty(as_json=True))

    assert (
        tags.pretty()
        == """\
TagSet{
  '!Del': 'str [NOT-LAZY] (granular_configuration_language.yaml._tags._del.handler) `str`',
  '!Merge': 'list[Any] (granular_configuration_language.yaml._tags._merge.handler) `Configuration`',
  '!Sub': 'str [interpolates] (granular_configuration_language.yaml._tags._sub.handler) `str`',
  '!UUID': 'str [interpolates-reduced] (granular_configuration_language.yaml._tags._uuid.handler) `UUID`'
}"""
    )
    assert (
        tags.pretty(as_json=True)
        == """\
TagSet{
  "!Del": {
    "input": "str",
    "notes": [
      "NOT-LAZY"
    ],
    "output": "'str'"
  },
  "!Merge": {
    "input": "list[Any]",
    "notes": [],
    "output": "'Configuration'"
  },
  "!Sub": {
    "input": "str",
    "notes": [
      "interpolates"
    ],
    "output": "'str'"
  },
  "!UUID": {
    "input": "str",
    "notes": [
      "interpolates-reduced"
    ],
    "output": "'UUID'"
  }
}"""
    )
