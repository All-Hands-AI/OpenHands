"""
Utility functions for RepoGraph.
Adapted from https://github.com/ozyyshr/RepoGraph
"""

import os
import ast
from typing import Dict, List, Tuple, Any, Optional, Set

def create_structure(directory_path: str) -> Dict[str, Any]:
    """Create the structure of the repository directory by parsing Python files.
    
    Args:
        directory_path: Path to the repository directory
        
    Returns:
        Dictionary representing the repository structure
    """
    structure = {}

    for root, _, files in os.walk(directory_path):
        repo_name = os.path.basename(directory_path)
        relative_root = os.path.relpath(root, directory_path)
        if relative_root == ".":
            relative_root = repo_name
        curr_struct = structure
        for part in relative_root.split(os.sep):
            if part not in curr_struct:
                curr_struct[part] = {}
            curr_struct = curr_struct[part]
        for file_name in files:
            if file_name.endswith(".py"):
                file_path = os.path.join(root, file_name)
                class_info, function_names, file_lines = parse_python_file(file_path)
                curr_struct[file_name] = {
                    "classes": class_info,
                    "functions": function_names,
                    "text": file_lines,
                }
            else:
                curr_struct[file_name] = {}

    return structure

def parse_python_file(file_path: str, file_content: Optional[str] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    """Parse a Python file to extract class and function definitions with their line numbers.
    
    Args:
        file_path: Path to the Python file
        file_content: Optional pre-loaded file content
        
    Returns:
        Tuple containing:
        - List of class information dictionaries
        - List of function information dictionaries
        - List of file lines
    """
    if file_content is None:
        try:
            with open(file_path, "r") as file:
                file_content = file.read()
                parsed_data = ast.parse(file_content)
        except Exception as e:
            print(f"Error in file {file_path}: {e}")
            return [], [], []
    else:
        try:
            parsed_data = ast.parse(file_content)
        except Exception as e:
            print(f"Error in file {file_path}: {e}")
            return [], [], []

    class_info = []
    function_names = []
    class_methods: Set[str] = set()

    for node in ast.walk(parsed_data):
        if isinstance(node, ast.ClassDef):
            methods = []
            for n in node.body:
                if isinstance(n, ast.FunctionDef):
                    methods.append(
                        {
                            "name": n.name,
                            "start_line": n.lineno,
                            "end_line": n.end_lineno,
                            "text": file_content.splitlines()[
                                n.lineno - 1 : n.end_lineno
                            ],
                        }
                    )
                    class_methods.add(n.name)
            class_info.append(
                {
                    "name": node.name,
                    "start_line": node.lineno,
                    "end_line": node.end_lineno,
                    "text": file_content.splitlines()[
                        node.lineno - 1 : node.end_lineno
                    ],
                    "methods": methods,
                }
            )
        elif isinstance(node, ast.FunctionDef) and not isinstance(
            node, ast.AsyncFunctionDef
        ):
            if node.name not in class_methods:
                function_names.append(
                    {
                        "name": node.name,
                        "start_line": node.lineno,
                        "end_line": node.end_lineno,
                        "text": file_content.splitlines()[
                            node.lineno - 1 : node.end_lineno
                        ],
                    }
                )

    return class_info, function_names, file_content.splitlines()