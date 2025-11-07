#!/usr/bin/env python3
"""
Script to analyze generated diff patches and calculate localization correctness.

This script:
1. Fetches generated patches from evaluation output directories
2. Loads golden patches from the SWE-bench dataset
3. Maps patches to the repository and extracts modified locations using AST
4. Calculates Jaccard similarity coefficient between generated and golden locations
"""

import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from typing import Optional

try:
    from datasets import load_dataset
except ImportError:
    print(
        "Error: 'datasets' library not found. Please install it with: pip install datasets"
    )
    sys.exit(1)


class PatchLocation:
    """Represents a code location modified by a patch."""

    def __init__(
        self,
        file_path: str,
        function_name: Optional[str] = None,
        class_name: Optional[str] = None,
        line_start: int = None,
        line_end: int = None,
        is_global: bool = False,
    ):
        self.file_path = file_path
        self.function_name = function_name
        self.class_name = class_name
        self.line_start = line_start
        self.line_end = line_end
        self.is_global = is_global

    def __hash__(self):
        # For function/class locations, ignore line numbers in hash
        # For global locations, include line numbers
        if self.is_global:
            return hash(
                (self.file_path, self.line_start, self.line_end, self.is_global)
            )
        else:
            return hash(
                (self.file_path, self.class_name, self.function_name, self.is_global)
            )

    def __eq__(self, other):
        if not isinstance(other, PatchLocation):
            return False

        # For function/class locations, compare by file, class, and function names
        # For global locations, also compare line ranges
        if self.is_global:
            return (
                self.file_path == other.file_path
                and self.line_start == other.line_start
                and self.line_end == other.line_end
                and self.is_global == other.is_global
            )
        else:
            return (
                self.file_path == other.file_path
                and self.class_name == other.class_name
                and self.function_name == other.function_name
                and self.is_global == other.is_global
            )

    def __repr__(self):
        if self.is_global:
            return f'PatchLocation(file={self.file_path}, lines={self.line_start}-{self.line_end}, global)'
        else:
            class_part = f'{self.class_name}.' if self.class_name else ''
            return f'PatchLocation(file={self.file_path}, {class_part}{self.function_name or "unknown"})'


class ASTLocationExtractor:
    """Extract function and class locations from Python files using AST."""

    @staticmethod
    def get_function_class_at_line(
        file_path: str, line_number: int
    ) -> tuple[Optional[str], Optional[str]]:
        """Get the function and class name at a given line number."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()

            tree = ast.parse(source, filename=file_path)

            class_name = None
            function_name = None

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                        if (
                            node.lineno
                            <= line_number
                            <= (node.end_lineno or node.lineno)
                        ):
                            class_name = node.name
                            # Check for methods within the class
                            for item in node.body:
                                if isinstance(
                                    item, (ast.FunctionDef, ast.AsyncFunctionDef)
                                ):
                                    if hasattr(item, 'lineno') and hasattr(
                                        item, 'end_lineno'
                                    ):
                                        if (
                                            item.lineno
                                            <= line_number
                                            <= (item.end_lineno or item.lineno)
                                        ):
                                            function_name = item.name
                                            break

                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                        if (
                            node.lineno
                            <= line_number
                            <= (node.end_lineno or node.lineno)
                        ):
                            # Only set if not already in a class
                            if not class_name:
                                function_name = node.name

            return class_name, function_name

        except Exception as e:
            print(f'Warning: Could not parse {file_path}: {e}')
            return None, None

    @staticmethod
    def get_context_lines(
        file_path: str, line_number: int, context: int = 3
    ) -> tuple[int, int]:
        """Get the line range for context around a line."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                total_lines = sum(1 for _ in f)

            start = max(1, line_number - context)
            end = min(total_lines, line_number + context)
            return start, end
        except Exception:
            return line_number, line_number


