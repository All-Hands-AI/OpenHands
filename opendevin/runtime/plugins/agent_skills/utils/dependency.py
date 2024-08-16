import importlib


def import_functions(package: str, function_names: list[str]) -> None:
    for name in function_names:
        # import the module containing the function
        module = importlib.import_module(f'.{name}', package)
        # add the function to the globals
        globals()[name] = getattr(module, name)
