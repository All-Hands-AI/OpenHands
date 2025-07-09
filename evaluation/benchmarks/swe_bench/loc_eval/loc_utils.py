import ast
import logging
import re
from dataclasses import dataclass
from typing import Any, Union

import pandas as pd
from datasets import load_dataset

from openhands.runtime.base import Runtime


@dataclass
class LocalizationInfo:
    """Container for ground-truth localization information"""

    instance_id: str  # SWE-Bench instance identifier
    files: list[str]  # List of modified files
    file_line_ranges: dict[
        str, list[tuple[int, int]]
    ]  # File -> [(start_line, end_line), ...]
    functions: dict[str, list[str]]  # File -> [function_names, ...]
    classes: dict[str, list[str]]  # File -> [class_names, ...]
    line_to_function: dict[str, dict[int, str]]  # File -> {line_num: function_name}
    line_to_class: dict[str, dict[int, str]]  # File -> {line_num: class_name}
    total_lines_changed: int
    total_files_changed: int
    hunks_per_file: dict[str, int]  # File -> number of hunks

    def to_dict(self) -> dict[str, Any]:
        """
        Convert LocalizationInfo to a dictionary for JSON serialization.

        Returns:
            Dictionary representation of the localization information
        """
        return {
            'instance_id': self.instance_id,
            'files': self.files,
            'file_line_ranges': {
                file: [[start, end] for start, end in ranges]
                for file, ranges in self.file_line_ranges.items()
            },
            'functions': self.functions,
            'classes': self.classes,
            'line_to_function': {
                file: {str(line): func for line, func in mapping.items()}
                for file, mapping in self.line_to_function.items()
            },
            'line_to_class': {
                file: {str(line): cls for line, cls in mapping.items()}
                for file, mapping in self.line_to_class.items()
            },
            'total_lines_changed': self.total_lines_changed,
            'total_files_changed': self.total_files_changed,
            'hunks_per_file': self.hunks_per_file,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'LocalizationInfo':
        """
        Create LocalizationInfo from a dictionary (for loading from JSON).

        Args:
            data: Dictionary containing localization information

        Returns:
            LocalizationInfo object
        """
        return cls(
            instance_id=data['instance_id'],
            files=data['files'],
            file_line_ranges={
                file: [(start, end) for start, end in ranges]
                for file, ranges in data['file_line_ranges'].items()
            },
            functions=data['functions'],
            classes=data['classes'],
            line_to_function={
                file: {int(line): func for line, func in mapping.items()}
                for file, mapping in data['line_to_function'].items()
            },
            line_to_class={
                file: {int(line): cls for line, cls in mapping.items()}
                for file, mapping in data['line_to_class'].items()
            },
            total_lines_changed=data['total_lines_changed'],
            total_files_changed=data['total_files_changed'],
            hunks_per_file=data['hunks_per_file'],
        )


class LocMeta:
    """
    SWE-Bench dataset loader and ground-truth localization parser.

    This class handles loading SWE-Bench datasets and extracting ground-truth
    localization information from patches for code localization evaluation.
    Works with both standalone Docker containers and OpenHands runtime.
    """

    def __init__(
        self,
        dataset_name: str = 'princeton-nlp/SWE-bench_Verified',
        split: str = 'test',
    ):
        """
        Initialize LocMeta with a SWE-Bench dataset.

        Args:
            dataset_name: HuggingFace dataset name (e.g., "princeton-nlp/SWE-bench_Verified")
        """
        self.dataset_name = dataset_name
        self.dataset = None
        self.split = split
        self.df = None
        self.instance_lookup = {}

        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Initialize dataset
        self._init_swe_dataset()

    def _init_swe_dataset(self) -> None:
        """
        Load and initialize the SWE-Bench dataset from HuggingFace.
        Converts to pandas DataFrame for easy manipulation.
        """
        try:
            self.logger.info(f'Loading dataset: {self.dataset_name}')

            # Load dataset from HuggingFace
            self.dataset = load_dataset(self.dataset_name, split=self.split)

            # Convert to pandas DataFrame
            self.df = pd.DataFrame(self.dataset)

            # Create lookup dictionary for fast instance access
            self.instance_lookup = {
                row['instance_id']: idx for idx, row in self.df.iterrows()
            }

            self.logger.info(f'Successfully loaded {len(self.df)} instances')
            self.logger.info(f'Available columns: {list(self.df.columns)}')

        except Exception as e:
            self.logger.error(f'Failed to load dataset {self.dataset_name}: {e}')
            raise

    def get_instance_by_id(self, instance_id: str) -> pd.Series:
        """
        Retrieve a specific instance by its ID.

        Args:
            instance_id: The instance identifier

        Returns:
            pandas Series containing the instance data

        Raises:
            KeyError: If instance_id is not found
        """
        if instance_id not in self.instance_lookup:
            raise KeyError(f"Instance ID '{instance_id}' not found in dataset")

        idx = self.instance_lookup[instance_id]
        return self.df.iloc[idx]

    def parse_instance_loc(self, instance: Union[pd.Series, str]) -> LocalizationInfo:
        """
        Parse ground-truth localization information from a SWE-Bench instance.

        Args:
            instance: Either a pandas Series with instance data or an instance_id string

        Returns:
            LocalizationInfo object containing extracted localization data
        """
        # Handle different input types
        if isinstance(instance, str):
            # instance is actually an instance_id
            actual_instance_id = instance
            instance = self.get_instance_by_id(actual_instance_id)
        else:
            # instance is a pandas Series
            actual_instance_id = instance.get('instance_id', 'unknown')

        self.logger.info(f'Parsing localization for instance: {actual_instance_id}')

        # Extract patch content
        patch_content = instance.get('patch', '')
        if not patch_content:
            self.logger.warning(
                f'No patch content found for instance {actual_instance_id}'
            )
            patch_loc_info = self._empty_localization_info(actual_instance_id)
        else:
            patch_loc_info = self._parse_patch_localization(
                patch_content, actual_instance_id
            )

        # Extract test patch content
        patch_content = instance.get('test_patch', '')
        if not patch_content:
            self.logger.warning(
                f'No test patch content found for instance {actual_instance_id}'
            )
            test_patch_loc_info = self._empty_localization_info(actual_instance_id)
        else:
            test_patch_loc_info = self._parse_patch_localization(
                patch_content, actual_instance_id
            )

        return {'patch': patch_loc_info, 'test_patch': test_patch_loc_info}

    def _parse_file_patch_lines(
        self, file_patch: str
    ) -> tuple[list[tuple[int, int]], int, int]:
        """
        Parse line ranges and count changes from a single file patch.

        Args:
            file_patch: Patch content for a single file

        Returns:
            Tuple of (line_ranges, total_lines_changed, num_hunks)
        """
        line_ranges = []
        lines_changed = 0
        num_hunks = 0

        lines = file_patch.split('\n')

        for line in lines:
            # Match hunk headers: @@ -start,count +start,count @@
            hunk_match = re.match(
                r'@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@', line
            )
            if hunk_match:
                num_hunks += 1
                new_start = int(hunk_match.group(3))
                new_count = int(hunk_match.group(4)) if hunk_match.group(4) else 1

                # For localization purposes, we consider the entire hunk range as potentially affected
                if new_count > 0:
                    line_ranges.append((new_start, new_start + new_count - 1))
                    lines_changed += new_count

        return line_ranges, lines_changed, num_hunks

    def _parse_code_structures_from_patch(
        self, file_patch: str, file_path: str
    ) -> tuple[list[str], list[str]]:
        """
        Extract function and class names from patch context (fallback method).

        Args:
            file_patch: Patch content for a single file
            file_path: Path to the file being patched

        Returns:
            Tuple of (function_names, class_names)
        """
        functions = set()
        classes = set()

        # Only attempt Python AST parsing for Python files
        if not file_path.endswith('.py'):
            return list(functions), list(classes)

        lines = file_patch.split('\n')

        for line in lines:
            # Check for function names in hunk headers
            # Format: @@ -start,count +start,count @@ [optional context like "def function_name"]
            hunk_match = re.match(r'@@.*?@@\s*(.*)', line)
            if hunk_match:
                context = hunk_match.group(1).strip()
                if context:
                    # Look for function definition in context
                    func_match = re.search(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)', context)
                    if func_match:
                        functions.add(func_match.group(1))

                    # Look for class definition in context
                    class_match = re.search(
                        r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', context
                    )
                    if class_match:
                        classes.add(class_match.group(1))

            # Look for function and class definitions in the patch content
            stripped_line = line.lstrip('+-@ ')

            # Match function definitions
            func_match = re.match(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', stripped_line)
            if func_match:
                functions.add(func_match.group(1))

            # Match class definitions
            class_match = re.match(
                r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[\(:]', stripped_line
            )
            if class_match:
                classes.add(class_match.group(1))

        return list(functions), list(classes)

    def _parse_patch_localization(
        self, patch_content: str, instance_id: str
    ) -> LocalizationInfo:
        """
        Parse localization information from a git patch (improved method).

        Args:
            patch_content: The git patch content
            instance_id: Instance ID for logging

        Returns:
            LocalizationInfo object with extracted data
        """
        files = []
        file_line_ranges = {}
        functions = {}
        classes = {}
        line_to_function = {}
        line_to_class = {}
        hunks_per_file = {}
        total_lines_changed = 0

        # Split patch into individual file patches
        file_patches = self._split_patch_by_files(patch_content)

        for file_path, file_patch in file_patches.items():
            files.append(file_path)

            # Parse line ranges and count changes
            line_ranges, lines_changed, num_hunks = self._parse_file_patch_lines(
                file_patch
            )
            file_line_ranges[file_path] = line_ranges
            total_lines_changed += lines_changed
            hunks_per_file[file_path] = num_hunks

            # Extract function and class names from patch context and content
            file_functions, file_classes = self._extract_code_structures_from_patch(
                file_patch, file_path
            )

            functions[file_path] = file_functions
            classes[file_path] = file_classes

            # Create basic line-to-function/class mapping
            line_func_map = {}
            line_class_map = {}

            # Get all affected lines
            affected_lines = []
            for start, end in line_ranges:
                affected_lines.extend(range(start, end + 1))

            # Simple mapping - this is the best we can do without the actual source code
            # In a more sophisticated implementation, you'd want to parse the actual source files
            if file_functions and affected_lines:
                # Map to the first function found (could be improved with better heuristics)
                for line_num in affected_lines:
                    if file_functions:
                        line_func_map[line_num] = file_functions[0]
                    if file_classes:
                        line_class_map[line_num] = file_classes[0]

            line_to_function[file_path] = line_func_map
            line_to_class[file_path] = line_class_map

        return LocalizationInfo(
            instance_id=instance_id,
            files=files,
            file_line_ranges=file_line_ranges,
            functions=functions,
            classes=classes,
            line_to_function=line_to_function,
            line_to_class=line_to_class,
            total_lines_changed=total_lines_changed,
            total_files_changed=len(files),
            hunks_per_file=hunks_per_file,
        )

    def _extract_code_structures_from_patch(
        self, file_patch: str, file_path: str
    ) -> tuple[list[str], list[str]]:
        """
        Extract function and class names from patch context and content.

        Args:
            file_patch: Patch content for a single file
            file_path: Path to the file being patched

        Returns:
            Tuple of (function_names, class_names)
        """
        functions = set()
        classes = set()

        # Process Python and Cython files
        if not (file_path.endswith('.py') or file_path.endswith('.pyx')):
            return list(functions), list(classes)

        lines = file_patch.split('\n')

        # Debug: Print some patch content for analysis
        self.logger.info(f'Analyzing patch for {file_path}')
        self.logger.info(f'Patch has {len(lines)} lines')

        for line in lines:
            # Check for function names in hunk headers with context
            # Format: @@ -start,count +start,count @@ [optional context like "def function_name"]
            hunk_match = re.match(r'@@.*?@@\s*(.*)', line)
            if hunk_match:
                context = hunk_match.group(1).strip()
                self.logger.info(f"Found hunk context: '{context}'")
                if context:
                    # Look for function definition in context
                    func_match = re.search(
                        r'(?:def|async\s+def|cdef\s+\w*\s+|cpdef\s+\w*\s+)\s*([a-zA-Z_][a-zA-Z0-9_]*)',
                        context,
                    )
                    if func_match:
                        func_name = func_match.group(1)
                        functions.add(func_name)
                        self.logger.info(f'Found function in hunk context: {func_name}')

                    # Look for class definition in context
                    class_match = re.search(
                        r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', context
                    )
                    if class_match:
                        class_name = class_match.group(1)
                        classes.add(class_name)
                        self.logger.info(f'Found class in hunk context: {class_name}')

            # Look for function and class definitions in the patch content
            # Check both added and removed lines, and context lines
            if line.startswith(('+', '-', ' ')):
                stripped_line = line[1:].strip()  # Remove +/- prefix and whitespace

                # Match function definitions (including async and cdef for Cython)
                func_match = re.match(
                    r'(?:async\s+|cdef\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                    stripped_line,
                )
                if func_match:
                    func_name = func_match.group(1)
                    functions.add(func_name)
                    self.logger.info(f'Found function in patch content: {func_name}')

                # Match Cython cdef functions
                cdef_func_match = re.match(
                    r'cdef\s+[^(]*\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', stripped_line
                )
                if cdef_func_match:
                    func_name = cdef_func_match.group(1)
                    functions.add(func_name)
                    self.logger.info(
                        f'Found cdef function in patch content: {func_name}'
                    )

                # Match class definitions
                class_match = re.match(
                    r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[\(:]', stripped_line
                )
                if class_match:
                    class_name = class_match.group(1)
                    classes.add(class_name)
                    self.logger.info(f'Found class in patch content: {class_name}')

            # Also check lines without prefixes (context lines in some patch formats)
            elif line.strip() and not line.startswith(
                ('@@', 'diff', '---', '+++', 'index')
            ):
                stripped_line = line.strip()

                # Match function definitions
                func_match = re.match(
                    r'(?:async\s+|cdef\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                    stripped_line,
                )
                if func_match:
                    func_name = func_match.group(1)
                    functions.add(func_name)
                    self.logger.info(f'Found function in context line: {func_name}')

                # Match Cython cdef functions
                cdef_func_match = re.match(
                    r'cdef\s+[^(]*\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', stripped_line
                )
                if cdef_func_match:
                    func_name = cdef_func_match.group(1)
                    functions.add(func_name)
                    self.logger.info(
                        f'Found cdef function in context line: {func_name}'
                    )

                # Match class definitions
                class_match = re.match(
                    r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[\(:]', stripped_line
                )
                if class_match:
                    class_name = class_match.group(1)
                    classes.add(class_name)
                    self.logger.info(f'Found class in context line: {class_name}')

        self.logger.info(
            f'Final results for {file_path}: functions={list(functions)}, classes={list(classes)}'
        )
        return list(functions), list(classes)

    def _parse_patch_localization_with_runtime(
        self, patch_content: str, instance_id: str, runtime: Runtime
    ) -> LocalizationInfo:
        """
        Parse localization information from a git patch using OpenHands runtime.
        This is the superior method when runtime is available.

        Args:
            patch_content: The git patch content
            instance_id: Instance ID for logging
            runtime: OpenHands runtime object

        Returns:
            LocalizationInfo object with extracted data
        """
        files = []
        file_line_ranges = {}
        functions = {}
        classes = {}
        line_to_function = {}
        line_to_class = {}
        hunks_per_file = {}
        total_lines_changed = 0

        # Split patch into individual file patches
        file_patches = self._split_patch_by_files(patch_content)

        for file_path, file_patch in file_patches.items():
            files.append(file_path)

            # Parse line ranges and count changes
            line_ranges, lines_changed, num_hunks = self._parse_file_patch_lines(
                file_patch
            )
            file_line_ranges[file_path] = line_ranges
            total_lines_changed += lines_changed
            hunks_per_file[file_path] = num_hunks

            # Get all affected line numbers
            affected_lines = []
            for start, end in line_ranges:
                affected_lines.extend(range(start, end + 1))

            # Analyze source code using OpenHands runtime for accurate function/class mapping
            if affected_lines and (
                file_path.endswith('.py') or file_path.endswith('.pyx')
            ):
                file_functions, file_classes, line_func_map, line_class_map = (
                    self._analyze_source_code_with_runtime(
                        runtime, file_path, affected_lines
                    )
                )
            else:
                # Fallback to patch-based extraction for non-Python/Cython files or when no lines affected
                file_functions, file_classes = self._extract_code_structures_from_patch(
                    file_patch, file_path
                )
                line_func_map, line_class_map = {}, {}

            functions[file_path] = file_functions
            classes[file_path] = file_classes
            line_to_function[file_path] = line_func_map
            line_to_class[file_path] = line_class_map

        return LocalizationInfo(
            instance_id=instance_id,
            files=files,
            file_line_ranges=file_line_ranges,
            functions=functions,
            classes=classes,
            line_to_function=line_to_function,
            line_to_class=line_to_class,
            total_lines_changed=total_lines_changed,
            total_files_changed=len(files),
            hunks_per_file=hunks_per_file,
        )

    def parse_instance_loc_with_runtime(
        self, instance: Union[pd.Series, str], runtime: Runtime = None
    ) -> LocalizationInfo:
        """
        Parse ground-truth localization information using OpenHands runtime.

        Args:
            instance: Either a pandas Series with instance data or an instance_id string
            runtime: OpenHands runtime object

        Returns:
            LocalizationInfo object containing extracted localization data
        """
        # Handle different input types
        if isinstance(instance, str):
            # instance is actually an instance_id
            actual_instance_id = instance
            instance = self.get_instance_by_id(actual_instance_id)
        else:
            # instance is a pandas Series
            actual_instance_id = instance.get('instance_id', 'unknown')

        self.logger.info(
            f'Parsing localization with runtime for instance: {actual_instance_id}'
        )

        # Extract patch content
        patch_content = instance.get('patch', '')
        if not patch_content:
            self.logger.warning(
                f'No patch content found for instance {actual_instance_id}'
            )
            return self._empty_localization_info(actual_instance_id)

        return self._parse_patch_localization_with_runtime(
            patch_content, actual_instance_id, runtime
        )

    def _analyze_source_code_with_runtime(
        self, runtime: Runtime, file_path: str, affected_lines: list[int]
    ) -> tuple[list[str], list[str], dict[int, str], dict[int, str]]:
        """
        Analyze source code using OpenHands runtime to find functions and classes.

        Args:
            runtime: OpenHands runtime object
            file_path: Path to the file being analyzed
            affected_lines: List of line numbers that were changed

        Returns:
            Tuple of (functions, classes, line_to_function_map, line_to_class_map)
        """
        try:
            # Check if file exists and is a Python/Cython file
            if not (file_path.endswith('.py') or file_path.endswith('.pyx')):
                self.logger.info(f'Skipping non-Python/Cython file: {file_path}')
                return [], [], {}, {}

            # Read the file content using runtime
            from openhands.events.action import CmdRunAction

            # First check if file exists
            check_action = CmdRunAction(
                command=f'test -f "{file_path}" && echo "EXISTS" || echo "NOT_EXISTS"'
            )
            obs = runtime.run_action(check_action)

            if 'NOT_EXISTS' in obs.content:
                self.logger.warning(f'File not found: {file_path}')
                return [], [], {}, {}

            # Read file content
            read_action = CmdRunAction(command=f'cat "{file_path}"')
            obs = runtime.run_action(read_action)

            if obs.exit_code != 0:
                self.logger.warning(f'Failed to read file {file_path}: {obs.content}')
                return [], [], {}, {}

            file_content = obs.content

            # Parse the content
            if file_path.endswith('.py'):
                return self._parse_python_content_with_line_mapping(
                    file_content, affected_lines
                )
            elif file_path.endswith('.pyx'):
                return self._parse_cython_content_with_line_mapping(
                    file_content, affected_lines
                )
            else:
                return [], [], {}, {}

        except Exception as e:
            self.logger.warning(
                f'Failed to analyze source code with runtime for {file_path}: {e}'
            )
            return [], [], {}, {}

    def _parse_cython_content_with_line_mapping(
        self, content: str, affected_lines: list[int]
    ) -> tuple[list[str], list[str], dict[int, str], dict[int, str]]:
        """
        Parse Cython content to extract functions and classes with line mapping.
        Since Cython files can't be parsed with Python's AST, we use regex-based parsing.

        Args:
            content: Cython source code content
            affected_lines: List of line numbers that were changed

        Returns:
            Tuple of (functions, classes, line_to_function_map, line_to_class_map)
        """
        try:
            functions = set()
            classes = set()
            line_to_function = {}
            line_to_class = {}

            lines = content.split('\n')
            current_function = None
            current_class = None

            for i, line in enumerate(lines, 1):
                stripped_line = line.strip()

                # Match class definitions
                class_match = re.match(
                    r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[\(:]', stripped_line
                )
                if class_match:
                    current_class = class_match.group(1)
                    classes.add(current_class)
                    continue

                # Match function definitions (def, cdef, cpdef)
                func_match = re.match(
                    r'(?:async\s+|c?p?def\s+(?:[^(]*\s+)?)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                    stripped_line,
                )
                if not func_match:
                    # Try matching cdef functions with return types
                    func_match = re.match(
                        r'cdef\s+[^(]*\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', stripped_line
                    )
                if not func_match:
                    # Try matching cpdef functions
                    func_match = re.match(
                        r'cpdef\s+[^(]*\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', stripped_line
                    )

                if func_match:
                    current_function = func_match.group(1)
                    functions.add(current_function)
                    continue

                # Check if we're leaving a function/class (basic heuristic based on indentation)
                if (
                    current_function
                    and line
                    and not line[0].isspace()
                    and not line.startswith('#')
                ):
                    # We've left the function
                    current_function = None

                if (
                    current_class
                    and line
                    and not line[0].isspace()
                    and not line.startswith('#')
                    and not stripped_line.startswith('def ')
                    and not stripped_line.startswith('cdef ')
                    and not stripped_line.startswith('cpdef ')
                ):
                    # We've left the class
                    current_class = None

            # Map affected lines to functions and classes using a simple heuristic
            # This is imperfect but better than nothing for Cython files
            lines = content.split('\n')
            for line_num in affected_lines:
                if line_num <= len(lines):
                    # Find the nearest function/class definition above this line
                    nearest_function = None
                    nearest_class = None

                    for i in range(line_num - 1, -1, -1):
                        if i < len(lines):
                            line = lines[i].strip()

                            # Check for function definition
                            func_match = re.match(
                                r'(?:async\s+|c?p?def\s+(?:[^(]*\s+)?)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                                line,
                            )
                            if not func_match:
                                func_match = re.match(
                                    r'cdef\s+[^(]*\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                                    line,
                                )
                            if not func_match:
                                func_match = re.match(
                                    r'cpdef\s+[^(]*\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                                    line,
                                )

                            if func_match and not nearest_function:
                                nearest_function = func_match.group(1)

                            # Check for class definition
                            class_match = re.match(
                                r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[\(:]', line
                            )
                            if class_match and not nearest_class:
                                nearest_class = class_match.group(1)

                            # Stop if we found both or hit the beginning
                            if (nearest_function and nearest_class) or i == 0:
                                break

                    if nearest_function:
                        line_to_function[line_num] = nearest_function
                    if nearest_class:
                        line_to_class[line_num] = nearest_class

            return list(functions), list(classes), line_to_function, line_to_class

        except Exception as e:
            self.logger.warning(f'Failed to parse Cython content: {e}')
            return [], [], {}, {}

    def _parse_python_content_with_line_mapping(
        self, content: str, affected_lines: list[int]
    ) -> tuple[list[str], list[str], dict[int, str], dict[int, str]]:
        """
        Parse Python content to extract functions and classes with accurate line mapping.

        Args:
            content: Python source code content
            affected_lines: List of line numbers that were changed

        Returns:
            Tuple of (functions, classes, line_to_function_map, line_to_class_map)
        """
        try:
            tree = ast.parse(content)

            functions = set()
            classes = set()
            line_to_function = {}
            line_to_class = {}

            # Create a mapping of line numbers to AST nodes
            line_to_node = {}

            class NodeVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.current_class = None
                    self.class_stack = []

                def visit_ClassDef(self, node):
                    self.class_stack.append(node.name)
                    old_class = self.current_class
                    self.current_class = node.name
                    classes.add(node.name)

                    # Mark lines in this class
                    start_line = node.lineno
                    end_line = getattr(node, 'end_lineno', node.lineno)
                    if end_line is None:
                        # Estimate end line by finding the next class/function or end of file
                        end_line = start_line + 100  # Conservative estimate

                    for line_num in range(start_line, end_line + 1):
                        line_to_node[line_num] = ('class', node.name)

                    self.generic_visit(node)
                    self.current_class = old_class
                    self.class_stack.pop()

                def visit_FunctionDef(self, node):
                    functions.add(node.name)

                    # Mark lines in this function
                    start_line = node.lineno
                    end_line = getattr(node, 'end_lineno', node.lineno)
                    if end_line is None:
                        # Estimate end line based on the next sibling or parent end
                        end_line = start_line + 50  # Conservative estimate

                    for line_num in range(start_line, end_line + 1):
                        line_to_node[line_num] = ('function', node.name)

                    self.generic_visit(node)

                def visit_AsyncFunctionDef(self, node):
                    # Handle async functions the same way
                    self.visit_FunctionDef(node)

            visitor = NodeVisitor()
            visitor.visit(tree)

            # Map affected lines to functions and classes
            for line_num in affected_lines:
                if line_num in line_to_node:
                    node_type, node_name = line_to_node[line_num]
                    if node_type == 'function':
                        line_to_function[line_num] = node_name
                    elif node_type == 'class':
                        line_to_class[line_num] = node_name

            return list(functions), list(classes), line_to_function, line_to_class

        except Exception as e:
            self.logger.warning(f'Failed to parse Python content: {e}')
            return [], [], {}, {}

    def _parse_python_content(
        self, content: str, affected_lines: list[int]
    ) -> tuple[list[str], list[str], dict[int, str], dict[int, str]]:
        """
        Parse Python content to extract functions and classes.

        Args:
            content: Python source code content
            affected_lines: List of line numbers that were changed

        Returns:
            Tuple of (functions, classes, line_to_function_map, line_to_class_map)
        """
        try:
            tree = ast.parse(content)

            functions = set()
            classes = set()
            line_to_function = {}
            line_to_class = {}

            class Analyzer(ast.NodeVisitor):
                def __init__(self):
                    self.current_class = None
                    self.function_stack = []
                    self.class_stack = []

                def visit_ClassDef(self, node):
                    self.class_stack.append(node.name)
                    old_class = self.current_class
                    self.current_class = node.name
                    classes.add(node.name)

                    # Mark lines in this class
                    end_line = getattr(node, 'end_lineno', node.lineno)
                    if end_line is None:
                        end_line = node.lineno

                    for line_num in range(node.lineno, end_line + 1):
                        if line_num in affected_lines:
                            line_to_class[line_num] = node.name

                    self.generic_visit(node)
                    self.current_class = old_class
                    self.class_stack.pop()

                def visit_FunctionDef(self, node):
                    self.function_stack.append(node.name)
                    functions.add(node.name)

                    # Mark lines in this function
                    end_line = getattr(node, 'end_lineno', node.lineno)
                    if end_line is None:
                        end_line = node.lineno

                    for line_num in range(node.lineno, end_line + 1):
                        if line_num in affected_lines:
                            line_to_function[line_num] = node.name
                            if self.current_class:
                                line_to_class[line_num] = self.current_class

                    self.generic_visit(node)
                    self.function_stack.pop()

                def visit_AsyncFunctionDef(self, node):
                    # Handle async functions the same way
                    self.visit_FunctionDef(node)

            analyzer = Analyzer()
            analyzer.visit(tree)

            return list(functions), list(classes), line_to_function, line_to_class

        except Exception as e:
            self.logger.warning(f'Failed to parse Python content: {e}')
            return [], [], {}, {}

    def _split_patch_by_files(self, patch_content: str) -> dict[str, str]:
        """
        Split a multi-file patch into individual file patches.

        Args:
            patch_content: Complete patch content

        Returns:
            Dictionary mapping file paths to their patch content
        """
        file_patches = {}
        current_file = None
        current_patch_lines = []

        lines = patch_content.split('\n')

        for line in lines:
            # Check for file header patterns
            if line.startswith('diff --git'):
                # Save previous file if exists
                if current_file and current_patch_lines:
                    file_patches[current_file] = '\n'.join(current_patch_lines)

                # Extract file path from diff line
                # Format: diff --git a/path/to/file.py b/path/to/file.py
                match = re.search(r'diff --git a/(.*?) b/(.*?)(?:\s|$)', line)
                if match:
                    current_file = match.group(1)  # Use the 'a/' path
                    current_patch_lines = [line]
                else:
                    current_file = None
                    current_patch_lines = []

            elif line.startswith('---') or line.startswith('+++'):
                # Alternative file path extraction
                if not current_file:
                    match = re.search(r'[+-]{3}\s+(?:a/|b/)?(.+?)(?:\s|$)', line)
                    if match and not match.group(1).startswith('/dev/null'):
                        current_file = match.group(1)
                        if not current_patch_lines:
                            current_patch_lines = [line]
                        else:
                            current_patch_lines.append(line)
                    else:
                        if current_patch_lines:
                            current_patch_lines.append(line)
                else:
                    current_patch_lines.append(line)

            elif current_file:
                current_patch_lines.append(line)

        # Save the last file
        if current_file and current_patch_lines:
            file_patches[current_file] = '\n'.join(current_patch_lines)

        return file_patches

    def _empty_localization_info(
        self, instance_id: str = 'unknown'
    ) -> LocalizationInfo:
        """
        Return an empty LocalizationInfo object.

        Args:
            instance_id: Instance identifier

        Returns:
            Empty LocalizationInfo instance
        """
        return LocalizationInfo(
            instance_id=instance_id,
            files=[],
            file_line_ranges={},
            functions={},
            classes={},
            line_to_function={},
            line_to_class={},
            total_lines_changed=0,
            total_files_changed=0,
            hunks_per_file={},
        )

    def get_dataset_statistics(self) -> dict[str, Any]:
        """
        Get statistics about the loaded dataset.

        Returns:
            Dictionary containing dataset statistics
        """
        if self.df is None:
            return {}

        stats = {
            'total_instances': len(self.df),
            'repositories': self.df['repo'].nunique()
            if 'repo' in self.df.columns
            else 0,
            'avg_patch_length': self.df['patch'].str.len().mean()
            if 'patch' in self.df.columns
            else 0,
            'columns': list(self.df.columns),
        }

        return stats

    def get_instances_by_repo(self, repo_name: str) -> pd.DataFrame:
        """
        Get all instances for a specific repository.

        Args:
            repo_name: Repository name (e.g., "django/django")

        Returns:
            DataFrame containing instances for the specified repository
        """
        if 'repo' not in self.df.columns:
            raise ValueError('Repository information not available in dataset')

        return self.df[self.df['repo'] == repo_name].copy()
