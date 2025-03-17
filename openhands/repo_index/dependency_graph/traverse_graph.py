import re
from collections import defaultdict
from typing import Optional, List

import networkx as nx

from dependency_graph.build_graph import (
    VALID_EDGE_TYPES, VALID_NODE_TYPES, 
    NODE_TYPE_FILE, NODE_TYPE_CLASS, NODE_TYPE_FUNCTION,
    EDGE_TYPE_CONTAINS
)

def is_test_file(nid):
    # input node id (e.g., 'tests/_core.py:test') and output whether it belongs to a test file
    file_path = nid.split(':')[0]
    word_list = re.split(r" |_|\/", file_path.lower())  # split by ' ', '_', and '/'
    return any([word.startswith('test') for word in word_list])


def wrap_code_snippet(code_snippet, start_line, end_line):
    lines = code_snippet.split("\n")
    max_line_number = start_line + len(lines) - 1
    if not start_line == end_line == 1:  # which is a file
        assert max_line_number == end_line
    number_width = len(str(max_line_number))
    return (f"```\n"
            + "\n".join(f"{str(i + start_line).rjust(number_width)} | {line}" for i, line in enumerate(lines))
            + "\n```")


def add_quotes_to_nodes(G):
    H = nx.MultiDiGraph()

    # Map old node names to new node names
    node_mapping = {node: f'"{node}"' for node in G.nodes}

    # Add nodes with updated names and copy attributes
    for node, new_name in node_mapping.items():
        H.add_node(new_name)

    # Add edges with updated node names
    for u, v, data in G.edges(data=True):
        H.add_edge(node_mapping[u], node_mapping[v], type=data['type'])
        # H.add_edge(u, v, type=key, **data)

    return H


class RepoEntitySearcher:
    """Retrieve Entity IDs and Code Snippets from Repository Graph"""

    def __init__(self, graph):
        self.G = graph
        self._global_name_dict = None
        self._global_name_dict_lowercase = None
        self._etypes_dict = {
            etype: i for i, etype in enumerate(VALID_EDGE_TYPES)
        }

    @property
    def global_name_dict(self):
        if self._global_name_dict is None:  # Compute only once
            _global_name_dict = defaultdict(list)
            for nid in self.G.nodes():
                if is_test_file(nid): continue

                if nid.endswith('.py'):
                    fname = nid.split('/')[-1]
                    _global_name_dict[fname].append(nid)

                    name = nid[:-(len('.py'))].split('/')[-1]
                    _global_name_dict[name].append(nid)

                elif ':' in nid:
                    name = nid.split(':')[-1].split('.')[-1]
                    _global_name_dict[name].append(nid)

            self._global_name_dict = _global_name_dict
        return self._global_name_dict


    @property
    def global_name_dict_lowercase(self):
        if self._global_name_dict_lowercase is None:  # Compute only once
            _global_name_dict_lowercase = defaultdict(list)
            for nid in self.G.nodes():
                if is_test_file(nid): continue

                if nid.endswith('.py'):
                    fname = nid.split('/')[-1].lower()
                    _global_name_dict_lowercase[fname].append(nid)

                    name = nid[:-(len('.py'))].split('/')[-1].lower()
                    _global_name_dict_lowercase[name].append(nid)

                elif ':' in nid:
                    name = nid.split(':')[-1].split('.')[-1].lower()
                    _global_name_dict_lowercase[name].append(nid)

            self._global_name_dict_lowercase = _global_name_dict_lowercase
        return self._global_name_dict_lowercase


    def has_node(self, nid, include_test=False):
        if not include_test and is_test_file(nid):
            return False
        return nid in self.G


    def get_node_data(self, nids, return_code_content=False, wrap_with_ln=True):
        rtn = []
        for nid in nids:
            node_data = self.G.nodes[nid]
            formatted_data = {
                'node_id': nid,
                'type': node_data['type'],
                # 'code_content': node.get('code', ''),
                # 'start_line': node_data.get('start_line', 0),
                # 'end_line': node_data.get('end_line', 0)
            }
            if node_data.get('code', ""):
                if 'start_line' in node_data:
                    formatted_data['start_line'] = node_data['start_line']
                    start_line = node_data['start_line']
                elif formatted_data['type'] == NODE_TYPE_FILE:
                    start_line = 1
                    formatted_data['start_line'] = start_line
                else:
                    start_line = 1

                if 'end_line' in node_data:
                    formatted_data['end_line'] = node_data['end_line']
                    end_line = node_data['end_line']
                elif formatted_data['type'] == NODE_TYPE_FILE:
                    end_line = len(node_data['code'].split("\n")) # - 1
                    formatted_data['end_line'] = end_line
                else:
                    end_line = 1
                # load formatted code data
                if return_code_content and wrap_with_ln:
                    formatted_data['code_content'] = wrap_code_snippet(
                        node_data['code'], start_line, end_line)
                elif return_code_content:
                    formatted_data['code_content'] = node_data['code']
            rtn.append(formatted_data)
        return rtn
    
    
    def get_all_nodes_by_type(self, type):
        assert type in VALID_NODE_TYPES
        nodes = []
        for nid in self.G.nodes():
            if is_test_file(nid): continue
            if self.G.nodes[nid]['type'] == type:
                node_data = self.G.nodes[nid]
                if type == NODE_TYPE_FILE:
                    formatted_data = {
                        'name': nid,
                        'type': node_data['type'],
                        'content': node_data.get('code', '').split('\n')
                    }
                elif type == NODE_TYPE_FUNCTION:
                    formatted_data = {
                        'name': nid.split(':')[-1],
                        'file': nid.split(':')[0],
                        'type': node_data['type'],
                        'content': node_data.get('code', '').split('\n'),
                        'start_line': node_data.get('start_line', 0),
                        'end_line': node_data.get('end_line', 0)
                    }
                elif type == NODE_TYPE_CLASS:
                    formatted_data = {
                        'name': nid.split(':')[-1],
                        'file': nid.split(':')[0],
                        'type': node_data['type'],
                        'content': node_data.get('code', '').split('\n'),
                        'start_line': node_data.get('start_line', 0),
                        'end_line': node_data.get('end_line', 0),
                        'methods': []
                    }
                    dp_searcher = RepoDependencySearcher(self.G)
                    methods = dp_searcher.get_neighbors(nid, 'forward', 
                                                        ntype_filter=[NODE_TYPE_FUNCTION],
                                                        etype_filter=[EDGE_TYPE_CONTAINS])[0]
                    formatted_methods = []
                    for mid in methods:
                        mnode = self.G.nodes[mid]
                        formatted_methods.append({
                            'name': mid.split('.')[-1],
                            'start_line': mnode.get('start_line', 0),
                            'end_line': mnode.get('end_line', 0),
                        })
                    formatted_data['methods'] = formatted_methods
                nodes.append(formatted_data)
        return nodes


