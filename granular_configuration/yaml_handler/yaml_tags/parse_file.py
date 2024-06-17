import typing as typ

from granular_configuration.yaml_handler.decorators import StateHolder, make_lazy_with_state, string_only_tag


@string_only_tag("!ParseFile")
@make_lazy_with_state
def handler(value: str, state: StateHolder) -> typ.Any:
    from granular_configuration._load import load_file

    return load_file(
        state.file_relative_path / value, obj_pairs_hook=state.obj_pairs_func, lazy_root=state.lazy_root_obj
    )
