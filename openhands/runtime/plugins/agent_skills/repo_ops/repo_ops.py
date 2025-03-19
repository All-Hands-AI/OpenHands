import collections
import json
import os
import pickle
import re
from collections import defaultdict
from copy import deepcopy
from typing import List, Optional

import networkx as nx

from openhands.runtime.plugins.agent_skills.repo_ops.repo_index.chunk_index.code_retriever import (
    build_code_retriever_from_repo as build_code_retriever,
)
from openhands.runtime.plugins.agent_skills.repo_ops.repo_index.dependency_graph import (
    EDGE_TYPE_CONTAINS,
    NODE_TYPE_CLASS,
    NODE_TYPE_DIRECTORY,
    NODE_TYPE_FILE,
    NODE_TYPE_FUNCTION,
    VALID_EDGE_TYPES,
    VALID_NODE_TYPES,
    RepoDependencySearcher,
    RepoEntitySearcher,
    build_graph,
    traverse_tree_structure,
)
from openhands.runtime.plugins.agent_skills.repo_ops.repo_index.dependency_graph.index_retriever import (
    build_module_retriever_from_graph as build_module_retriever,
)
from openhands.runtime.plugins.agent_skills.repo_ops.repo_index.dependency_graph.index_retriever import (
    build_retriever_from_persist_dir as load_retriever,
)
from openhands.runtime.plugins.agent_skills.repo_ops.repo_index.dependency_graph.index_retriever import (
    fuzzy_retrieve_from_graph_nodes as fuzzy_retrieve,
)
from openhands.runtime.plugins.agent_skills.repo_ops.repo_index.dependency_graph.traverse_graph import (
    is_test_file,
    traverse_json_structure,
)
from openhands.runtime.plugins.agent_skills.repo_ops.result_format import (
    QueryInfo,
    QueryResult,
)
from openhands.runtime.plugins.agent_skills.repo_ops.util import (
    # get_meta_data,
    find_matching_files_from_list,
    merge_intervals,
)

# from util.benchmark.setup_repo import setup_repo
# import subprocess
# import logging
# logger = logging.getLogger(__name__)

# from openhands.core.logger import openhands_logger as logger
# SET THIS IF YOU WANT TO USE THE PREPROCESSED FILES

REPO_PATH = os.environ.get('REPO_PATH', '')
BASE_INDEX_DIR = os.path.join(REPO_PATH, '_index_data')
GRAPH_INDEX_DIR = os.path.join(BASE_INDEX_DIR, 'graph_index_v2.3')
BM25_INDEX_DIR = os.path.join(BASE_INDEX_DIR, 'bm25_index')

# CURRENT_ISSUE_ID: str | None = None
# CURRENT_INSTANCE: dict | None = None
ALL_FILE: list | None = None
ALL_CLASS: list | None = None
ALL_FUNC: list | None = None

DP_GRAPH_ENTITY_SEARCHER: RepoEntitySearcher | None = None
DP_GRAPH_DEPENDENCY_SEARCHER: RepoDependencySearcher | None = None
DP_GRAPH: nx.MultiDiGraph | None = None


def parse_repo_index():
    # setup graph traverser
    global DP_GRAPH_ENTITY_SEARCHER, DP_GRAPH_DEPENDENCY_SEARCHER, DP_GRAPH
    graph_index_file = f'{GRAPH_INDEX_DIR}/code_graph.pkl'
    if not os.path.exists(graph_index_file):
        try:
            os.makedirs(GRAPH_INDEX_DIR, exist_ok=True)
            G = build_graph(REPO_PATH, global_import=True)
            with open(graph_index_file, 'wb') as f:
                pickle.dump(G, f)
            # logger.debug(f'Parsed repo `{REPO_PATH}`')
            print(f'Parsed repo `{REPO_PATH}`')
        except Exception as e:
            # logger.error(f'Error processing repo `{REPO_PATH}`: {e}')
            print(f'Error processing repo `{REPO_PATH}`: {e}')
    else:
        G = pickle.load(open(graph_index_file, 'rb'))

    DP_GRAPH_ENTITY_SEARCHER = RepoEntitySearcher(G)
    DP_GRAPH_DEPENDENCY_SEARCHER = RepoDependencySearcher(G)
    DP_GRAPH = G

    global ALL_FILE, ALL_CLASS, ALL_FUNC
    ALL_FILE = DP_GRAPH_ENTITY_SEARCHER.get_all_nodes_by_type(NODE_TYPE_FILE)
    ALL_CLASS = DP_GRAPH_ENTITY_SEARCHER.get_all_nodes_by_type(NODE_TYPE_CLASS)
    ALL_FUNC = DP_GRAPH_ENTITY_SEARCHER.get_all_nodes_by_type(NODE_TYPE_FUNCTION)

    # logging.debug(f'Set CURRENT_ISSUE_ID = {CURRENT_ISSUE_ID}')
    # logger.debug(f'Process repo {REPO_PATH} successfully.')
    print(f'Process repo {REPO_PATH} successfully.')


if REPO_PATH:
    # logger.debug(f'Begin to process repo {REPO_PATH}.')
    print(f'Begin to process repo {REPO_PATH}.')
    parse_repo_index()
