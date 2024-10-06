from granular_configuration_language.yaml import Placeholder, loads


def test_placeholder_value_and_message() -> None:
    placeholder = loads("!Placeholder value")

    assert isinstance(
        placeholder, Placeholder
    ), f"Placeholder isn't type Placeholder: `{placeholder.__class__.__name__}` {repr(placeholder)}"
    assert str(placeholder) == "value"