class RepoDependencySearcher:
    """Traverse Repository Graph"""

    def __init__(self, graph):
        self.G = graph
        self._etypes_dict = {
            etype: i for i, etype in enumerate(VALID_EDGE_TYPES)
        }

    def subgraph(self, nids):
        return self.G.subgraph(nids)

    def get_neighbors(self, nid, direction='forward',
                      ntype_filter=None, etype_filter=None, ignore_test_file=True):
        nodes, edges = [], []
        if direction == 'forward':
            for sn in self.G.successors(nid):
                if ntype_filter and self.G.nodes[sn]['type'] not in ntype_filter:
                    continue
                if ignore_test_file and is_test_file(sn):
                    continue
                for key, edge_data in self.G.get_edge_data(nid, sn).items():
                    etype = edge_data['type']
                    if etype_filter and etype not in etype_filter:
                        continue
                    edges.append((nid, sn, self._etypes_dict[etype], {'type': etype}))
                    nodes.append(sn)

        elif direction == 'backward':
            for pn in self.G.predecessors(nid):
                if ntype_filter and self.G.nodes[pn]['type'] not in ntype_filter:
                    continue
                if ignore_test_file and is_test_file(pn):
                    continue
                for key, edge_data in self.G.get_edge_data(pn, nid).items():
                    etype = edge_data['type']
                    if etype_filter and etype not in etype_filter:
                        continue
                    edges.append((pn, nid, self._etypes_dict[etype], {'type': etype}))
                    nodes.append(pn)

        return nodes, edges