else:
    # logger.debug("no need to process repo")
    print('no need to process repo')


def get_current_repo_modules():
    # global ALL_FILE, ALL_CLASS, ALL_FUNC
    return ALL_FILE, ALL_CLASS, ALL_FUNC


def get_graph_entity_searcher() -> RepoEntitySearcher:
    # global DP_GRAPH_ENTITY_SEARCHER
    return DP_GRAPH_ENTITY_SEARCHER


def get_graph_dependency_searcher() -> RepoDependencySearcher:
    # global DP_GRAPH_DEPENDENCY_SEARCHER
    return DP_GRAPH_DEPENDENCY_SEARCHER


def get_graph():
    # global DP_GRAPH
    assert DP_GRAPH is not None
    return DP_GRAPH


def get_module_name_by_line_num(file_path: str, line_num: int):
    # TODO:
    # if the given line isn't in a function of a class and the class is large,
    # find the nearest two member functions and return

    entity_searcher = get_graph_entity_searcher()
    dp_searcher = get_graph_dependency_searcher()

    cur_module = None
    if entity_searcher.has_node(file_path):
        module_nids, _ = dp_searcher.get_neighbors(
            file_path, etype_filter=[EDGE_TYPE_CONTAINS]
        )
        module_ndatas = entity_searcher.get_node_data(module_nids)
        for module in module_ndatas:
            if module['start_line'] <= line_num <= module['end_line']:
                cur_module = module  # ['node_id']
                break
        if cur_module and cur_module['type'] == NODE_TYPE_CLASS:
            func_nids, _ = dp_searcher.get_neighbors(
                cur_module['node_id'], etype_filter=[EDGE_TYPE_CONTAINS]
            )
            func_ndatas = entity_searcher.get_node_data(
                func_nids, return_code_content=True
            )
            for func in func_ndatas:
                if func['start_line'] <= line_num <= func['end_line']:
                    cur_module = func  # ['node_id']
                    break

    if cur_module:  # and cur_module['type'] in [NODE_TYPE_CLASS, NODE_TYPE_FUNCTION]
        return cur_module
        # module_ndata = entity_searcher.get_node_data([cur_module['node_id']], return_code_content=True)
        # return module_ndata[0]
    return None


def get_code_block_by_line_nums(query_info, context_window=20):
    # file_path: str, line_nums: List[int]
    searcher = get_graph_entity_searcher()

    file_path = query_info.file_path_or_pattern
    line_nums = query_info.line_nums
    cur_query_results = []

    file_data = searcher.get_node_data([file_path], return_code_content=False)[0]
    line_intervals = []
    res_modules = []
    # res_code_blocks = None
    for line in line_nums:
        # 首先检查是哪个module的代码
        module_data = get_module_name_by_line_num(file_path, line)

        # 如果不是某个module, 则搜索上下20行
        if not module_data:
            min_line_num = max(1, line - context_window)
            max_line_num = min(file_data['end_line'], line + context_window)
            line_intervals.append((min_line_num, max_line_num))

        elif module_data['node_id'] not in res_modules:
            query_result = QueryResult(
                query_info=query_info,
                format_mode='preview',
                nid=module_data['node_id'],
                ntype=module_data['type'],
                start_line=module_data['start_line'],
                end_line=module_data['end_line'],
                retrieve_src=f'Retrieved code context including {query_info.term}.',
            )
            cur_query_results.append(query_result)
            res_modules.append(module_data['node_id'])

    if line_intervals:
        line_intervals = merge_intervals(line_intervals)
        for interval in line_intervals:
            start_line, end_line = interval
            query_result = QueryResult(
                query_info=query_info,
                format_mode='code_snippet',
                nid=file_path,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                retrieve_src=f'Retrieved code context including {query_info.term}.',
            )
            cur_query_results.append(query_result)
        # res_code_blocks = line_wrap_content('\n'.join(file_content), line_intervals)

    # return res_code_blocks, res_modules
    return cur_query_results


def parse_node_id(nid: str):
    nfile = nid.split(':')[0]
    nname = nid.split(':')[-1]
    return nfile, nname


def search_entity_in_global_dict(
    term: str, include_files: Optional[List[str]] = None, prefix_term=None
):
    searcher = get_graph_entity_searcher()

    # TODO: hard code cases like "class Migration" and "function testing"
    if term.startswith(('class ', 'Class')):
        term = term[len('class ') :].strip()
    elif term.startswith(('function ', 'Function ')):
        term = term[len('function ') :].strip()
    elif term.startswith(('method ', 'Method ')):
        term = term[len('method ') :].strip()
    elif term.startswith('def '):
        term = term[len('def ') :].strip()

    # TODO: lower case if not find
    # TODO: filename xxx.py as key (also lowercase if not find)
    # global_name_dict = None
    if term in searcher.global_name_dict:
        global_name_dict = searcher.global_name_dict
        nids = global_name_dict[term]
    elif term.lower() in searcher.global_name_dict_lowercase:
        term = term.lower()
        global_name_dict = searcher.global_name_dict_lowercase
        nids = global_name_dict[term]
    else:
        return None

    node_datas = searcher.get_node_data(nids, return_code_content=False)
    found_entities_filter_dict = collections.defaultdict(list)
    for ndata in node_datas:
        nfile, _ = parse_node_id(ndata['node_id'])
        if not include_files or nfile in include_files:
            prefix_terms = []
            # candidite_prefixes = ndata['node_id'].lower().replace('.py', '').replace('/', '.').split('.')
            candidite_prefixes = re.split(
                r'[./:]', ndata['node_id'].lower().replace('.py', '')
            )[:-1]
            if prefix_term:
                prefix_terms = prefix_term.lower().split('.')
            if not prefix_term or all(
                [prefix in candidite_prefixes for prefix in prefix_terms]
            ):
                found_entities_filter_dict[ndata['type']].append(ndata['node_id'])

    return found_entities_filter_dict