class PatchParser:
    """Parse unified diff patches and extract modified locations."""

    @staticmethod
    def parse_patch(patch_content: str) -> dict[str, list[tuple[int, str]]]:
        """
        Parse a unified diff patch and return modified files with their line changes.

        Returns:
            Dict mapping file paths to list of (line_number, change_type) tuples
            where change_type is 'add', 'remove', or 'context'
        """
        file_changes = defaultdict(list)
        current_file = None
        current_line_old = 0
        current_line_new = 0

        lines = patch_content.split('\n')

        for line in lines:
            # File header
            if line.startswith('--- ') or line.startswith('+++ '):
                if line.startswith('+++ '):
                    # Extract file path
                    file_path = line[4:].split('\t')[0].strip()
                    # Remove 'b/' prefix if present
                    if file_path.startswith('b/'):
                        file_path = file_path[2:]
                    if file_path and file_path != '/dev/null':
                        current_file = file_path
                continue

            # Hunk header
            if line.startswith('@@'):
                match = re.match(r'@@ -(\d+),?\d* \+(\d+),?\d* @@', line)
                if match:
                    current_line_old = int(match.group(1))
                    current_line_new = int(match.group(2))
                continue

            if current_file is None:
                continue

            # Change lines
            if line.startswith('+') and not line.startswith('+++'):
                file_changes[current_file].append((current_line_new, 'add'))
                current_line_new += 1
            elif line.startswith('-') and not line.startswith('---'):
                file_changes[current_file].append((current_line_old, 'remove'))
                current_line_old += 1
            elif line.startswith(' '):
                current_line_old += 1
                current_line_new += 1

        return dict(file_changes)

    @staticmethod
    def extract_modified_locations(
        patch_content: str, repo_path: str
    ) -> set[PatchLocation]:
        """
        Extract modified locations from a patch using AST analysis.

        Args:
            patch_content: The unified diff patch content
            repo_path: Path to the repository root

        Returns:
            Set of PatchLocation objects representing modified locations
        """
        file_changes = PatchParser.parse_patch(patch_content)
        locations = set()

        for file_path, changes in file_changes.items():
            full_path = os.path.join(repo_path, file_path)

            # Skip if file doesn't exist or is not a Python file
            if not os.path.exists(full_path):
                continue

            if not file_path.endswith('.py'):
                # For non-Python files, use line-based locations
                for line_num, change_type in changes:
                    if change_type in ['add', 'remove']:
                        extractor = ASTLocationExtractor()
                        start, end = extractor.get_context_lines(
                            full_path, line_num, context=3
                        )
                        locations.add(
                            PatchLocation(
                                file_path=file_path,
                                line_start=start,
                                line_end=end,
                                is_global=True,
                            )
                        )
                continue

            # Group changes by their containing function/class
            extractor = ASTLocationExtractor()
            function_class_map = defaultdict(list)

            for line_num, change_type in changes:
                if change_type in ['add', 'remove']:
                    class_name, function_name = extractor.get_function_class_at_line(
                        full_path, line_num
                    )

                    if function_name or class_name:
                        # Inside a function or class
                        key = (class_name, function_name)
                        function_class_map[key].append(line_num)
                    else:
                        # Global code - use context lines
                        start, end = extractor.get_context_lines(
                            full_path, line_num, context=3
                        )
                        locations.add(
                            PatchLocation(
                                file_path=file_path,
                                line_start=start,
                                line_end=end,
                                is_global=True,
                            )
                        )

            # Add function/class locations
            for (class_name, function_name), lines in function_class_map.items():
                locations.add(
                    PatchLocation(
                        file_path=file_path,
                        class_name=class_name,
                        function_name=function_name,
                        line_start=min(lines),
                        line_end=max(lines),
                        is_global=False,
                    )
                )

        return locations


class RepositoryManager:
    """Manage repository cloning and checkout operations."""

    @staticmethod
    def clone_and_checkout(repo_name: str, commit: str, temp_dir: str) -> str:
        """
        Clone a repository and checkout a specific commit.

        Args:
            repo_name: Repository name in format 'owner/repo'
            commit: Commit hash to checkout
            temp_dir: Temporary directory to clone into

        Returns:
            Path to the cloned repository
        """
        repo_url = f'https://github.com/{repo_name}.git'
        repo_path = os.path.join(temp_dir, repo_name.replace('/', '_'))

        try:
            # Clone with depth=1 for speed, then fetch the specific commit
            print(f'  Cloning {repo_name}...')
            subprocess.run(
                ['git', 'clone', '--depth', '1', repo_url, repo_path],
                check=True,
                capture_output=True,
                text=True,
                timeout=300,
            )

            # Fetch the specific commit
            print(f'  Fetching commit {commit[:8]}...')
            subprocess.run(
                ['git', 'fetch', 'origin', commit],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True,
                timeout=300,
            )

            # Checkout the commit
            print(f'  Checking out commit {commit[:8]}...')
            subprocess.run(
                ['git', 'checkout', commit],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True,
                timeout=60,
            )

            return repo_path

        except subprocess.TimeoutExpired:
            print(f'  Warning: Git operation timed out for {repo_name}')
            return None
        except subprocess.CalledProcessError as e:
            print(f'  Warning: Git operation failed for {repo_name}: {e}')
            return None
        except Exception as e:
            print(f'  Warning: Unexpected error cloning {repo_name}: {e}')
            return None


