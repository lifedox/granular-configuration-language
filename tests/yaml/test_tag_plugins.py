from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from granular_configuration_language.exceptions import ErrorWhileLoadingTags
from granular_configuration_language.yaml._tags import handlers
from granular_configuration_language.yaml.decorators._tag_loader import load_tags
from granular_configuration_language.yaml.decorators._tag_set import TagSet


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


def test_csv() -> None:
    tags = handlers.get_subset("!Del", "!UUID", "!Merge", "!Sub")

    print(tags.csv())

    assert (
        tags.csv()
        == """\
category,tag,type,interpolates,lazy,returns,handler
Formatter,!Sub,str,full,,str,granular_configuration_language.yaml._tags._sub.handler
Manipulator,!Del,str,,NOT_LAZY,str,granular_configuration_language.yaml._tags._del.handler
Manipulator,!Merge,list[Any],,,Configuration,granular_configuration_language.yaml._tags._merge.handler
Typer,!UUID,str,reduced,,UUID,granular_configuration_language.yaml._tags._uuid.handler"""
    )


def test_json() -> None:
    tags = handlers.get_subset("!Del", "!UUID", "!Merge", "!Sub")

    print(tags.json())

    assert (
        tags.json()
        == """\
{
  "Formatter": {
    "!Sub": {
      "handler": "granular_configuration_language.yaml._tags._sub.handler",
      "interpolates": "full",
      "lazy": "",
      "returns": "str",
      "type": "str"
    }
  },
  "Manipulator": {
    "!Del": {
      "handler": "granular_configuration_language.yaml._tags._del.handler",
      "interpolates": "",
      "lazy": "NOT_LAZY",
      "returns": "str",
      "type": "str"
    },
    "!Merge": {
      "handler": "granular_configuration_language.yaml._tags._merge.handler",
      "interpolates": "",
      "lazy": "",
      "returns": "Configuration",
      "type": "list[Any]"
    }
  },
  "Typer": {
    "!UUID": {
      "handler": "granular_configuration_language.yaml._tags._uuid.handler",
      "interpolates": "reduced",
      "lazy": "",
      "returns": "UUID",
      "type": "str"
    }
  }
}"""
    )


def test_table() -> None:
    tags = handlers.get_subset("!Del", "!UUID", "!Merge", "!Sub")
    output = tags.table()

    print(output)

    if tags.can_table:
        assert (
            output
            == """\
category     tag     type       interpolates    lazy      returns        handler
-----------  ------  ---------  --------------  --------  -------------  ---------------------------------------------------------
Formatter    !Sub    str        full                      str            granular_configuration_language.yaml._tags._sub.handler
Manipulator  !Del    str                        NOT_LAZY  str            granular_configuration_language.yaml._tags._del.handler
Manipulator  !Merge  list[Any]                            Configuration  granular_configuration_language.yaml._tags._merge.handler
Typer        !UUID   str        reduced                   UUID           granular_configuration_language.yaml._tags._uuid.handler"""
        )


def test_table_missing() -> None:
    tags = handlers.get_subset("!Del", "!UUID", "!Merge", "!Sub")
    output = tags.table(_force_missing=True)

    print(output)

    assert (
        output
        == """\
The "table" option requires `tabulate` to be installed.
You can use the "printing" extra to install the needed dependencies"""
    )