def search_entity(query_info, include_files: List[str] = None):
    term = query_info.term
    searcher = get_graph_entity_searcher()
    # cur_result = ''
    continue_search = True

    cur_query_results = []

    # first: exact match in graph
    if searcher.has_node(term):
        continue_search = False
        query_result = QueryResult(
            query_info=query_info,
            format_mode='complete',
            nid=term,
            retrieve_src=f'Exact match found for entity name `{term}`.',
        )
        cur_query_results.append(query_result)

    # TODO: __init__ not exsit
    elif term.endswith('.__init__'):
        nid = term[: -(len('.__init__'))]
        if searcher.has_node(nid):
            continue_search = False
            node_data = searcher.get_node_data([nid], return_code_content=True)[0]
            query_result = QueryResult(
                query_info=query_info,
                format_mode='preview',
                nid=nid,
                ntype=node_data['type'],
                start_line=node_data['start_line'],
                end_line=node_data['end_line'],
                retrieve_src=f'Exact match found for entity name `{nid}`.',
            )
            cur_query_results.append(query_result)

    # second: search in global name dict
    if continue_search:
        found_entities_dict = search_entity_in_global_dict(term, include_files)
        if not found_entities_dict:
            found_entities_dict = search_entity_in_global_dict(term)

        use_sub_term = False
        used_term = term
        if not found_entities_dict and '.' in term:
            # for cases: class_name.method_name
            try:
                prefix_term = '.'.join(term.split('.')[:-1]).split()[
                    -1
                ]  # incase of 'class '/ 'function '
            except IndexError:
                prefix_term = None
            split_term = term.split('.')[-1].strip()
            used_term = split_term
            found_entities_dict = search_entity_in_global_dict(
                split_term, include_files, prefix_term
            )
            if not found_entities_dict:
                found_entities_dict = search_entity_in_global_dict(
                    split_term, prefix_term
                )
            if not found_entities_dict:
                use_sub_term = True
                found_entities_dict = search_entity_in_global_dict(split_term)

        # TODO: split the term and find in global dict

        if found_entities_dict:
            for ntype, nids in found_entities_dict.items():
                if not nids:
                    continue
                # if not continue_search: break

                # procee class and function in the same way
                if ntype in [NODE_TYPE_FUNCTION, NODE_TYPE_CLASS, NODE_TYPE_FILE]:
                    if len(nids) <= 3:
                        node_datas = searcher.get_node_data(
                            nids, return_code_content=True
                        )
                        for ndata in node_datas:
                            query_result = QueryResult(
                                query_info=query_info,
                                format_mode='preview',
                                nid=ndata['node_id'],
                                ntype=ndata['type'],
                                start_line=ndata['start_line'],
                                end_line=ndata['end_line'],
                                retrieve_src=f'Match found for entity name `{used_term}`.',
                            )
                            cur_query_results.append(query_result)
                        # continue_search = False
                    else:
                        node_datas = searcher.get_node_data(
                            nids, return_code_content=False
                        )
                        for ndata in node_datas:
                            query_result = QueryResult(
                                query_info=query_info,
                                format_mode='fold',
                                nid=ndata['node_id'],
                                ntype=ndata['type'],
                                retrieve_src=f'Match found for entity name `{used_term}`.',
                            )
                            cur_query_results.append(query_result)
                        if not use_sub_term:
                            continue_search = False
                        else:
                            continue_search = True

    # third: bm25 search (entity + content)
    if continue_search:
        module_nids = []

        # append the file name to keyword?
        # # if not any(symbol in file_path_or_pattern for symbol in ['*','?', '[', ']']):
        # term_with_file = f'{file_path_or_pattern}:{term}'
        # module_nids = bm25_module_retrieve(query=term_with_file, include_files=include_files)

        # search entity by keyword
        module_nids = bm25_module_retrieve(query=term, include_files=include_files)
        if not module_nids:
            module_nids = bm25_module_retrieve(query=term)

        if not module_nids:
            # result += f"No entity found using BM25 search. Try to use fuzzy search...\n"
            module_nids = fuzzy_retrieve(term, graph=get_graph(), similarity_top_k=3)

        module_datas = searcher.get_node_data(module_nids, return_code_content=True)
        showed_module_num = 0
        for module in module_datas[:5]:
            if module['type'] in [NODE_TYPE_FILE, NODE_TYPE_DIRECTORY]:
                query_result = QueryResult(
                    query_info=query_info,
                    format_mode='fold',
                    nid=module['node_id'],
                    ntype=module['type'],
                    retrieve_src='Retrieved entity using keyword search (bm25).',
                )
                cur_query_results.append(query_result)
            elif showed_module_num < 3:
                showed_module_num += 1
                query_result = QueryResult(
                    query_info=query_info,
                    format_mode='preview',
                    nid=module['node_id'],
                    ntype=module['type'],
                    start_line=module['start_line'],
                    end_line=module['end_line'],
                    retrieve_src='Retrieved entity using keyword search (bm25).',
                )
                cur_query_results.append(query_result)

    return (cur_query_results, continue_search)


