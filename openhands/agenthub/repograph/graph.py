"""
RepoGraph analyzer module for OpenHands.
Adapted from https://github.com/ozyyshr/RepoGraph
"""

import os
import ast
import re
import warnings
import builtins
import inspect
import networkx as nx
from collections import namedtuple
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from tqdm import tqdm
from pygments.lexers import guess_lexer_for_filename
from pygments.token import Token
from pygments.util import ClassNotFound
from tree_sitter_languages import get_language, get_parser

from .utils import create_structure

# Suppress tree_sitter FutureWarning
warnings.simplefilter("ignore", category=FutureWarning)

Tag = namedtuple("Tag", "rel_fname fname line name kind category info")

class RepoGraphAnalyzer:
    """Repository-level code graph analyzer."""

    def __init__(
        self,
        root: str,
        map_tokens: int = 1024,
        max_context_window: Optional[int] = None,
        verbose: bool = False,
    ):
        """Initialize the RepoGraph analyzer.
        
        Args:
            root: Root directory of the repository
            map_tokens: Maximum number of tokens to map
            max_context_window: Maximum context window size
            verbose: Enable verbose output
        """
        self.root = root if root else os.getcwd()
        self.max_map_tokens = map_tokens
        self.max_context_window = max_context_window
        self.verbose = verbose
        self.warned_files: Set[str] = set()
        self.structure = create_structure(self.root)

    def analyze(self, files: List[str], mentioned_files: Optional[Set[str]] = None) -> Tuple[List[Dict[str, Any]], nx.MultiDiGraph]:
        """Analyze the repository and build a code graph.
        
        Args:
            files: List of files to analyze
            mentioned_files: Set of files that were mentioned/referenced
            
        Returns:
            Tuple containing tags and the code graph
        """
        if self.max_map_tokens <= 0 or not files:
            return [], nx.MultiDiGraph()

        mentioned_files = mentioned_files or set()
        tags = self._get_tag_files(files, mentioned_files)
        code_graph = self._tag_to_graph(tags)
        return tags, code_graph

    def _get_tag_files(self, files: List[str], mentioned_files: Set[str]) -> List[Dict[str, Any]]:
        """Get tags for the given files."""
        try:
            return self._get_ranked_tags(files, mentioned_files)
        except RecursionError:
            if self.verbose:
                print("Warning: Disabling code graph, git repo too large?")
            self.max_map_tokens = 0
            return []

    def _tag_to_graph(self, tags: List[Dict[str, Any]]) -> nx.MultiDiGraph:
        """Convert tags to a NetworkX graph."""
        G = nx.MultiDiGraph()
        
        # Add nodes
        for tag in tags:
            G.add_node(tag['name'], 
                      category=tag['category'], 
                      info=tag['info'],
                      fname=tag['fname'],
                      line=tag['line'],
                      kind=tag['kind'])

        # Add edges for class methods
        for tag in tags:
            if tag['category'] == 'class':
                class_funcs = tag['info'].split('\t')
                for f in class_funcs:
                    G.add_edge(tag['name'], f.strip())

        # Add edges for references
        tags_ref = [tag for tag in tags if tag['kind'] == 'ref']
        tags_def = [tag for tag in tags if tag['kind'] == 'def']
        for tag in tags_ref:
            for tag_def in tags_def:
                if tag['name'] == tag_def['name']:
                    G.add_edge(tag['name'], tag_def['name'])
        
        return G

    def _get_tags(self, fname: str, rel_fname: str) -> List[Tag]:
        """Get tags for a single file."""
        file_mtime = self._get_mtime(fname)
        if file_mtime is None:
            return []
        return list(self._get_tags_raw(fname, rel_fname))

    def _get_tags_raw(self, fname: str, rel_fname: str):
        """Extract raw tags from a file."""
        # Get file structure
        ref_fname_lst = rel_fname.split('/')
        s = self.structure
        for fname_part in ref_fname_lst:
            s = s[fname_part]
        structure_classes = {item['name']: item for item in s.get('classes', [])}
        structure_functions = {item['name']: item for item in s.get('functions', [])}
        structure_class_methods = {}
        for cls in s.get('classes', []):
            for item in cls.get('methods', []):
                structure_class_methods[item['name']] = item
        structure_all_funcs = {**structure_functions, **structure_class_methods}

        # Get language and parser
        lang = self._get_file_language(fname)
        if not lang:
            return
        language = get_language(lang)
        parser = get_parser(lang)

        # Load and parse code
        try:
            with open(str(fname), "r", encoding='utf-8') as f:
                code = f.read()
                codelines = f.readlines()
        except Exception:
            return

        # Clean code
        code = self._clean_code(code)
        
        # Parse code
        tree = parser.parse(bytes(code, "utf-8"))
        try:
            tree_ast = ast.parse(code)
        except:
            tree_ast = None

        # Get standard and builtin functions
        std_funcs, std_libs = self._get_std_funcs(code, fname)
        builtin_funcs = self._get_builtin_funcs()

        # Run tags query
        query = language.query(self._get_tags_query())
        captures = query.captures(tree.root_node)

        saw = set()
        for node, tag in captures:
            if tag.startswith("name.definition."):
                kind = "def"
            elif tag.startswith("name.reference."):
                kind = "ref"
            else:
                continue

            saw.add(kind)
            cur_cdl = codelines[node.start_point[0]]
            category = 'class' if 'class ' in cur_cdl else 'function'
            tag_name = node.text.decode("utf-8")
            
            # Skip standard/builtin functions
            if (tag_name in std_funcs or 
                tag_name in std_libs or 
                tag_name in builtin_funcs):
                continue

            if category == 'class':
                class_functions = [item['name'] for item in structure_classes[tag_name]['methods']]
                if kind == 'def':
                    line_nums = [structure_classes[tag_name]['start_line'], 
                               structure_classes[tag_name]['end_line']]
                else:
                    line_nums = [node.start_point[0], node.end_point[0]]
                
                yield Tag(
                    rel_fname=rel_fname,
                    fname=fname,
                    name=tag_name,
                    kind=kind,
                    category=category,
                    info='\n'.join(class_functions),
                    line=line_nums,
                )

            elif category == 'function':
                if kind == 'def':
                    cur_cdl = '\n'.join(structure_all_funcs[tag_name]['text'])
                    line_nums = [structure_all_funcs[tag_name]['start_line'],
                               structure_all_funcs[tag_name]['end_line']]
                else:
                    line_nums = [node.start_point[0], node.end_point[0]]

                yield Tag(
                    rel_fname=rel_fname,
                    fname=fname,
                    name=tag_name,
                    kind=kind,
                    category=category,
                    info=cur_cdl,
                    line=line_nums,
                )

        # Backfill references using pygments if needed
        if "ref" in saw or "def" not in saw:
            return

        try:
            lexer = guess_lexer_for_filename(fname, code)
            tokens = list(lexer.get_tokens(code))
            tokens = [token[1] for token in tokens if token[0] in Token.Name]

            for token in tokens:
                yield Tag(
                    rel_fname=rel_fname,
                    fname=fname,
                    name=token,
                    kind="ref",
                    line=-1,
                    category='function',
                    info='none',
                )
        except ClassNotFound:
            return

    def _get_ranked_tags(self, files: List[str], mentioned_files: Set[str]) -> List[Dict[str, Any]]:
        """Get ranked tags for multiple files."""
        tags_of_files = []
        personalization = {}
        files = sorted(set(files))
        personalize = 10 / len(files)

        for fname in tqdm(files, disable=not self.verbose):
            if not Path(fname).is_file():
                if fname not in self.warned_files:
                    if Path(fname).exists():
                        if self.verbose:
                            print(f"Warning: Code graph can't include {fname}, it is not a normal file")
                    else:
                        if self.verbose:
                            print(f"Warning: Code graph can't include {fname}, it no longer exists")
                self.warned_files.add(fname)
                continue

            rel_fname = os.path.relpath(fname, self.root)
            if fname in mentioned_files:
                personalization[rel_fname] = personalize
            
            tags = list(self._get_tags(fname, rel_fname))
            if tags is not None:
                tags_of_files.extend(tags)

        return tags_of_files

    def _get_mtime(self, fname: str) -> Optional[float]:
        """Get file modification time."""
        try:
            return os.path.getmtime(fname)
        except FileNotFoundError:
            if self.verbose:
                print(f"Warning: File not found: {fname}")
            return None

    def _get_file_language(self, fname: str) -> Optional[str]:
        """Get the programming language of a file."""
        ext = os.path.splitext(fname)[1].lower()
        if ext == '.py':
            return 'python'
        # Add more language mappings as needed
        return None

    def _get_tags_query(self) -> str:
        """Get the tree-sitter query for tags."""
        return """
        (class_definition
        name: (identifier) @name.definition.class) @definition.class

        (function_definition
        name: (identifier) @name.definition.function) @definition.function

        (call
        function: [
            (identifier) @name.reference.call
            (attribute
                attribute: (identifier) @name.reference.call)
        ]) @reference.call
        """

    def _clean_code(self, code: str) -> str:
        """Clean code for parsing."""
        code = code.replace('\ufeff', '')
        code = code.replace('constants.False', '_False')
        code = code.replace('constants.True', '_True')
        code = code.replace("False", "_False")
        code = code.replace("True", "_True")
        code = code.replace("DOMAIN\\username", "DOMAIN\\\\username")
        code = code.replace("Error, ", "Error as ")
        code = code.replace('Exception, ', 'Exception as ')
        code = code.replace("print ", "yield ")
        pattern = r'except\s+\(([^,]+)\s+as\s+([^)]+)\):'
        code = re.sub(pattern, r'except (\1, \2):', code)
        code = code.replace("raise AttributeError as aname", "raise AttributeError")
        return code

    def _get_std_funcs(self, code: str, fname: str) -> Tuple[List[str], List[str]]:
        """Get standard library functions and imports."""
        try:
            tree = ast.parse(code)
            codelines = code.split('\n')
            std_libs = []
            std_funcs = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    import_statement = codelines[node.lineno-1]
                    for alias in node.names:
                        import_name = alias.name.split('.')[0]
                        if import_name not in fname:
                            try:
                                exec(import_statement.strip())
                                std_libs.append(alias.name)
                                eval_name = alias.asname or alias.name
                                std_funcs.extend([name for name, member in inspect.getmembers(eval(eval_name)) if callable(member)])
                            except:
                                continue

                elif isinstance(node, ast.ImportFrom):
                    import_statement = codelines[node.lineno-1]
                    if node.module is None:
                        continue
                    module_name = node.module.split('.')[0]
                    if module_name not in fname:
                        if "(" in import_statement:
                            for ln in range(node.lineno-1, len(codelines)):
                                if ")" in codelines[ln]:
                                    code_num = ln
                                    break
                            import_statement = '\n'.join(codelines[node.lineno-1:code_num+1])
                        try:
                            exec(import_statement.strip())
                            for alias in node.names:
                                std_libs.append(alias.name)
                                eval_name = alias.asname or alias.name
                                if eval_name == "*":
                                    continue
                                std_funcs.extend([name for name, member in inspect.getmembers(eval(eval_name)) if callable(member)])
                        except:
                            continue

            return std_funcs, std_libs
        except:
            return [], []

    def _get_builtin_funcs(self) -> List[str]:
        """Get built-in Python functions."""
        builtin_funcs = []
        builtin_funcs.extend(dir(builtins))
        builtin_funcs.extend(dir(list))
        builtin_funcs.extend(dir(dict))
        builtin_funcs.extend(dir(set))
        builtin_funcs.extend(dir(str))
        builtin_funcs.extend(dir(tuple))
        return builtin_funcs