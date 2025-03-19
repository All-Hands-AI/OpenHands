from typing import List, Optional

from openhands.runtime.plugins.agent_skills.repo_ops.compress_file import get_skeleton
from openhands.runtime.plugins.agent_skills.repo_ops.repo_index.dependency_graph.build_graph import (
    NODE_TYPE_CLASS,
    NODE_TYPE_DIRECTORY,
    NODE_TYPE_FILE,
    NODE_TYPE_FUNCTION,
)


class QueryInfo:
    query_type: str = 'keyword'
    term: Optional[str] = None
    line_nums: Optional[List] = None
    file_path_or_pattern: Optional[str] = None

    def __init__(
        self,
        query_type: str = 'keyword',
        term: Optional[str] = None,
        line_nums: Optional[List] = None,
        file_path_or_pattern: Optional[str] = None,
    ):
        self.query_type = query_type
        if term is not None:
            self.term = term
        if line_nums is not None:
            self.line_nums = line_nums
        if file_path_or_pattern is not None:
            self.file_path_or_pattern = file_path_or_pattern

    def __str__(self):
        parts = []
        if self.term is not None:
            parts.append(f'term: {self.term}')
        if self.line_nums is not None:
            parts.append(f'line_nums: {self.line_nums}')
        if self.file_path_or_pattern is not None:
            parts.append(f'file_path_or_pattern: {self.file_path_or_pattern}')
        return ', '.join(parts)

    def __repr__(self):
        return self.__str__()


class QueryResult:
    file_path: Optional[str] = None
    format_mode: Optional[str] = 'complete'
    nid: Optional[str] = None
    ntype: Optional[str] = None
    # code_snippet: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    query_info_list: Optional[List[QueryInfo]] = None
    desc: Optional[str] = None
    message: Optional[str] = None
    warning: Optional[str] = None
    retrieve_src: Optional[str] = None

    def __init__(
        self,
        query_info: QueryInfo,
        format_mode: str,
        nid: Optional[str] = None,
        ntype: Optional[str] = None,
        file_path: Optional[str] = None,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        desc: Optional[str] = None,
        message: Optional[str] = None,
        warning: Optional[str] = None,
        retrieve_src: Optional[str] = None,
    ):
        self.format_mode = format_mode
        self.query_info_list = []
        self.insert_query_info(query_info)

        # 根据传入参数进行不同的初始化逻辑
        if nid is not None:
            self.nid = nid

        if ntype is not None:
            self.ntype = ntype
            if ntype in [NODE_TYPE_FILE, NODE_TYPE_CLASS, NODE_TYPE_FUNCTION]:
                self.file_path = nid.split(':')[0]

        if file_path is not None:
            self.file_path = file_path
        if start_line is not None and end_line is not None:
            self.start_line = start_line
            self.end_line = end_line

        if retrieve_src is not None:
            self.retrieve_src = retrieve_src

        if desc is not None:
            self.desc = desc
        if message is not None:
            self.message = message
        if warning is not None:
            self.warning = warning

    def insert_query_info(self, query_info: QueryInfo):
        self.query_info_list.append(query_info)

    def format_output(self, searcher):
        cur_result = ''

        if self.format_mode == 'complete':
            node_data = searcher.get_node_data([self.nid], return_code_content=True)[0]
            ntype = node_data['type']
            cur_result += f'Found {ntype} `{self.nid}`.\n'
            cur_result += 'Source: ' + self.retrieve_src + '\n'
            if 'code_content' in node_data:
                cur_result += node_data['code_content'] + '\n'

        elif self.format_mode == 'preview':
            node_data = searcher.get_node_data([self.nid], return_code_content=True)[0]
            ntype = node_data['type']
            cur_result += f'Found {ntype} `{self.nid}`.\n'
            cur_result += 'Source: ' + self.retrieve_src + '\n'
            if ntype == NODE_TYPE_FUNCTION:
                cur_result += node_data['code_content'] + '\n'

            elif ntype in [NODE_TYPE_CLASS, NODE_TYPE_FILE]:
                content_size = node_data['end_line'] - node_data['start_line']
                if content_size <= 100:
                    cur_result += node_data['code_content'] + '\n'
                else:
                    cur_result += f'Just show the structure of this {ntype} due to response length limitations:\n'
                    code_content = searcher.G.nodes[self.nid].get('code', '')
                    # if ntype == NODE_TYPE_CLASS:
                    #     #  show structure
                    #     structure_lines = get_skeleton(code_content).splitlines()
                    #     # structure_lines = []
                    #     # structure_lines_wo_init = get_skeleton(code_content).splitlines()
                    #     # # TODO: no init function in the graph
                    #     # init_nid = f'{self.nid}.__init__'
                    #     # for line in structure_lines_wo_init:
                    #     #     if 'def __init__' in line and searcher.has_node(init_nid):
                    #     #         init_ndata = searcher.G.nodes[init_nid]
                    #     #         structure_lines.extend(init_ndata.get('code', "").splitlines())
                    #     #     else:
                    #     #         structure_lines.append(line)
                    #     structure = '\n'.join(structure_lines)
                    #     cur_result += '```\n' + structure + '\n```\n'
                    # else:
                    structure = get_skeleton(code_content)
                    cur_result += '```\n' + structure + '\n```\n'
                    cur_result += f'Hint: Search `{self.nid}` to get the full content if needed.\n'

            elif ntype == NODE_TYPE_DIRECTORY:
                pass

        elif self.format_mode == 'code_snippet':
            if self.desc:
                cur_result += self.desc + '\n'
            else:
                cur_result += f'Found code snippet in file `{self.file_path}`.\n'
            cur_result += 'Source: ' + self.retrieve_src + '\n'
            # content = get_file_content_(qr.file_path, return_str=True)
            # result_content = line_wrap_content(content, [(, )])
            node_data = searcher.get_node_data(
                [self.file_path], return_code_content=True
            )[0]
            content = node_data['code_content'].split('\n')[1:-1]

            code_snippet = content[
                (self.start_line - 1) : self.end_line
            ]  # TODO: try-catch

            code_snippet = '```\n' + '\n'.join(code_snippet) + '\n```'
            cur_result += code_snippet + '\n'
            if self.message and self.message.strip():
                cur_result += self.message

        elif self.format_mode == 'fold':
            node_data = searcher.get_node_data([self.nid], return_code_content=False)[0]
            self.ntype = node_data['type']
            cur_result += f'Found {self.ntype} `{self.nid}`.\n'

        return cur_result

    def __str__(self):
        return (
            f'QueryResult(\n'
            f'  query_info_list: {str(self.query_info_list)},\n'
            f'  format_mode: {self.format_mode},\n'
            f'  nid: {self.nid},\n'
            f'  file_path: {self.file_path},\n'
            f'  start_line: {self.start_line},\n'
            f'  end_line: {self.end_line}\n'
            f')'
        )
