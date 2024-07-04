from collections import defaultdict, namedtuple
from collections.abc import MutableMapping

if __package__ is None or __package__ == '':
    from utils import (
        SearchResult,
        find_python_files,
        get_class_signature,
        parse_python_file,
    )
else:
    from .utils import (
        SearchResult,
        find_python_files,
        get_class_signature,
        parse_python_file,
    )


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

RESULT_SHOW_LIMIT = 3


class SearchManager:
    def __init__(self, project_path) -> None:
        self.project_path = project_path
        # list of all files ending with .py, which are likely not test files
        # These are all ABSOLUTE paths.
        self.parsed_files: list[str] = []

        # for file name in the indexes, assume they are absolute path
        # class name -> [(file_name, line_range)]
        self.class_index: ClassIndexType = {}

        # {class_name -> {func_name -> [(file_name, line_range)]}}
        # inner dict is a list, since we can have (1) overloading func names,
        # and (2) multiple classes with the same name, having the same method
        self.class_func_index: ClassFuncIndexType = {}

        # function name -> [(file_name, line_range)]
        self.function_index: FuncIndexType = {}
        self._build_index()

    def search_class(self, class_name):
        # initialize them to error case
        summary = f'Class {class_name} did not appear in the codebase.'
        tool_result = f'Could not find class {class_name} in the codebase.'

        if class_name not in self.class_index:
            return tool_result, summary, None

        search_res: list[SearchResult] = []
        for fname, _ in self.class_index[class_name]:
            # there are some classes; we return their signatures
            code = get_class_signature(fname, class_name)
            res = SearchResult(fname, class_name, None, code)
            search_res.append(res)

        if not search_res:
            # this should not happen, but just in case
            return tool_result, summary, False

        # the good path
        # for all the searched result, append them and form the final result
        tool_result = f'Found {len(search_res)} classes with name {class_name} in the codebase:\n\n'
        if len(search_res) > RESULT_SHOW_LIMIT:
            tool_result += 'They appeared in the following files:\n'
            tool_result += SearchResult.collapse_to_file_level(
                search_res, self.project_path
            )
        else:
            for idx, res in enumerate(search_res):
                res_str = res.to_tagged_str(self.project_path)
                tool_result += f'- Search result {idx + 1}:\n```\n{res_str}\n```\n'
        summary = f'The tool returned information about class `{class_name}`.'
        return tool_result, summary, True

    def _build_index(self):
        """
        With all source code of the project, build two indexes:
            1. From class name to (source file, start line, end line)
            2. From function name to (source file, start line, end line)
        Since there can be two classes/functions with the same name, the mapping
        value is a list of tuples.
        This is for fast lookup whenever we receive a query.
        """
        self._update_indices(*self._build_python_index())

    def _update_indices(
        self,
        class_index: ClassIndexType,
        class_func_index: ClassFuncIndexType,
        func_index: FuncIndexType,
        parsed_files: list[str],
    ):
        self.class_index.update(class_index)
        self.class_func_index.update(class_func_index)
        self.function_index.update(func_index)
        self.parsed_files.extend(parsed_files)

    def _build_python_index(self):
        class_index: ClassIndexType = defaultdict(list)
        class_func_index: ClassFuncIndexType = defaultdict(lambda: defaultdict(list))
        function_index: FuncIndexType = defaultdict(list)

        py_files = find_python_files(self.project_path)
        # holds the parsable subset of all py files
        parsed_py_files = []
        for py_file in py_files:
            file_info = parse_python_file(py_file)
            if file_info is None:
                # parsing of this file failed
                continue

            parsed_py_files.append(py_file)
            # extract from file info, and form search index
            classes, class_to_funcs, top_level_funcs = file_info

            # (1) build class index
            for c, start, end in classes:
                class_index[c].append((py_file, LineRange(start, end)))

            # (2) build class-function index
            for c, class_funcs in class_to_funcs.items():
                for f, start, end in class_funcs:
                    class_func_index[c][f].append((py_file, LineRange(start, end)))

            # (3) build (top-level) function index
            for f, start, end in top_level_funcs:
                function_index[f].append((py_file, LineRange(start, end)))

        return class_index, class_func_index, function_index, parsed_py_files


if __name__ == '__main__':
    import pprint

    # for testing
    sm = SearchManager('.')
    pprint.pprint(sm.search_class('SearchResult'))