def traverse_graph_structure(G, roots, direction='downstream', hops=2,
                             node_type_filter: Optional[List[str]] = None,
                             edge_type_filter: Optional[List[str]] = None):
    if hops == -1:
        hops = 20

    searcher = RepoDependencySearcher(G)

    ## traverse graph using BFS with type filter and direction control
    subG = nx.MultiDiGraph()
    subG.add_nodes_from(roots)
    frontiers, visited = [(nid, 0) for nid in roots], []

    while frontiers:
        nid, level = frontiers.pop()
        if nid in visited or abs(level) >= hops:
            continue
        visited.append(nid)

        # Filter by hop
        # etype_filter = edge_type_filter[abs(level)] if isinstance(edge_type_filter,
        #                                                           list) else edge_type_filter
        # ntype_filter = node_type_filter[abs(level)] if isinstance(node_type_filter,
        #                                                           list) else node_type_filter
        ntype_filter, etype_filter = node_type_filter, edge_type_filter

        # if direction == 'both', we only search bidirectionally at level == 0 and perform
        # unidirectional search for other levels (e.g., when level < 0 perform backward search
        # and when level > 0 perform forward search)
        if level > 0 or (level == 0 and (direction == 'downstream' or direction == 'both')):
            nodes, edges = searcher.get_neighbors(nid,
                                                  'forward',
                                                  ntype_filter=ntype_filter,
                                                  etype_filter=etype_filter,
                                                  ignore_test_file=True)
            frontiers.extend([(nid, level + 1) for nid in nodes])
            subG.add_edges_from(edges)  # return the path in a graph format

        if level < 0 or (level == 0 and (direction == 'upstream' or direction == 'both')):
            nodes, edges = searcher.get_neighbors(nid,
                                                  'backward',
                                                  ntype_filter=ntype_filter,
                                                  etype_filter=etype_filter,
                                                  ignore_test_file=True)
            frontiers.extend([(nid, level - 1) for nid in nodes])
            subG.add_edges_from(edges)  # return the path in a graph format

    ## [optional] use subgraph
    # subG = searcher.subgraph(subG.nodes)

    if subG.number_of_nodes() == 0:
        return ''

    ## encoding graph to text
    # encode_type = 'incident-index'
    # encode_type = 'incident'
    # encode_type = 'raw'
    encode_type = 'pydot'
    if encode_type == 'raw':
        rtn = str(list(subG.edges(data='type')))
    elif encode_type == 'data':
        return {
            'node_data': searcher.get_node_data(subG.nodes, True),
            'edge_list': list(subG.edges(data='type')),
        }
    elif encode_type == 'pydot':
        H = add_quotes_to_nodes(subG)
        pydot_graph = nx.drawing.nx_pydot.to_pydot(H)
        dot_string = pydot_graph.to_string()
        cleaned_dot_string = re.sub(r'\bkey=\d+,\s*', '', dot_string)
        return cleaned_dot_string
    elif 'incident' in encode_type:
        rtn_strs = []
        n_index_dict = {}
        if encode_type == 'incident-index':
            s = ""
            for i, node in enumerate(subG.nodes()):
                s += f'Map {G.nodes[node]["type"]} {node} to index {i}.\n'
                n_index_dict[node] = i
            rtn_strs.append(s[:-1])

        for node in subG.nodes():
            incident_dict = defaultdict(lambda: defaultdict(list))
            ntype = G.nodes[node]['type']
            for neigh in subG.neighbors(node):
                neigh_type = G.nodes[neigh]['type']
                for key, edge_data in subG.get_edge_data(node, neigh).items():
                    etype = edge_data['type']
                    incident_dict[etype][neigh_type].append(neigh)
            s = ""
            for i, (edge_type, neigh_dict) in enumerate(incident_dict.items()):
                if i == 0:
                    if encode_type == 'incident-index':
                        s += f'{ntype} {n_index_dict[node]} '
                    else:
                        s += f'{ntype} "{node}" '
                s += f'{edge_type} '
                # s += f'\n\t- {edge_type} '
                for neigh_type, neigh_list in neigh_dict.items():
                    if encode_type == 'incident-index':
                        neigh_list = [str(n_index_dict[neigh]) for neigh in neigh_list]
                    else:
                        neigh_list = ['"' + neigh + '"' for neigh in neigh_list]
                    s += f'{neigh_type} {",".join(neigh_list)} '
                s = s[:-1] + '; and '
                # s = s[:-1] + ';'
            if len(s) > 0:
                s = s[:-6] + '.'
                # s = s[:-1]
                rtn_strs.append(s)
        rtn = "\n\n".join(rtn_strs)
    else:
        raise NotImplementedError

    return rtn


