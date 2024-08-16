from types import ModuleType


def import_functions(
    module: ModuleType, function_names: list[str], target_globals: dict
) -> None:
    for name in function_names:
        if hasattr(module, name):
            target_globals[name] = getattr(module, name)
        else:
            raise ValueError(f'Function {name} not found in {module.__name__}')