def merge_query_results(query_results):
    priority = ['complete', 'code_snippet', 'preview', 'fold']
    merged_results = {}
    all_query_results: List[QueryResult] = []

    for qr in query_results:
        if qr.format_mode == 'code_snippet':
            all_query_results.append(qr)

        elif qr.nid and qr.nid in merged_results:
            # Merge query_info_list
            if qr.query_info_list[0] not in merged_results[qr.nid].query_info_list:
                merged_results[qr.nid].query_info_list.extend(qr.query_info_list)

            # Select the format_mode with the highest priority
            existing_format_mode = merged_results[qr.nid].format_mode
            if priority.index(qr.format_mode) < priority.index(existing_format_mode):
                merged_results[qr.nid].format_mode = qr.format_mode
                merged_results[qr.nid].start_line = qr.start_line
                merged_results[qr.nid].end_line = qr.end_line
                merged_results[qr.nid].retrieve_src = qr.retrieve_src

        elif qr.nid:
            merged_results[qr.nid] = qr

    all_query_results += list(merged_results.values())
    return all_query_results


def rank_and_aggr_query_results(query_results, fixed_query_info_list):
    query_info_list_dict = {}

    for qr in query_results:
        # Convert the query_info_list to a tuple so it can be used as a dictionary key
        key = tuple(qr.query_info_list)

        if key in query_info_list_dict:
            query_info_list_dict[key].append(qr)
        else:
            query_info_list_dict[key] = [qr]

    # for the key: sort by query
    def sorting_key(key):
        # Find the first matching element index from fixed_query_info_list in the key (tuple of query_info_list)
        for i, fixed_query in enumerate(fixed_query_info_list):
            if fixed_query in key:
                return i
        # If no match is found, assign a large index to push it to the end
        return len(fixed_query_info_list)

    sorted_keys = sorted(query_info_list_dict.keys(), key=sorting_key)
    sorted_query_info_list_dict = {
        key: query_info_list_dict[key] for key in sorted_keys
    }

    # for the value: sort by format priority
    priority = {
        'complete': 1,
        'code_snippet': 2,
        'preview': 3,
        'fold': 4,
    }  # Lower value indicates higher priority
    # TODO: merge the same node in 'code_snippet' and 'preview'

    organized_dict = {}
    for key, values in sorted_query_info_list_dict.items():
        nested_dict = {priority_key: [] for priority_key in priority.keys()}
        for qr in values:
            # Place the qr in the nested dictionary based on its format_mode
            if qr.format_mode in nested_dict:
                nested_dict[qr.format_mode].append(qr)

        # Only add keys with non-empty lists to keep the result clean
        organized_dict[key] = {k: v for k, v in nested_dict.items() if v}

    return organized_dict