def traverse_tree_structure(G, root, direction='downstream', hops=2,
                            node_type_filter: Optional[List[str]] = None,
                            edge_type_filter: Optional[List[str]] = None):
    if hops == -1:
        hops = 20

    rtn_str = []  # return tree string
    traversed_nodes = set()  # ignore all the traversed edges
    traversed_edges = set()  # ignore all the traversed nodes

    def traverse(node, prefix, is_last, level, edge_type, edirection):
        if level > hops:
            return

        if node == root and level == 0:
            rtn_str.append(f"{node}")
            new_prefix = ''
            edirection = direction
        else:
            connector = '└── ' if is_last else '├── '
            connector += f"{edge_type} ── "
            rtn_str.append(f"{prefix}{connector}{node}")
            new_prefix = prefix + (' ' if is_last else '│') + ' ' * (len(connector) - 1)

        if node in traversed_nodes:
            return
        traversed_nodes.add(node)

        neigh_ids, etypes, edirs = [], [], []

        def is_ntype_not_valid(_ntype):
            return node_type_filter is not None and _ntype not in node_type_filter

        def is_etype_not_valid(_etype):
            return edge_type_filter is not None and _etype not in edge_type_filter

        if 'downstream' == edirection or (node == root and direction == 'both'):
        # if 'downstream' == edirection or direction == 'both':
            for neighbor in G.successors(node):
                neigh_type = G.nodes[neighbor]['type']
                if is_ntype_not_valid(neigh_type):
                    continue
                edges = G[node][neighbor]
                for key in edges:
                    etype = edges[key]['type']
                    if is_etype_not_valid(etype):
                        continue
                    if not is_test_file(neighbor):
                        if (node, etype, neighbor) not in traversed_edges:
                            neigh_ids.append(neighbor)
                            etypes.append(etype)
                            edirs.append('downstream')
                            traversed_edges.add((node, etype, neighbor))

        if 'upstream' == edirection or (node == root and direction == 'both'):
        # if 'upstream' == edirection or direction == 'both':
            for neighbor in G.predecessors(node):
                neigh_type = G.nodes[neighbor]['type']
                if is_ntype_not_valid(neigh_type):
                    continue
                edges = G[neighbor][node]
                for key in edges:
                    etype = edges[key]['type']
                    if is_etype_not_valid(etype):
                        continue
                    if not is_test_file(neighbor):
                        if (neighbor, etype, node) not in traversed_edges:
                            neigh_ids.append(neighbor)
                            etypes.append(etype)
                            edirs.append('upstream')
                            traversed_edges.add((neighbor, etype, node))

        for i, (neigh_id, etype, edir) in enumerate(zip(neigh_ids, etypes, edirs)):
            is_last_child = (i == len(neigh_ids) - 1)
            if edir == 'upstream':
                etype += '-by'
            traverse(neigh_id, new_prefix, is_last_child, level + 1, etype, edir)

    traverse(root, '', False, 0, None, None)
    return "\n".join(rtn_str)


def traverse_json_structure(G, root, direction='downstream', hops=2,
                            node_type_filter: Optional[List[str]] = None,
                            edge_type_filter: Optional[List[str]] = None):
    if hops == -1:
        hops = 20

    root_dict = dict()

    def traverse(node, node_dict, level, edirection=None):
        neigh_set, neigh_ids, etypes, edirs = [], [], [], []

        def is_ntype_not_validate(_ntype):
            return node_type_filter is not None and _ntype not in node_type_filter

        def is_etype_not_validate(_etype):
            return edge_type_filter is not None and _etype not in edge_type_filter

        if 'downstream' == edirection or (node == root and direction == 'both'):
            for neighbor in G.successors(node):
                neigh_type = G.nodes[neighbor]['type']
                if is_ntype_not_validate(neigh_type):
                    continue
                edges = G[node][neighbor]
                for key in edges:
                    etype = edges[key]['type']
                    if is_etype_not_validate(etype):
                        continue
                    if (not is_test_file(neighbor) and
                            (etype, neigh_type, neighbor) not in neigh_set):
                        neigh_ids.append(neighbor)
                        etypes.append(etype)
                        edirs.append('downstream')
                        neigh_set.append((etype, neigh_type, neighbor))

        if 'upstream' == edirection or (node == root and direction == 'both'):
            for neighbor in G.predecessors(node):
                neigh_type = G.nodes[neighbor]['type']
                if is_ntype_not_validate(neigh_type):
                    continue
                edges = G[neighbor][node]
                for key in edges:
                    etype = edges[key]['type']
                    if is_etype_not_validate(etype):
                        continue
                    if (not is_test_file(neighbor) and
                            (etype, neigh_type, neighbor) not in neigh_set):
                        neigh_ids.append(neighbor)
                        etypes.append(etype)
                        edirs.append('upstream')
                        neigh_set.append((etype, neigh_type, neighbor))

        for i, (neigh_id, etype, edir) in enumerate(zip(neigh_ids, etypes, edirs)):
            if edir == 'upstream':
                etype += '-by'

            if level + 1 >= hops:
                if etype not in node_dict:
                    node_dict[etype] = []
                node_dict[etype].append(neigh_id)
            else:
                if etype not in node_dict:
                    node_dict[etype] = {}
                node_dict[etype][neigh_id] = dict()
                traverse(neigh_id, node_dict[etype][neigh_id], level + 1, edir)

    traverse(root, root_dict, 0)
    return root_dict
