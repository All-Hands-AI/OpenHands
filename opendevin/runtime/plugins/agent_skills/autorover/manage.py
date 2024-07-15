import os
from pathlib import Path

from search.search_manage import SearchManager

if __package__ is None or __package__ == '':
    from autorover.manage import *
else:
    from .autorover.manage import *

class ProjectApiManager:
    def __init__(self, project_path: str):
        # build search manager
        self.search_manager = SearchManager(project_path)

    # not a search API - just to get full class definition when bug_location only specifies a class
    def get_class_full_snippet(self, class_name: str):
        return self.search_manager.get_class_full_snippet(class_name)

    def search_class(self, class_name: str) -> tuple[str, str, bool]:
        """Search for a class in the codebase.

        Only the signature of the class is returned. The class signature
        includes class name, base classes, and signatures for all of its methods/properties.

        Args:
            class_name (string): Name of the class to search for.

        Returns:
            string: the class signature in string if success;
                    an error message if the class cannot be found.
            string: a message summarizing the method.
        """
        return self.search_manager.search_class(class_name)

    def search_class_in_file(
        self, class_name: str, file_name: str
    ) -> tuple[str, str, bool]:
        """Search for a class in a given file.

        Returns the actual code of the entire class definition.

        Args:
            class_name (string): Name of the class to search for.
            file_name (string): The file to search in. Must be a valid python file name.

        Returns:
            part 1 - the searched class code or error message.
            part 2 - summary of the tool call.
        """
        return self.search_manager.search_class_in_file(class_name, file_name)

    def search_method_in_file(
        self, method_name: str, file_name: str
    ) -> tuple[str, str, bool]:
        """Search for a method in a given file.

        Returns the actual code of the method.

        Args:
            method_name (string): Name of the method to search for.
            file_name (string): The file to search in. Must be a valid python file name.

        Returns:
            part 1 - the searched code or error message.
            part 2 - summary of the tool call.
        """
        return self.search_manager.search_method_in_file(method_name, file_name)

    def search_method_in_class(
        self, method_name: str, class_name: str
    ) -> tuple[str, str, bool]:
        """Search for a method in a given class.

        Returns the actual code of the method.

        Args:
            method_name (string): Name of the method to search for.
            class_name (string): Consider only methods in this class.

        Returns:
            part 1 - the searched code or error message.
            part 2 - summary of the tool call.
        """
        return self.search_manager.search_method_in_class(method_name, class_name)

    def search_method(self, method_name: str) -> tuple[str, str, bool]:
        """Search for a method in the entire codebase.

        Returns the actual code of the method.

        Args:
            method_name (string): Name of the method to search for.

        Returns:
            part 1 - the searched code or error message.
            part 2 - summary of the tool call.
        """
        return self.search_manager.search_method(method_name)

    def search_code(self, code_str: str) -> tuple[str, str, bool]:
        """Search for a code snippet in the entire codebase.

        Returns the method that contains the code snippet, if it is found inside a file.
        Otherwise, returns the region of code surrounding it.

        Args:
            code_str (string): The code snippet to search for.

        Returns:
            The region of code containing the searched code string.
        """
        return self.search_manager.search_code(code_str)

    def search_code_in_file(
        self, code_str: str, file_name: str
    ) -> tuple[str, str, bool]:
        """Search for a code snippet in a given file file.

        Returns the entire method that contains the code snippet.

        Args:
            code_str (string): The code snippet to search for.
            file_name (string): The file to search in. Must be a valid python file name in the project.

        Returns:
            The method code that contains the searched code string.
        """
        return self.search_manager.search_code_in_file(code_str, file_name)