class LocalizationAnalyzer:
    """Analyze patch localization correctness."""

    def __init__(
        self,
        eval_output_dir: str,
        dataset_name: str = 'princeton-nlp/SWE-bench_Verified',
        split: str = 'test',
    ):
        self.eval_output_dir = eval_output_dir
        self.dataset_name = dataset_name
        self.split = split
        self.dataset = None
        self.dataset_dict = {}

    def calculate_file_level_similarity(
        self,
        generated_locations: set[PatchLocation],
        golden_locations: set[PatchLocation],
    ) -> float:
        """
        Calculate file-level Jaccard similarity.
        Only considers whether patches modify the same files.
        """
        generated_files = {loc.file_path for loc in generated_locations}
        golden_files = {loc.file_path for loc in golden_locations}

        return self.calculate_jaccard_similarity(generated_files, golden_files)

    def calculate_function_level_similarity(
        self,
        generated_locations: set[PatchLocation],
        golden_locations: set[PatchLocation],
    ) -> float:
        """
        Calculate function-level Jaccard similarity.
        Considers file, class, and function names (ignores line numbers for function/class locations).
        """

        # Create normalized locations (without line numbers for function/class based locations)
        def normalize_location(loc: PatchLocation):
            if loc.is_global:
                # For global code, use file path only (not line numbers)
                return (loc.file_path, 'global', None, None)
            else:
                return (loc.file_path, loc.class_name, loc.function_name, 'function')

        generated_normalized = {normalize_location(loc) for loc in generated_locations}
        golden_normalized = {normalize_location(loc) for loc in golden_locations}

        return self.calculate_jaccard_similarity(
            generated_normalized, golden_normalized
        )

    def calculate_line_level_similarity(
        self, generated_patch: str, golden_patch: str, repo_path: str
    ) -> float:
        """
        Calculate line-level overlap.
        A line is considered a hit if:
        - For generated patch: the start line appears in the range of any golden edit scope
        - For golden patch: the start line appears in the range of any generated edit scope

        Note: Test files are excluded from generated patch to avoid dilution.
        """
        parser = PatchParser()

        # Get file changes with line numbers
        generated_changes = parser.parse_patch(generated_patch)
        golden_changes = parser.parse_patch(golden_patch)

        # Filter out test files from generated changes
        def is_test_file(file_path):
            """Check if a file is a test file."""
            path_lower = file_path.lower()
            parts = file_path.split('/')

            # Common test patterns
            if any(
                part in ['test', 'tests', '__tests__', 'test_utils'] for part in parts
            ):
                return True
            if path_lower.startswith('test') or path_lower.startswith('tests/'):
                return True
            if 'test_' in path_lower or '_test' in path_lower:
                return True
            if path_lower.endswith('_test.py') or path_lower.endswith('_tests.py'):
                return True
            if path_lower.endswith('test.py') or path_lower.endswith('tests.py'):
                return True

            return False

        # Filter generated changes to exclude test files
        generated_changes_filtered = {
            file_path: changes
            for file_path, changes in generated_changes.items()
            if not is_test_file(file_path)
        }

        # Build line ranges for each file
        def get_line_ranges(file_changes):
            """Convert list of line changes to set of (file, line) tuples and ranges."""
            line_sets = defaultdict(set)
            line_ranges = defaultdict(list)

            for file_path, changes in file_changes.items():
                for line_num, change_type in changes:
                    if change_type in ['add', 'remove']:
                        line_sets[file_path].add(line_num)

                # Create ranges with +/- 3 lines context
                if line_sets[file_path]:
                    sorted_lines = sorted(line_sets[file_path])
                    ranges = []
                    for line in sorted_lines:
                        ranges.append((max(1, line - 3), line + 3))
                    line_ranges[file_path] = ranges

            return line_sets, line_ranges

        gen_lines, gen_ranges = get_line_ranges(generated_changes_filtered)
        gold_lines, gold_ranges = get_line_ranges(golden_changes)

        # Calculate hits
        generated_hits = set()
        golden_hits = set()

        # Check if generated lines fall within golden ranges
        for file_path in gen_lines:
            if file_path in gold_ranges:
                for gen_line in gen_lines[file_path]:
                    for gold_start, gold_end in gold_ranges[file_path]:
                        if gold_start <= gen_line <= gold_end:
                            generated_hits.add((file_path, gen_line))
                            break

        # Check if golden lines fall within generated ranges
        for file_path in gold_lines:
            if file_path in gen_ranges:
                for gold_line in gold_lines[file_path]:
                    for gen_start, gen_end in gen_ranges[file_path]:
                        if gen_start <= gold_line <= gen_end:
                            golden_hits.add((file_path, gold_line))
                            break

        # Calculate total unique modified lines
        all_gen_lines = {(f, line) for f in gen_lines for line in gen_lines[f]}
        all_gold_lines = {(f, line) for f in gold_lines for line in gold_lines[f]}

        # Jaccard: intersection over union
        intersection = len(generated_hits) + len(golden_hits)
        union = len(all_gen_lines) + len(all_gold_lines)

        if union == 0:
            return 1.0 if intersection == 0 else 0.0

        # Alternative: use symmetric hit rate
        # This counts how many lines on each side have overlapping ranges
        total_lines = len(all_gen_lines) + len(all_gold_lines)
        if total_lines == 0:
            return 1.0

        return intersection / total_lines

    def load_dataset(self):
        """Load the SWE-bench dataset."""
        print(f'Loading dataset {self.dataset_name} (split: {self.split})...')
        self.dataset = load_dataset(self.dataset_name, split=self.split)

        # Create a dictionary for faster lookup
        for item in self.dataset:
            self.dataset_dict[item['instance_id']] = item

        print(f'Loaded {len(self.dataset_dict)} instances from dataset')

    def get_generated_patch(self, instance_id: str) -> Optional[str]:
        """Get the generated patch for an instance."""
        patch_path = os.path.join(
            self.eval_output_dir, 'eval_outputs', instance_id, 'patch.diff'
        )

        if not os.path.exists(patch_path):
            return None

        try:
            with open(patch_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            print(f'  Warning: Could not read patch for {instance_id}: {e}')
            return None

    def get_golden_patch(self, instance_id: str) -> Optional[str]:
        """Get the golden patch for an instance from the dataset."""
        if instance_id not in self.dataset_dict:
            return None

        return self.dataset_dict[instance_id].get('patch', None)

    def calculate_jaccard_similarity(self, set1: set, set2: set) -> float:
        """Calculate Jaccard similarity coefficient between two sets."""
        if len(set1) == 0 and len(set2) == 0:
            return 1.0

        if len(set1) == 0 or len(set2) == 0:
            return 0.0

        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        return intersection / union if union > 0 else 0.0

    def analyze_instance(self, instance_id: str, temp_dir: str) -> dict:
        """
        Analyze a single instance and calculate localization correctness.

        Returns:
            Dictionary with analysis results
        """
        print(f'\nAnalyzing {instance_id}...')

        result = {
            'instance_id': instance_id,
            'success': False,
            'file_level_jaccard': 0.0,
            'function_level_jaccard': 0.0,
            'line_level_overlap': 0.0,
            'generated_locations': [],
            'golden_locations': [],
            'generated_files': [],
            'golden_files': [],
            'error': None,
        }

        # Get patches
        generated_patch = self.get_generated_patch(instance_id)
        if generated_patch is None:
            result['error'] = 'Generated patch not found'
            return result

        golden_patch = self.get_golden_patch(instance_id)
        if golden_patch is None:
            result['error'] = 'Golden patch not found in dataset'
            return result

        # Get repository info
        instance_data = self.dataset_dict.get(instance_id)
        if instance_data is None:
            result['error'] = 'Instance not found in dataset'
            return result

        repo_name = instance_data['repo']
        base_commit = instance_data['base_commit']

        # Clone and checkout repository
        repo_manager = RepositoryManager()
        repo_path = repo_manager.clone_and_checkout(repo_name, base_commit, temp_dir)

        if repo_path is None:
            result['error'] = 'Failed to clone/checkout repository'
            return result

        # Extract locations from patches
        parser = PatchParser()

        print('  Extracting locations from generated patch...')
        generated_locations = parser.extract_modified_locations(
            generated_patch, repo_path
        )

        print('  Extracting locations from golden patch...')
        golden_locations = parser.extract_modified_locations(golden_patch, repo_path)

        # Calculate similarities at different levels
        file_level_jaccard = self.calculate_file_level_similarity(
            generated_locations, golden_locations
        )
        function_level_jaccard = self.calculate_function_level_similarity(
            generated_locations, golden_locations
        )
        line_level_overlap = self.calculate_line_level_similarity(
            generated_patch, golden_patch, repo_path
        )

        # Identify test files in generated patch for reporting
        def is_test_file(file_path):
            path_lower = file_path.lower()
            parts = file_path.split('/')
            if any(
                part in ['test', 'tests', '__tests__', 'test_utils'] for part in parts
            ):
                return True
            if path_lower.startswith('test') or path_lower.startswith('tests/'):
                return True
            if 'test_' in path_lower or '_test' in path_lower:
                return True
            if path_lower.endswith('_test.py') or path_lower.endswith('_tests.py'):
                return True
            if path_lower.endswith('test.py') or path_lower.endswith('tests.py'):
                return True
            return False

        generated_files_all = sorted(
            list({loc.file_path for loc in generated_locations})
        )
        generated_test_files = [f for f in generated_files_all if is_test_file(f)]
        generated_non_test_files = [
            f for f in generated_files_all if not is_test_file(f)
        ]

        result['success'] = True
        result['file_level_jaccard'] = file_level_jaccard
        result['function_level_jaccard'] = function_level_jaccard
        result['line_level_overlap'] = line_level_overlap
        result['generated_locations'] = [repr(loc) for loc in generated_locations]
        result['golden_locations'] = [repr(loc) for loc in golden_locations]
        result['generated_files'] = generated_files_all
        result['generated_non_test_files'] = generated_non_test_files
        result['generated_test_files'] = generated_test_files
        result['golden_files'] = sorted(
            list({loc.file_path for loc in golden_locations})
        )
        result['num_generated_locations'] = len(generated_locations)
        result['num_golden_locations'] = len(golden_locations)

        # Calculate intersection at function level
        def normalize_location(loc: PatchLocation):
            if loc.is_global:
                return (loc.file_path, 'global', None, None)
            else:
                return (loc.file_path, loc.class_name, loc.function_name, 'function')

        gen_normalized = {normalize_location(loc) for loc in generated_locations}
        gold_normalized = {normalize_location(loc) for loc in golden_locations}
        result['num_function_level_intersection'] = len(
            gen_normalized.intersection(gold_normalized)
        )

        print('  Results:')
        print(f'    Generated locations: {len(generated_locations)}')
        print(f'    Golden locations: {len(golden_locations)}')
        print(f'    File-level Jaccard: {file_level_jaccard:.4f}')
        print(f'    Function-level Jaccard: {function_level_jaccard:.4f}')
        print(f'    Line-level overlap: {line_level_overlap:.4f}')

        return result

    def analyze_all(self, output_file: str = None, limit: int = None):
        """
        Analyze all instances in the evaluation output directory.

        Args:
            output_file: Path to save results JSON (optional)
            limit: Maximum number of instances to analyze (optional)
        """
        # Load dataset
        self.load_dataset()

        # Get list of instances
        eval_outputs_dir = os.path.join(self.eval_output_dir, 'eval_outputs')
        if not os.path.exists(eval_outputs_dir):
            print(f'Error: eval_outputs directory not found: {eval_outputs_dir}')
            return

        instance_dirs = [
            d
            for d in os.listdir(eval_outputs_dir)
            if os.path.isdir(os.path.join(eval_outputs_dir, d))
        ]

        if limit:
            instance_dirs = instance_dirs[:limit]

        print(f'Found {len(instance_dirs)} instances to analyze')

        # Create temporary directory for repository clones
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f'Using temporary directory: {temp_dir}')

            results = []

            for i, instance_id in enumerate(instance_dirs, 1):
                print(f'\n[{i}/{len(instance_dirs)}]')
                result = self.analyze_instance(instance_id, temp_dir)
                results.append(result)

                # Clean up the cloned repository to save space
                instance_data = self.dataset_dict.get(instance_id)
                if instance_data:
                    repo_name = instance_data['repo']
                    repo_path = os.path.join(temp_dir, repo_name.replace('/', '_'))
                    if os.path.exists(repo_path):
                        try:
                            shutil.rmtree(repo_path)
                        except Exception as e:
                            print(f'  Warning: Could not remove {repo_path}: {e}')

        # Calculate statistics
        successful = [r for r in results if r['success']]

        if successful:
            avg_file_level = sum(r['file_level_jaccard'] for r in successful) / len(
                successful
            )
            avg_function_level = sum(
                r['function_level_jaccard'] for r in successful
            ) / len(successful)
            avg_line_level = sum(r['line_level_overlap'] for r in successful) / len(
                successful
            )

            print('\n' + '=' * 60)
            print('SUMMARY')
            print('=' * 60)
            print(f'Total instances: {len(results)}')
            print(f'Successful analyses: {len(successful)}')
            print(f'Failed analyses: {len(results) - len(successful)}')
            print()
            print(f'Average File-level Jaccard: {avg_file_level:.4f}')
            print(f'Average Function-level Jaccard: {avg_function_level:.4f}')
            print(f'Average Line-level overlap: {avg_line_level:.4f}')

            # Distribution for each metric
            bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]

            def calculate_distribution(values):
                distribution = {
                    f'{bins[i]:.1f}-{bins[i + 1]:.1f}': 0 for i in range(len(bins) - 1)
                }
                for value in values:
                    for i in range(len(bins) - 1):
                        if bins[i] <= value <= bins[i + 1]:
                            distribution[f'{bins[i]:.1f}-{bins[i + 1]:.1f}'] += 1
                            break
                return distribution

            file_dist = calculate_distribution(
                [r['file_level_jaccard'] for r in successful]
            )
            function_dist = calculate_distribution(
                [r['function_level_jaccard'] for r in successful]
            )
            line_dist = calculate_distribution(
                [r['line_level_overlap'] for r in successful]
            )

            print('\nFile-level Jaccard distribution:')
            for range_str, count in file_dist.items():
                percentage = (count / len(successful)) * 100
                print(f'  {range_str}: {count} ({percentage:.1f}%)')

            print('\nFunction-level Jaccard distribution:')
            for range_str, count in function_dist.items():
                percentage = (count / len(successful)) * 100
                print(f'  {range_str}: {count} ({percentage:.1f}%)')

            print('\nLine-level overlap distribution:')
            for range_str, count in line_dist.items():
                percentage = (count / len(successful)) * 100
                print(f'  {range_str}: {count} ({percentage:.1f}%)')
        else:
            avg_file_level = avg_function_level = avg_line_level = 0.0
            file_dist = function_dist = line_dist = {}

        # Save results
        if output_file:
            output_path = output_file
        else:
            output_path = os.path.join(
                self.eval_output_dir, 'localization_analysis.json'
            )

        with open(output_path, 'w') as f:
            json.dump(
                {
                    'summary': {
                        'total_instances': len(results),
                        'successful': len(successful),
                        'failed': len(results) - len(successful),
                        'average_file_level_jaccard': avg_file_level,
                        'average_function_level_jaccard': avg_function_level,
                        'average_line_level_overlap': avg_line_level,
                        'file_level_distribution': file_dist,
                        'function_level_distribution': function_dist,
                        'line_level_distribution': line_dist,
                    },
                    'results': results,
                },
                f,
                indent=2,
            )

        print(f'\nResults saved to: {output_path}')


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Analyze patch localization correctness for SWE-bench evaluation outputs'
    )
    parser.add_argument(
        'eval_output_dir',
        help='Path to evaluation output directory (e.g., .../eval_outputs)',
    )
    parser.add_argument(
        '--dataset',
        default='princeton-nlp/SWE-bench_Verified',
        help='Dataset name (default: princeton-nlp/SWE-bench_Verified)',
    )
    parser.add_argument('--split', default='test', help='Dataset split (default: test)')
    parser.add_argument(
        '--output',
        help='Output JSON file path (default: <eval_output_dir>/localization_analysis.json)',
    )
    parser.add_argument(
        '--limit', type=int, help='Limit number of instances to analyze (for testing)'
    )

    args = parser.parse_args()

    # Validate input directory
    if not os.path.exists(args.eval_output_dir):
        print(f'Error: Directory not found: {args.eval_output_dir}')
        sys.exit(1)

    # Create analyzer and run analysis
    analyzer = LocalizationAnalyzer(args.eval_output_dir, args.dataset, args.split)
    analyzer.analyze_all(args.output, args.limit)


if __name__ == '__main__':
    main()

"""
python analyze_patch_localization.py /home/v-murongma/code/OpenHands/evaluation/evaluation_outputs/outputs/princeton-nlp__SWE-bench_Verified-test/CodeActAgent/Qwen3-Coder-30B-A3B-Instruct_maxiter_100_N_v0.59.0-no-hint-run_1  --output localization_results.json
"""
