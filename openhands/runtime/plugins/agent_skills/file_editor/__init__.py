"""This file imports a global singleton of the `EditTool` class as well as raw functions that expose
its __call__.
The implementation of the `EditTool` class can be found at: https://github.com/All-Hands-AI/openhands-aci/.
"""

from openhands_aci.editor import file_editor as _file_editor


def file_editor(*args, **kwargs):
    # Override enable_linting to True by default
    kwargs['enable_linting'] = True
    return _file_editor(*args, **kwargs)


__all__ = ['file_editor']
