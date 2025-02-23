from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from granular_configuration_language.exceptions import ErrorWhileLoadingTags
from granular_configuration_language.yaml._tags import handlers
from granular_configuration_language.yaml.decorators._tag_loader import load_tags
from granular_configuration_language.yaml.decorators._tag_set import TagSet
from granular_configuration_language.yaml.decorators._viewer import AvailablePlugins, AvailableTags, can_table


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


def test_available_tags_csv() -> None:
    tags = handlers.get_subset("!Del", "!UUID", "!Merge", "!Sub")
    output = AvailableTags(tags).csv()

    print(output)

    assert (
        output
        == """\
category,tag,type,interpolates,lazy,returns
Formatter,!Sub,str,full,,str
Manipulator,!Del,str,,NOT_LAZY,str
Manipulator,!Merge,list[Any],,,Configuration
Typer,!UUID,str,reduced,,UUID"""
    )


def test_available_tags_json() -> None:
    tags = handlers.get_subset("!Del", "!UUID", "!Merge", "!Sub")
    output = AvailableTags(tags).json()

    print(output)

    assert (
        output
        == """\
{
  "Formatter": {
    "!Sub": {
      "interpolates": "full",
      "lazy": "",
      "returns": "str",
      "type": "str"
    }
  },
  "Manipulator": {
    "!Del": {
      "interpolates": "",
      "lazy": "NOT_LAZY",
      "returns": "str",
      "type": "str"
    },
    "!Merge": {
      "interpolates": "",
      "lazy": "",
      "returns": "Configuration",
      "type": "list[Any]"
    }
  },
  "Typer": {
    "!UUID": {
      "interpolates": "reduced",
      "lazy": "",
      "returns": "UUID",
      "type": "str"
    }
  }
}"""
    )


def test_available_tags_table() -> None:
    tags = handlers.get_subset("!Del", "!UUID", "!Merge", "!Sub")
    output = AvailableTags(tags).table()

    print(output)

    if can_table:
        assert (
            output
            == """\
category     tag     type       interpolates    lazy      returns
-----------  ------  ---------  --------------  --------  -------------
Formatter    !Sub    str        full                      str
Manipulator  !Del    str                        NOT_LAZY  str
Manipulator  !Merge  list[Any]                            Configuration
Typer        !UUID   str        reduced                   UUID"""
        )


def test_table_missing() -> None:
    tags = handlers.get_subset("!Del", "!UUID", "!Merge", "!Sub")
    output = AvailableTags(tags).table(_force_missing=True)

    print(output)

    assert (
        output
        == """\
The "table" option requires `tabulate` to be installed.
You can use the "printing" extra to install the needed dependencies"""
    )


def test_available_plugins_csv() -> None:
    tags = handlers.get_subset("!Func", "!UUID", "!Merge", "!Mask")
    output = AvailablePlugins(tags).csv()

    print(output)

    assert (
        output
        == """\
plugin,category,tag,handler
<gcl-built-in>,Manipulator,!Merge,granular_configuration_language.yaml._tags._merge.handler
<gcl-built-in>,Typer,!Mask,granular_configuration_language.yaml._tags._mask.handler
<gcl-built-in>,Typer,!UUID,granular_configuration_language.yaml._tags._uuid.handler
official_extra,Typer,!Func,granular_configuration_language.yaml._tags.func_and_class.func_handler"""
    )


def test_available_plugins_json() -> None:
    tags = handlers.get_subset("!Func", "!UUID", "!Merge", "!Mask")
    output = AvailablePlugins(tags).json()

    print(output)

    assert (
        output
        == """\
{
  "<gcl-built-in>": {
    "Manipulator": {
      "!Merge": {
        "handler": "granular_configuration_language.yaml._tags._merge.handler",
        "plugin": "<gcl-built-in>"
      }
    },
    "Typer": {
      "!Mask": {
        "handler": "granular_configuration_language.yaml._tags._mask.handler",
        "plugin": "<gcl-built-in>"
      },
      "!UUID": {
        "handler": "granular_configuration_language.yaml._tags._uuid.handler",
        "plugin": "<gcl-built-in>"
      }
    }
  },
  "official_extra": {
    "Typer": {
      "!Func": {
        "handler": "granular_configuration_language.yaml._tags.func_and_class.func_handler",
        "plugin": "official_extra"
      }
    }
  }
}"""
    )


def test_available_plugins_table() -> None:
    tags = handlers.get_subset("!Func", "!UUID", "!Merge", "!Mask")
    output = AvailablePlugins(tags).table()

    print(output)

    if can_table:
        assert (
            output
            == """\
plugin          category     tag     handler
--------------  -----------  ------  ----------------------------------------------------------------------
<gcl-built-in>  Manipulator  !Merge  granular_configuration_language.yaml._tags._merge.handler
<gcl-built-in>  Typer        !Mask   granular_configuration_language.yaml._tags._mask.handler
<gcl-built-in>  Typer        !UUID   granular_configuration_language.yaml._tags._uuid.handler
official_extra  Typer        !Func   granular_configuration_language.yaml._tags.func_and_class.func_handler"""
        )