def search_code_snippets(
    search_terms: Optional[List[str]] = None,
    line_nums: Optional[List] = None,
    file_path_or_pattern: Optional[str] = '**/*.py',
) -> str:
    """Searches the codebase to retrieve relevant code snippets based on given queries(terms or line numbers).

    This function supports retrieving the complete content of a code entity,
    searching for code entities such as classes or functions by keywords, or locating specific lines within a file.
    It also supports filtering searches based on a file path or file pattern.

    Note:
    1. If `search_terms` are provided, it searches for code snippets based on each term:
        - If a term is formatted as 'file_path:QualifiedName' (e.g., 'src/helpers/math_helpers.py:MathUtils.calculate_sum') ,
          or just 'file_path', the corresponding complete code is retrieved or file content is retrieved.
        - If a term matches a file, class, or function name, matched entities are retrieved.
        - If there is no match with any module name, it attempts to find code snippets that likely contain the term.

    2. If `line_nums` is provided, it searches for code snippets at the specified lines within the file defined by
       `file_path_or_pattern`.

    Args:
        search_terms (Optional[List[str]]): A list of names, keywords, or code snippets to search for within the codebase.
            Terms can be formatted as 'file_path:QualifiedName' to search for a specific module or entity within a file
            (e.g., 'src/helpers/math_helpers.py:MathUtils.calculate_sum') or as 'file_path' to retrieve the complete content
            of a file. This can also include potential function names, class names, or general code fragments.

        line_nums (Optional[List[int]]): Specific line numbers to locate code snippets within a specified file.
            When provided, `file_path_or_pattern` must specify a valid file path.

        file_path_or_pattern (Optional[str]): A glob pattern or specific file path used to filter search results
            to particular files or directories. Defaults to '**/*.py', meaning all Python files are searched by default.
            If `line_nums` are provided, this must specify a specific file path.

    Returns:
        str: The search results, which may include code snippets, matching entities, or complete file content.


    Example Usage:
        # Search for the full content of a specific file
        result = search_code_snippets(search_terms=['src/my_file.py'])

        # Search for a specific function
        result = search_code_snippets(search_terms=['src/my_file.py:MyClass.func_name'])

        # Search for specific lines (10 and 15) within a file
        result = search_code_snippets(line_nums=[10, 15], file_path_or_pattern='src/example.py')

        # Combined search for a module name and within a specific file pattern
        result = search_code_snippets(search_terms=["MyClass"], file_path_or_pattern="src/**/*.py")
    """

    files, _, _ = get_current_repo_modules()
    all_file_paths = [file['name'] for file in files]

    result = ''
    # exclude_files = find_matching_files_from_list(all_file_paths, "**/test*/**")
    if file_path_or_pattern:
        include_files = find_matching_files_from_list(
            all_file_paths, file_path_or_pattern
        )
        if not include_files:
            include_files = all_file_paths
            result += f"No files found for file pattern '{file_path_or_pattern}'. Will search all files.\n...\n"
    else:
        include_files = all_file_paths

    query_info_list = []
    all_query_results = []

    if search_terms:
        # search all terms together
        filter_terms = []
        for term in search_terms:
            if is_test_file(term):
                result += f'No results for test files: `{term}`. Please do not search for any test files.\n\n'
            else:
                filter_terms.append(term)

        joint_terms = deepcopy(filter_terms)
        if len(filter_terms) > 1:
            filter_terms.append(' '.join(filter_terms))

        for i, term in enumerate(filter_terms):
            term = term.strip().strip('.')
            if not term:
                continue

            query_info = QueryInfo(term=term)
            query_info_list.append(query_info)

            cur_query_results = []

            # search entity
            query_results, continue_search = search_entity(
                query_info=query_info, include_files=include_files
            )
            cur_query_results.extend(query_results)

            # search content
            # if continue_search:
            #     query_results = bm25_content_retrieve(query_info=query_info, include_files=include_files)
            #     cur_query_results.extend(query_results)

            # elif i != (len(filter_terms)-1):
            #     joint_terms[i] = ''
            #     filter_terms[-1] = ' '.join([t for t in joint_terms if t.strip()])
            #     if filter_terms[-1] in filter_terms[:-1]:
            #         filter_terms[-1] = ''

            all_query_results.extend(cur_query_results)

    if file_path_or_pattern in all_file_paths and line_nums:
        if isinstance(line_nums, int):
            line_nums = [line_nums]
        file_path = file_path_or_pattern
        term = file_path + ':line ' + ', '.join([str(line) for line in line_nums])
        # result += f"Search `line(s) {line_nums}` in file `{file_path}` ...\n"
        query_info = QueryInfo(
            term=term, line_nums=line_nums, file_path_or_pattern=file_path
        )

        # Search for codes based on file name and line number
        query_results = get_code_block_by_line_nums(query_info)
        all_query_results.extend(query_results)

    merged_results = merge_query_results(all_query_results)
    ranked_query_to_results = rank_and_aggr_query_results(
        merged_results, query_info_list
    )

    # format output
    # format_mode: 'complete', 'preview', 'code_snippet', 'fold': 4
    searcher = get_graph_entity_searcher()

    for query_infos, format_to_results in ranked_query_to_results.items():
        term_desc = ', '.join([f'"{query.term}"' for query in query_infos])
        result += f'##Searching for term {term_desc}...\n'
        result += '### Search Result:\n'
        cur_result = ''
        for format_mode, query_results in format_to_results.items():
            if format_mode == 'fold':
                cur_retrieve_src = ''
                for qr in query_results:
                    if not cur_retrieve_src:
                        cur_retrieve_src = qr.retrieve_src

                    if cur_retrieve_src != qr.retrieve_src:
                        cur_result += 'Source: ' + cur_retrieve_src + '\n\n'
                        cur_retrieve_src = qr.retrieve_src

                    cur_result += qr.format_output(searcher)

                cur_result += 'Source: ' + cur_retrieve_src + '\n'
                if len(query_results) > 1:
                    cur_result += 'Hint: Use more detailed query to get the full content of some if needed.\n'
                else:
                    cur_result += f'Hint: Search `{query_results[0].nid}` for the full content if needed.\n'
                cur_result += '\n'

            elif format_mode == 'complete':
                for qr in query_results:
                    cur_result += qr.format_output(searcher)
                    cur_result += '\n'

            elif format_mode == 'preview':
                # Remove the small modules, leaving only the large ones
                filtered_results = []
                grouped_by_file = defaultdict(list)
                for qr in query_results:
                    if (qr.end_line - qr.start_line) < 100:
                        grouped_by_file[qr.file_path].append(qr)
                    else:
                        filtered_results.append(qr)

                for file_path, results in grouped_by_file.items():
                    # Sort by start_line and then by end_line in descending order
                    sorted_results = sorted(
                        results, key=lambda qr: (qr.start_line, -qr.end_line)
                    )

                    max_end_line = -1
                    for qr in sorted_results:
                        # If the current QueryResult's range is not completely covered by the largest range seen so far, keep it
                        if qr.end_line > max_end_line:
                            filtered_results.append(qr)
                            max_end_line = max(max_end_line, qr.end_line)

                # filtered_results = query_results
                for qr in filtered_results:
                    cur_result += qr.format_output(searcher)
                    cur_result += '\n'

            elif format_mode == 'code_snippet':
                for qr in query_results:
                    cur_result += qr.format_output(searcher)
                    cur_result += '\n'

        cur_result += '\n\n'

        if cur_result.strip():
            result += cur_result
        else:
            result += 'No locations found.\n\n'

    return result.strip()


