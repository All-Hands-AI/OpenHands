from types import ModuleType
from typing import Dict, List


def import_functions(
    module: ModuleType, function_names: List[str], target_globals: Dict[str, object]
) -> None:
    for name in function_names:
        if hasattr(module, name):
            target_globals[name] = getattr(module, name)
        else:
            raise ValueError(f'Function {name} not found in {module.__name__}')
