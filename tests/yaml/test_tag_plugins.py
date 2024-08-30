import typing as typ

import pytest

from granular_configuration.exceptions import ErrorWhileLoadingTags
from granular_configuration.yaml._tags import handlers
from granular_configuration.yaml.decorators._tag_loader import TagConstructor, TagSet, load_tags


def test_singletonness() -> None:
    assert tuple(load_tags()) == tuple(load_tags())


def test_disabling_official_extra_tags_removes_Func_and_Class() -> None:
    assert load_tags().has_tags("!Func", "!Class")
    assert load_tags(disable_plugin=("official_extra",)).does_not_have_tags("!Func", "!Class")


def test_disabling_tags_removes_those_tags() -> None:
    assert load_tags().has_tags("!Func", "!Class")
    assert load_tags(disable_tag=("!Func", "!Class")).does_not_have_tags("!Func", "!Class")


def test_trying_to_override_a_tag_errors() -> None:
    tag = next(iter(handlers))
    with pytest.raises(ErrorWhileLoadingTags):
        TagSet((tag, tag))


def test_pretty() -> None:
    select = ("!Del", "!UUID", "!Merge", "!Sub")

    def subset(tags: typ.Iterable[TagConstructor]) -> typ.Iterator[TagConstructor]:
        for tag in tags:
            if tag.tag in select:
                yield tag

    tags = TagSet(subset(handlers))

    assert (
        tags.pretty()
        == """\
TagSet{
  '!Del': 'str [NOT-LAZY] (granular_configuration.yaml._tags._del.handler)',
  '!Merge': 'list[Any] (granular_configuration.yaml._tags._merge.handler)',
  '!Sub': 'str [interpolates] (granular_configuration.yaml._tags._sub.handler)',
  '!UUID': 'str [interpolates-reduced] (granular_configuration.yaml._tags._uuid.handler)'
}"""
    )