def get_entity_contents(entity_names: List[str]):
    """
    Retrieves the complete implementations of specified entities from the codebase.

    This function allows searching for function implementations, class definitions, or entire file contents
    based on the provided entity names. Entity names can be specified in the following formats:

    - `file_path:QualifiedName` (e.g., `'src/helpers/math_helpers.py:MathUtils.calculate_sum'`)
      to retrieve a specific function or class definition.
    - `file_path` (e.g., `'src/my_file.py'`) to retrieve the entire content of a file.

    Args:
        entity_names (List[str]):
            A list of entity names to query. Each entity name can represent a function, class, or file.

    Returns:
        Dict[str, str]:
            A dictionary mapping each entity name to its corresponding implementation or file content.

    Example:
        >>> get_entity_contents(['src/my_file.py:MyClass.func_name'])
        >>> get_entity_contents(['src/my_file.py'])
    """

    searcher = get_graph_entity_searcher()

    result = ''
    for name in entity_names:
        name = name.strip().strip('.')
        if not name:
            continue

        result += f'##Searching for entity `{name}`...\n'
        result += '### Search Result:\n'
        query_info = QueryInfo(term=name)

        if searcher.has_node(name):
            query_result = QueryResult(
                query_info=query_info,
                format_mode='complete',
                nid=name,
                retrieve_src=f'Exact match found for entity name `{name}`.',
            )
            result += query_result.format_output(searcher)
            result += '\n\n'
        else:
            result += 'Invalid name. \nHint: Valid entity name should be formatted as "file_path:QualifiedName" or just "file_path".'
            result += '\n\n'
    return result.strip()


def bm25_module_retrieve(
    query: str,
    include_files: Optional[List[str]] = None,
    # file_pattern: Optional[str] = None,
    search_scope: str = 'all',
    similarity_top_k: int = 10,
    # sort_by_type = False
):
    retriever = build_module_retriever(
        entity_searcher=get_graph_entity_searcher(),
        search_scope=search_scope,
        similarity_top_k=similarity_top_k,
    )
    try:
        retrieved_nodes = retriever.retrieve(query)
    except IndexError as e:
        # logger.warning(f'{e}. Probably because the query `{query}` is too short.')
        print(f'{e}. Probably because the query `{query}` is too short.')
        return []

    filter_nodes = []
    all_nodes = []
    for node in retrieved_nodes:
        if node.score <= 0:
            continue
        if not include_files or node.text.split(':')[0] in include_files:
            filter_nodes.append(node.text)
        all_nodes.append(node.text)

    if filter_nodes:
        return filter_nodes
    else:
        return all_nodes


