from collections import defaultdict, namedtuple
from collections.abc import MutableMapping

if __package__ is None or __package__ == '':
    from utils import (
        SearchResult,
        find_python_files,
        get_class_signature,
        get_code_snippets,
        parse_python_file,
    )
else:
    from .utils import (
        SearchResult,
        find_python_files,
        get_class_signature,
        get_code_snippets,
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

    def search_class_in_file(self, class_name, file_name: str) -> tuple[str, str, bool]:
        # (1) check whether we can get the file
        candidate_py_abs_paths = [f for f in self.parsed_files if f.endswith(file_name)]
        if not candidate_py_abs_paths:
            tool_output = f'Could not find file {file_name} in the codebase.'
            summary = tool_output
            return tool_output, summary, False

        # (2) search for this class in the entire code base (we do filtering later)
        if class_name not in self.class_index:
            tool_output = f'Could not find class {class_name} in the codebase.'
            summary = tool_output
            return tool_output, summary, False

        # (3) class is there, check whether it exists in the file specified.
        search_res: list[SearchResult] = []
        for fname, (start_line, end_line) in self.class_index[class_name]:
            if fname in candidate_py_abs_paths:
                class_code = get_code_snippets(fname, start_line, end_line)
                res = SearchResult(fname, class_name, None, class_code)
                search_res.append(res)

        if not search_res:
            tool_output = f'Could not find class {class_name} in file {file_name}.'
            summary = tool_output
            return tool_output, summary, False

        # good path; we have result, now just form a response
        tool_output = f'Found {len(search_res)} classes with name {class_name} in file {file_name}:\n\n'
        summary = tool_output
        for idx, res in enumerate(search_res):
            res_str = res.to_tagged_str(self.project_path)
            tool_output += f'- Search result {idx + 1}:\n```\n{res_str}\n```\n'
        return tool_output, summary, True

    def search_method(self, method_name: str) -> tuple[str, str, bool]:
        """
        Search for a method in the entire codebase.
        """
        search_res: list[SearchResult] = self._search_func_in_code_base(method_name)
        if not search_res:
            tool_output = f'Could not find method {method_name} in the codebase.'
            summary = tool_output
            return tool_output, summary, False

        tool_output = f'Found {len(search_res)} methods with name {method_name} in the codebase:\n\n'
        summary = tool_output

        if len(search_res) > RESULT_SHOW_LIMIT:
            tool_output += 'They appeared in the following files:\n'
            tool_output += SearchResult.collapse_to_file_level(
                search_res, self.project_path
            )
        else:
            for idx, res in enumerate(search_res):
                res_str = res.to_tagged_str(self.project_path)
                tool_output += f'- Search result {idx + 1}:\n```\n{res_str}\n```\n'

        return tool_output, summary, True

    def search_method_in_class(
        self, method_name: str, class_name: str
    ) -> tuple[str, str, bool]:
        if class_name not in self.class_index:
            tool_output = f'Could not find class {class_name} in the codebase.'
            summary = tool_output
            return tool_output, summary, False

        # has this class, check its methods
        search_res: list[SearchResult] = self._search_func_in_class(
            method_name, class_name
        )
        if not search_res:
            tool_output = f'Could not find method {method_name} in class {class_name}`.'
            summary = tool_output
            return tool_output, summary, False

        # found some methods, prepare the result
        tool_output = f'Found {len(search_res)} methods with name {method_name} in class {class_name}:\n\n'
        summary = tool_output

        # There can be multiple classes defined in multiple files, which contain the same method
        # still trim the result, just in case
        if len(search_res) > RESULT_SHOW_LIMIT:
            tool_output += f'Too many results, showing full code for {RESULT_SHOW_LIMIT} of them, and the rest just file names:\n'
        first_five = search_res[:RESULT_SHOW_LIMIT]
        for idx, res in enumerate(first_five):
            res_str = res.to_tagged_str(self.project_path)
            tool_output += f'- Search result {idx + 1}:\n```\n{res_str}\n```\n'
        # for the rest, collect the file names into a set
        if rest := search_res[RESULT_SHOW_LIMIT:]:
            tool_output += 'Other results are in these files:\n'
            tool_output += SearchResult.collapse_to_file_level(rest, self.project_path)
        return tool_output, summary, True

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

    def _search_func_in_code_base(self, function_name: str) -> list[SearchResult]:
        """
        Search for this function, from both top-level and all class definitions.
        """
        result: list[SearchResult] = []  # list of (file_name, func_code)
        # (1) search in top level
        top_level_res = self._search_top_level_func(function_name)
        class_res = self._search_func_in_all_classes(function_name)
        result.extend(top_level_res)
        result.extend(class_res)
        return result

    def _search_top_level_func(self, function_name: str) -> list[SearchResult]:
        """
        Search for top-level function name in the entire project.
        Args:
            function_name (str): Name of the function.
        Returns:
            The list of code snippets searched.
        """
        result: list[SearchResult] = []
        if function_name not in self.function_index:
            return result

        for fname, (start, end) in self.function_index[function_name]:
            func_code = get_code_snippets(fname, start, end)
            res = SearchResult(fname, None, function_name, func_code)
            result.append(res)
        return result

    def _search_func_in_all_classes(self, function_name: str) -> list[SearchResult]:
        """
        Search for the function name in all classes.
        Args:
            function_name (str): Name of the function.
        Returns:
            The list of code snippets searched.
        """
        result: list[SearchResult] = []
        for class_name in self.class_index:
            res = self._search_func_in_class(function_name, class_name)
            result.extend(res)
        return result

    def _search_func_in_class(
        self, function_name: str, class_name: str
    ) -> list[SearchResult]:
        """
        Search for the function name in the class.
        Args:
            function_name (str): Name of the function.
            class_name (str): Name of the class.
        Returns:
            The list of code snippets searched.
        """
        result: list[SearchResult] = []
        if class_name not in self.class_func_index:
            return result
        if function_name not in self.class_func_index[class_name]:
            return result
        for fname, (start, end) in self.class_func_index[class_name][function_name]:
            func_code = get_code_snippets(fname, start, end)
            res = SearchResult(fname, class_name, function_name, func_code)
            result.append(res)
        return result


if __name__ == '__main__':
    import pprint

    sm = SearchManager('.')
    # pprint.pprint(sm.search_class('SearchResult'))
    # pprint.pprint(sm.search_class_in_file('SearchManager', 'manager.py'))
    # pprint.pprint(sm.search_method('step'))
    pprint.pprint(sm.search_method_in_class('search_class', 'SearchManager'))
