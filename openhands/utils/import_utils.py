import importlib


def import_from(qual_name: str):
    parts = qual_name.split('.')
    module_name = '.'.join(parts[:-1])
    module = importlib.import_module(module_name)
    result = getattr(module, parts[-1])
    return result