def bm25_content_retrieve(
    query_info: QueryInfo,
    # query: str,
    include_files: Optional[List[str]] = None,
    # file_pattern: Optional[str] = None,
    similarity_top_k: int = 10,
) -> str:
    """Retrieves code snippets from the codebase using the BM25 algorithm based on the provided query, class names, and function names. This function helps in finding relevant code sections that match specific criteria, aiding in code analysis and understanding.

    Args:
        query (Optional[str]): A textual query to search for relevant code snippets. Defaults to an empty string if not provided.
        class_names (list[str]): A list of class names to include in the search query. If None, class names are not included.
        function_names (list[str]): A list of function names to include in the search query. If None, function names are not included.
        file_pattern (Optional[str]): A glob pattern to filter search results to specific file types or directories. If None, the search includes all files.
        similarity_top_k (int): The number of top similar documents to retrieve based on the BM25 ranking. Defaults to 15.

    Returns:
        str: A formatted string containing the search results, including file paths and the retrieved code snippets (the partial code of a module or the skeleton of the specific module).
    """

    # instance = get_current_issue_data()
    # instance_id = get_current_issue_id()
    query = query_info.term

    # persist_path = os.path.join(BM25_INDEX_DIR, instance_id)
    if os.path.exists(f'{BM25_INDEX_DIR}/corpus.jsonl'):
        # TODO: if similairy_top_k > cache's setting, then regenerate
        retriever = load_retriever(BM25_INDEX_DIR)
    else:
        # repo_path = get_repo_save_dir()
        # repo_dir = setup_repo(instance_data=instance, repo_base_dir=repo_playground,
        # dataset=None, split=None)
        # absolute_repo_dir = os.path.abspath(REPO_SAVE_DIR)
        retriever = build_code_retriever(
            REPO_PATH, persist_path=BM25_INDEX_DIR, similarity_top_k=similarity_top_k
        )

    # similarity: {score}
    cur_query_results = []
    retrieved_nodes = retriever.retrieve(query)
    for node in retrieved_nodes:
        file = node.metadata['file_path']
        # print(node.metadata)
        if not include_files or file in include_files:
            # drop the import code
            # if len(node.metadata['span_ids']) == 1 and node.metadata['span_ids'][0] == 'imports':
            #     continue
            if all(
                [
                    span_id in ['docstring', 'imports', 'comments']
                    for span_id in node.metadata['span_ids']
                ]
            ):
                # TODO: drop ?
                query_result = QueryResult(
                    query_info=query_info,
                    format_mode='code_snippet',
                    nid=node.metadata['file_path'],
                    file_path=node.metadata['file_path'],
                    start_line=node.metadata['start_line'],
                    end_line=node.metadata['end_line'],
                    retrieve_src='Retrieved code content using keyword search (bm25).',
                )
                cur_query_results.append(query_result)

            elif any(
                [
                    span_id in ['docstring', 'imports', 'comments']
                    for span_id in node.metadata['span_ids']
                ]
            ):
                nids = []
                for span_id in node.metadata['span_ids']:
                    nid = f'{file}:{span_id}'
                    searcher = get_graph_entity_searcher()
                    if searcher.has_node(nid):
                        nids.append(nid)
                    # TODO: warning if not find

                node_datas = searcher.get_node_data(nids, return_code_content=True)
                sorted_ndatas = sorted(node_datas, key=lambda x: x['start_line'])
                sorted_nids = [ndata['node_id'] for ndata in sorted_ndatas]

                message = ''
                if sorted_nids:
                    if sorted_ndatas[0]['start_line'] < node.metadata['start_line']:
                        nid = sorted_ndatas[0]['node_id']
                        ntype = sorted_ndatas[0]['type']
                        # The code for {ntype} {nid} is incomplete; search {nid} for the full content if needed.
                        message += f'The code for {ntype} `{nid}` is incomplete; search `{nid}` for the full content if needed.\n'
                    if sorted_ndatas[-1]['end_line'] > node.metadata['end_line']:
                        nid = sorted_ndatas[-1]['node_id']
                        ntype = sorted_ndatas[-1]['type']
                        message += f'The code for {ntype} `{nid}` is incomplete; search `{nid}` for the full content if needed.\n'
                    if message.strip():
                        message = 'Hint: \n' + message

                nids_str = ', '.join([f'`{nid}`' for nid in sorted_nids])
                desc = f'Found {nids_str}.'
                query_result = QueryResult(
                    query_info=query_info,
                    format_mode='code_snippet',
                    nid=node.metadata['file_path'],
                    file_path=node.metadata['file_path'],
                    start_line=node.metadata['start_line'],
                    end_line=node.metadata['end_line'],
                    desc=desc,
                    message=message,
                    retrieve_src='Retrieved code content using keyword search (bm25).',
                )

                cur_query_results.append(query_result)
            else:
                for span_id in node.metadata['span_ids']:
                    nid = f'{file}:{span_id}'
                    searcher = get_graph_entity_searcher()
                    if searcher.has_node(nid):
                        ndata = searcher.get_node_data([nid], return_code_content=True)[
                            0
                        ]
                        query_result = QueryResult(
                            query_info=query_info,
                            format_mode='preview',
                            nid=ndata['node_id'],
                            ntype=ndata['type'],
                            start_line=ndata['start_line'],
                            end_line=ndata['end_line'],
                            retrieve_src='Retrieved code content using keyword search (bm25).',
                        )
                        cur_query_results.append(query_result)
                    else:
                        continue

        cur_query_results = cur_query_results[:5]
        return cur_query_results


def _validate_graph_explorer_inputs(
    start_entities: List[str],
    direction: str = 'downstream',
    traversal_depth: int = 1,
    node_type_filter: Optional[List[str]] = None,
    edge_type_filter: Optional[List[str]] = None,
):
    """evaluate input arguments"""

    # assert len(invalid_entities) == 0, (
    #     f"Invalid value for `start_entities`: entities {invalid_entities} are not in the repository graph."
    # )
    assert direction in ['downstream', 'upstream', 'both'], (
        "Invalid value for `direction`: Expected one of 'downstream', 'upstream', and 'both'. "
        f"Received: '{direction}'."
    )
    assert traversal_depth == -1 or traversal_depth >= 0, (
        'Invalid value for `traversal_depth`: It must be either -1 or a non-negative integer (>= 0). '
        f'Received: {traversal_depth}.'
    )
    if isinstance(node_type_filter, list):
        invalid_ntypes = []
        for ntype in invalid_ntypes:
            if ntype not in VALID_NODE_TYPES:
                invalid_ntypes.append(ntype)
        assert (
            len(invalid_ntypes) == 0
        ), f'Invalid node types {invalid_ntypes} in node_type_filter. Expected node type in {VALID_NODE_TYPES}'
    if isinstance(edge_type_filter, list):
        invalid_etypes = []
        for etype in edge_type_filter:
            if etype not in VALID_EDGE_TYPES:
                invalid_etypes.append(etype)
        assert (
            len(invalid_etypes) == 0
        ), f'Invalid edge types {invalid_etypes} in edge_type_filter. Expected edge type in {VALID_EDGE_TYPES}'

    graph = get_graph()
    entity_searcher = get_graph_entity_searcher()

    hints = ''
    valid_entities = []
    for i, root in enumerate(start_entities):
        # process node name
        if root != '/':
            root = root.strip('/')
        if root.endswith('.__init__'):
            root = root[: -(len('.__init__'))]

        # validate node name
        if root not in graph:
            # search with bm25
            module_nids = bm25_module_retrieve(query=root)
            module_datas = entity_searcher.get_node_data(
                module_nids, return_code_content=False
            )
            if len(module_datas) > 0:
                hints += f'The entity name `{root}` is invalid. Based on your input, here are some candidate entities you might be referring to:\n'
                for module in module_datas[:5]:
                    ntype = module['type']
                    nid = module['node_id']
                    hints += f'{ntype}: `{nid}`\n'
                hints += 'Source: Retrieved entity using keyword search (bm25).\n\n'
            else:
                hints += f'The entity name `{root}` is invalid. There are no possible candidate entities in record.\n'
        elif is_test_file(root):
            hints += f'No results for the test entity: `{root}`. Please do not include any test entities.\n\n'
        else:
            valid_entities.append(root)

    return valid_entities, hints


