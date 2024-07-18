from collections import namedtuple
from collections.abc import MutableMapping

LineRange = namedtuple('LineRange', ['start', 'end'])
ClassIndexType = MutableMapping[
    str, list[tuple[str, LineRange]]
]  # class_name -> [(file_path, line_range)]
ClassFuncIndexType = MutableMapping[
    str, MutableMapping[str, list[tuple[str, LineRange]]]
]  # class_name -> function_name -> [(file_path, line_range)]
FuncIndexType = MutableMapping[
    str, list[tuple[str, LineRange]]
]  # function_name -> [(file_path, line_range)]
