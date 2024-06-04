"""
Mostly borrow from: https://github.com/paul-gauthier/aider/blob/main/aider/repomap.py
"""

import os
import warnings
from collections import Counter, defaultdict, namedtuple
from importlib import resources
from pathlib import Path
from typing import Any, Set

import networkx as nx
from diskcache import Cache
from grep_ast import TreeContext, filename_to_lang
from pygments.lexers import guess_lexer_for_filename
from pygments.token import Token
from pygments.util import ClassNotFound
from tqdm import tqdm

from opendevin.indexing.repomap.io import InputOutput
from opendevin.llm.llm import LLM

# tree_sitter is throwing a FutureWarning
warnings.simplefilter('ignore', category=FutureWarning)
from tree_sitter_languages import get_language, get_parser  # noqa: E402

Tag = namedtuple('Tag', ('rel_fname', 'fname', 'line', 'name', 'kind'))


class RepoMap:
    """
    The RepoMap class represents a mapping of a repository's files and their associated tags.
    """

    CACHE_VERSION = 3
    TAGS_CACHE_DIR = f'.aider.tags.cache.v{CACHE_VERSION}'

    cache_missing = False

    warned_files: Set[str] = set()

    def __init__(
        self,
        llm: LLM,
        io=None,
        map_tokens=1024,
        root=None,
        repo_content_prefix=None,
        verbose=False,
        max_context_window=None,
    ):
        """
        Initialize the Repomap object.

        Args:
            llm (LLM): The LLM object used for token counting.
            io (InputOutput): The InputOutput object used for file I/O operations.
            map_tokens (int, optional): The maximum number of tokens to map. Defaults to 1024.
            root (str, optional): The root directory path. If not provided, the current working directory is used. Defaults to None.
            repo_content_prefix (str, optional): The prefix to add to the repository content paths. Defaults to None.
            verbose (bool, optional): Whether to enable verbose mode. Defaults to False.
            max_context_window (int, optional): The maximum context window size. Defaults to None.
        """

        self.io = io if io else InputOutput()
        self.verbose = verbose

        if not root:
            root = os.getcwd()
        self.root = root

        self.load_tags_cache()

        self.max_map_tokens = map_tokens
        self.max_context_window = max_context_window

        self.token_count = llm.get_token_count_from_text
        self.repo_content_prefix = repo_content_prefix

    def get_repo_map(
        self, chat_files, other_files, mentioned_fnames=None, mentioned_idents=None
    ):
        """
        Generate a repository map based on the provided files and parameters.

        Args:
            chat_files (list): List of files in the chat.
            other_files (list): List of other files in the repository.
            mentioned_fnames (set, optional): Set of mentioned filenames. Defaults to None.
            mentioned_idents (set, optional): Set of mentioned identifiers. Defaults to None.

        Returns:
            str: The generated repository map as a string.
        """

        if self.max_map_tokens <= 0:
            return
        if not other_files:
            return
        if not mentioned_fnames:
            mentioned_fnames = set()
        if not mentioned_idents:
            mentioned_idents = set()

        max_map_tokens = self.max_map_tokens

        # With no files in the chat, give a bigger view of the entire repo
        MUL = 16
        padding = 4096
        if max_map_tokens and self.max_context_window:
            target = min(max_map_tokens * MUL, self.max_context_window - padding)
        else:
            target = 0
        if not chat_files and self.max_context_window and target > 0:
            max_map_tokens = target

        try:
            files_listing = self.get_ranked_tags_map(
                chat_files,
                other_files,
                max_map_tokens,
                mentioned_fnames,
                mentioned_idents,
            )
        except RecursionError:
            self.io.tool_error('Disabling repo map, git repo too large?')
            self.max_map_tokens = 0
            return

        if not files_listing:
            return

        num_tokens = self.token_count(files_listing)
        if self.verbose:
            self.io.tool_output(f'Repo-map: {num_tokens/1024:.1f} k-tokens')

        if chat_files:
            other = 'other '
        else:
            other = ''

        if self.repo_content_prefix:
            repo_content = self.repo_content_prefix.format(other=other)
        else:
            repo_content = ''

        repo_content += files_listing

        return repo_content

    def get_rel_fname(self, fname):
        """
        Returns the relative path of a file with respect to the root directory.

        Args:
            fname (str): The absolute path of the file.

        Returns:
            str: The relative path of the file.
        """
        return os.path.relpath(fname, self.root)

    def load_tags_cache(self):
        """
        Loads the tags cache from the specified path.

        If the cache directory does not exist, sets the `cache_missing` flag to True.
        """
        path = Path(self.root) / self.TAGS_CACHE_DIR
        if not path.exists():
            self.cache_missing = True
        self.TAGS_CACHE = Cache(path)

    def save_tags_cache(self):
        pass

    def get_mtime(self, fname):
        """
        Get the modification time of a file.

        Args:
            fname (str): The path to the file.

        Returns:
            float: The modification time of the file in seconds since the epoch.

        Raises:
            FileNotFoundError: If the file is not found.
        """
        try:
            return os.path.getmtime(fname)
        except FileNotFoundError:
            self.io.tool_error(f'File not found error: {fname}')

    def get_tags(self, fname, rel_fname):
        """
        Retrieves the tags associated with a file.

        Args:
            fname (str): The absolute path of the file.
            rel_fname (str): The relative path of the file.

        Returns:
            list: A list of tags associated with the file.
        """
        # Check if the file is in the cache and if the modification time has not changed
        file_mtime = self.get_mtime(fname)
        if file_mtime is None:
            return []

        cache_key = fname
        if (
            cache_key in self.TAGS_CACHE
            and self.TAGS_CACHE[cache_key]['mtime'] == file_mtime
        ):
            return self.TAGS_CACHE[cache_key]['data']

        # miss!

        data = list(self.get_tags_raw(fname, rel_fname))

        # Update the cache
        self.TAGS_CACHE[cache_key] = {'mtime': file_mtime, 'data': data}
        self.save_tags_cache()
        return data

    def get_tags_raw(self, fname, rel_fname):
        """
        Retrieves tags from the given file.

        Args:
            fname (str): The absolute path of the file.
            rel_fname (str): The relative path of the file.

        Yields:
            Tag: A Tag object representing a tag found in the file.

        Returns:
            None: If the language of the file is not supported or if the file is empty.
        """
        lang = filename_to_lang(fname)
        if not lang:
            return

        language = get_language(lang)
        parser = get_parser(lang)

        # Load the tags queries
        try:
            scm_fname = (
                resources.files(__package__)
                .joinpath('queries')
                .joinpath(f'tree-sitter-{lang}-tags.scm')
            )
        except KeyError:
            return
        query_scm = str(scm_fname)
        if not Path(query_scm).exists():
            return
        query_scm = scm_fname.read_text()

        code = self.io.read_text(fname)
        if not code:
            return
        tree = parser.parse(bytes(code, 'utf-8'))

        # Run the tags queries
        query = language.query(query_scm)
        captures = query.captures(tree.root_node)

        captures = list(captures)

        saw = set()
        for node, tag in captures:
            if tag.startswith('name.definition.'):
                kind = 'def'
            elif tag.startswith('name.reference.'):
                kind = 'ref'
            else:
                continue

            saw.add(kind)

            result = Tag(
                rel_fname=rel_fname,
                fname=fname,
                name=node.text.decode('utf-8'),
                kind=kind,
                line=node.start_point[0],
            )

            yield result

        if 'ref' in saw:
            return
        if 'def' not in saw:
            return

        # We saw defs, without any refs
        # Some tags files only provide defs (cpp, for example)
        # Use pygments to backfill refs

        try:
            lexer = guess_lexer_for_filename(fname, code)
        except ClassNotFound:
            return

        tokens = list(lexer.get_tokens(code))
        tokens = [token[1] for token in tokens if token[0] in Token.Name]

        for token in tokens:
            yield Tag(
                rel_fname=rel_fname,
                fname=fname,
                name=token,
                kind='ref',
                line=-1,
            )

    def get_ranked_tags(
        self, chat_fnames, other_fnames, mentioned_fnames, mentioned_idents
    ):
        """
        Returns a list of ranked tags based on the provided file names and mentioned identifiers.

        Args:
            chat_fnames (list): List of file names from the chat.
            other_fnames (list): List of other file names.
            mentioned_fnames (list): List of mentioned file names.
            mentioned_idents (list): List of mentioned identifiers.

        Returns:
            list: A list of ranked tags.
        """
        defines = defaultdict(set)
        references = defaultdict(list)
        definitions = defaultdict(set)

        personalization = dict()

        fnames_set = set(chat_fnames).union(set(other_fnames))
        chat_rel_fnames = set()

        fnames = sorted(fnames_set)

        # Default personalization for unspecified files is 1/num_nodes
        # https://networkx.org/documentation/stable/_modules/networkx/algorithms/link_analysis/pagerank_alg.html#pagerank
        personalize = 10 / len(fnames)

        if self.cache_missing:
            fnames = tqdm(fnames)
        self.cache_missing = False

        for fname in fnames:
            if not Path(fname).is_file():
                if fname not in self.warned_files:
                    if Path(fname).exists():
                        self.io.tool_error(
                            f"Repo-map can't include {fname}, it is not a normal file"
                        )
                    else:
                        self.io.tool_error(
                            f"Repo-map can't include {fname}, it no longer exists"
                        )

                self.warned_files.add(fname)
                continue

            # dump(fname)
            rel_fname = self.get_rel_fname(fname)

            if fname in chat_fnames:
                personalization[rel_fname] = personalize
                chat_rel_fnames.add(rel_fname)

            if fname in mentioned_fnames:
                personalization[rel_fname] = personalize

            tags = list(self.get_tags(fname, rel_fname))

            for tag in tags:
                if tag.kind == 'def':
                    defines[tag.name].add(rel_fname)
                    key = (rel_fname, tag.name)
                    definitions[key].add(tag)

                if tag.kind == 'ref':
                    references[tag.name].append(rel_fname)

        ##
        # dump(defines)
        # dump(references)
        # dump(personalization)

        if not references:
            references = defaultdict(list)
            for k, v in defines.items():
                references[k] = list(v)

        idents = set(defines.keys()).intersection(set(references.keys()))

        G = nx.MultiDiGraph()

        for ident in idents:
            definers = defines[ident]
            if ident in mentioned_idents:
                mul = 10
            else:
                mul = 1
            for referencer, num_refs in Counter(references[ident]).items():
                for definer in definers:
                    # if referencer == definer:
                    #    continue
                    G.add_edge(referencer, definer, weight=mul * num_refs, ident=ident)

        if not references:
            pass

        if personalization:
            pers_args = dict(personalization=personalization, dangling=personalization)
        else:
            pers_args = dict()

        try:
            ranked = nx.pagerank(G, weight='weight', **pers_args)
        except ZeroDivisionError:
            return []

        # distribute the rank from each source node, across all of its out edges
        ranked_definitions: Any = defaultdict(float)
        for src in G.nodes:
            src_rank = ranked[src]
            total_weight = sum(
                data['weight'] for _src, _dst, data in G.out_edges(src, data=True)
            )
            # dump(src, src_rank, total_weight)
            for _src, dst, data in G.out_edges(src, data=True):
                data['rank'] = src_rank * data['weight'] / total_weight
                ident = data['ident']
                ranked_definitions[(dst, ident)] += data['rank']

        ranked_tags = []
        ranked_definitions = sorted(
            ranked_definitions.items(), reverse=True, key=lambda x: x[1]
        )

        # dump(ranked_definitions)

        for (fname, ident), rank in ranked_definitions:
            # print(f"{rank:.03f} {fname} {ident}")
            if fname in chat_rel_fnames:
                continue
            ranked_tags += list(definitions.get((fname, ident), []))

        rel_other_fnames_without_tags = set(
            self.get_rel_fname(fname) for fname in other_fnames
        )

        fnames_already_included = set(rt[0] for rt in ranked_tags)

        top_rank = sorted(
            [(rank, node) for (node, rank) in ranked.items()], reverse=True
        )
        for rank, fname in top_rank:
            if fname in rel_other_fnames_without_tags:
                rel_other_fnames_without_tags.remove(fname)
            if fname not in fnames_already_included:
                ranked_tags.append((fname,))

        for fname in rel_other_fnames_without_tags:
            ranked_tags.append((fname,))

        return ranked_tags

    def get_ranked_tags_map(
        self,
        chat_fnames,
        other_fnames=None,
        max_map_tokens=None,
        mentioned_fnames=None,
        mentioned_idents=None,
    ):
        """
        Returns the best tree representation of ranked tags based on the given parameters.

        Args:
            chat_fnames (list): A list of chat filenames.
            other_fnames (list, optional): A list of other filenames. Defaults to None.
            max_map_tokens (int, optional): The maximum number of tokens allowed in the map. Defaults to None.
            mentioned_fnames (set, optional): A set of mentioned filenames. Defaults to None.
            mentioned_idents (set, optional): A set of mentioned identifiers. Defaults to None.

        Returns:
            The best tree representation of ranked tags.
        """
        if not other_fnames:
            other_fnames = list()
        if not max_map_tokens:
            max_map_tokens = self.max_map_tokens
        if not mentioned_fnames:
            mentioned_fnames = set()
        if not mentioned_idents:
            mentioned_idents = set()

        ranked_tags = self.get_ranked_tags(
            chat_fnames, other_fnames, mentioned_fnames, mentioned_idents
        )

        num_tags = len(ranked_tags)
        lower_bound = 0
        upper_bound = num_tags
        best_tree = None
        best_tree_tokens = 0

        chat_rel_fnames = {self.get_rel_fname(fname) for fname in chat_fnames}

        # Guess a small starting number to help with giant repos
        middle = min(max_map_tokens // 25, num_tags)

        self.tree_cache = dict()

        while lower_bound <= upper_bound:
            tree = self.to_tree(ranked_tags[:middle], chat_rel_fnames)
            num_tokens = self.token_count(tree)

            if num_tokens < max_map_tokens and num_tokens > best_tree_tokens:
                best_tree = tree
                best_tree_tokens = num_tokens

            if num_tokens < max_map_tokens:
                lower_bound = middle + 1
            else:
                upper_bound = middle - 1

            middle = (lower_bound + upper_bound) // 2

        return best_tree

    tree_cache: Any = dict()

    def render_tree(self, abs_fname, rel_fname, lois):
        """
        Renders the tree for a given file and lines of interest (lois).

        Args:
            abs_fname (str): The absolute file path.
            rel_fname (str): The relative file path.
            lois (list): A list of lines of interest.

        Returns:
            str: The rendered tree.
        """
        key = (rel_fname, tuple(sorted(lois)))

        if key in self.tree_cache:
            return self.tree_cache[key]

        code = self.io.read_text(abs_fname) or ''
        if not code.endswith('\n'):
            code += '\n'

        context = TreeContext(
            rel_fname,
            code,
            color=False,
            line_number=False,
            child_context=False,
            last_line=False,
            margin=0,
            mark_lois=False,
            loi_pad=0,
            # header_max=30,
            show_top_of_file_parent_scope=False,
        )

        context.add_lines_of_interest(lois)
        context.add_context()
        res = context.format()
        self.tree_cache[key] = res
        return res

    def to_tree(self, tags, chat_rel_fnames):
        """
        Converts a list of tags into a tree-like structure.

        Args:
            tags (list): A list of tags.
            chat_rel_fnames (list): A list of chat relative filenames.

        Returns:
            str: The tree-like structure as a string.
        """
        if not tags:
            return ''

        tags = [tag for tag in tags if tag[0] not in chat_rel_fnames]
        tags = sorted(tags)

        cur_fname: Any = None
        cur_abs_fname = None
        lois: Any = None
        output = ''

        # add a bogus tag at the end so we trip the this_fname != cur_fname...
        dummy_tag = (None,)
        for tag in tags + [dummy_tag]:
            this_rel_fname = tag[0]

            # ... here ... to output the final real entry in the list
            if this_rel_fname != cur_fname:
                if lois is not None:
                    output += cur_fname + ':\n'
                    output += self.render_tree(cur_abs_fname, cur_fname, lois)
                    lois = None
                elif cur_fname:
                    output += '\n' + cur_fname + '\n'

                if type(tag) is Tag:
                    lois = []
                    cur_abs_fname = tag.fname
                cur_fname = this_rel_fname

            if lois is not None:
                lois.append(tag.line)

        # truncate long lines, in case we get minified js or something else crazy
        output = '\n'.join([line[:100] for line in output.splitlines()]) + '\n'

        return output