def explore_tree_structure(
    start_entities: List[str],
    direction: str = 'downstream',
    traversal_depth: int = 2,
    entity_type_filter: Optional[List[str]] = None,
    dependency_type_filter: Optional[List[str]] = None,
):
    """Analyzes and displays the dependency structure around specified entities in a code graph.

    This function searches and presents relationships and dependencies for the specified entities (such as classes, functions, files, or directories) in a code graph.
    It explores how the input entities relate to others, using defined types of dependencies, including 'contains', 'imports', 'invokes' and 'inherits'.
    The search can be controlled to traverse upstream (exploring dependencies that entities rely on) or downstream (exploring how entities impact others), with optional limits on traversal depth and filters for entity and dependency types.

    Example Usage:
    1. Exploring Outward Dependencies:
        ```
        get_local_structure(
            start_entities=['src/module_a.py:ClassA'],
            direction='downstream',
            traversal_depth=2,
            entity_type_filter=['class', 'function'],
            dependency_type_filter=['invokes', 'imports']
        )
        ```
        This retrieves the dependencies of `ClassA` up to 2 levels deep, focusing only on classes and functions with 'invokes' and 'imports' relationships.

    2. Exploring Inward Dependencies:
        ```
        get_local_structure(
            start_entities=['src/module_b.py:FunctionY'],
            direction='upstream',
            traversal_depth=-1
        )
        ```
        This finds all entities that depend on `FunctionY` without restricting the traversal depth.

    Notes:
    * Traversal Control: The `traversal_depth` parameter specifies how deep the function should explore the graph starting from the input entities.
    * Filtering: Use `entity_type_filter` and `dependency_type_filter` to narrow down the scope of the search, focusing on specific entity types and relationships.
    * Graph Context: The function operates on a pre-built code graph containing entities (e.g., files, classes and functions) and dependencies representing their interactions and relationships.

    Parameters:
    ----------
    start_entities : list[str]
        List of entities (e.g., class, function, file, or directory paths) to begin the search from.
        - Entities representing classes or functions must be formatted as "file_path:QualifiedName"
          (e.g., `interface/C.py:C.method_a.inner_func`).
        - For files or directories, provide only the file or directory path (e.g., `src/module_a.py` or `src/`).

    direction : str, optional
        Direction of traversal in the code graph; allowed options are:
        - 'upstream': Traversal to explore dependencies that the specified entities rely on (how they depend on others).
        - 'downstream': Traversal to explore the effects or interactions of the specified entities on others
          (how others depend on them).
        - 'both': Traversal in both directions.
        Default is 'downstream'.

    traversal_depth : int, optional
        Maximum depth of traversal. A value of -1 indicates unlimited depth (subject to a maximum limit).
        Must be either `-1` or a non-negative integer (≥ 0).
        Default is 2.

    entity_type_filter : list[str], optional
        List of entity types (e.g., 'class', 'function', 'file', 'directory') to include in the traversal.
        If None, all entity types are included.
        Default is None.

    dependency_type_filter : list[str], optional
        List of dependency types (e.g., 'contains', 'imports', 'invokes', 'inherits') to include in the traversal.
        If None, all dependency types are included.
        Default is None.

    Returns:
    -------
    result : object
        An object representing the traversal results, which includes discovered entities and their dependencies.
    """
    start_entities, hints = _validate_graph_explorer_inputs(
        start_entities,
        direction,
        traversal_depth,
        entity_type_filter,
        dependency_type_filter,
    )
    G = get_graph()

    # return_json = True
    return_json = False
    if return_json:
        rtns = {
            node: traverse_json_structure(
                G,
                node,
                direction,
                traversal_depth,
                entity_type_filter,
                dependency_type_filter,
            )
            for node in start_entities
        }
        rtn_str = json.dumps(rtns)
    else:
        rtns = [
            traverse_tree_structure(
                G,
                node,
                direction,
                traversal_depth,
                entity_type_filter,
                dependency_type_filter,
            )
            for node in start_entities
        ]
        rtn_str = '\n\n'.join(rtns)

    if hints.strip():
        rtn_str += '\n\n' + hints
    return rtn_str.strip()


__all__ = [
    'get_entity_contents',
    'search_code_snippets',
    'explore_tree_structure',
]
