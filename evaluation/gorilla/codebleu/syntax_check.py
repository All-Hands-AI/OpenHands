# Copyright (c) Microsoft Corporation. 
# Licensed under the MIT license.

from codebleu.parser import DFG_python,DFG_java,DFG_ruby,DFG_go,DFG_php,DFG_javascript,DFG_csharp
from codebleu.parser import (remove_comments_and_docstrings,
                   tree_to_token_index,
                   index_to_code_token,
                   tree_to_variable_index)
from tree_sitter import Language, Parser

dfg_function={
    'python':DFG_python,
    'java':DFG_java,
    'ruby':DFG_ruby,
    'go':DFG_go,
    'php':DFG_php,
    'javascript':DFG_javascript,
    'c_sharp':DFG_csharp,
}

def calc_syntax_match(references, candidate, lang):
    return corpus_syntax_match([references], [candidate], lang)

def corpus_syntax_check(references, candidates, lang):   
    LANGUAGE = Language('codebleu/parser/my-languages.so', lang)
    parser = Parser()
    parser.set_language(LANGUAGE)
    match_count = 0
    total_count = 0
    scores = []

    for i in range(len(candidates)):
        references_sample = references[i]
        candidate = candidates[i] 
        for reference in references_sample:
            try:
                candidate=remove_comments_and_docstrings(candidate,'java')
            except:
                pass    
            try:
                reference=remove_comments_and_docstrings(reference,'java')
            except:
                pass  

            candidate_tree = parser.parse(bytes(candidate,'utf8')).root_node

            reference_tree = parser.parse(bytes(reference,'utf8')).root_node

            def get_all_sub_trees(root_node):
                node_stack = []
                sub_tree_sexp_list = []
                depth = 1
                node_stack.append([root_node, depth])
                while len(node_stack) != 0:
                    cur_node, cur_depth = node_stack.pop()
                    sub_tree_sexp_list.append([cur_node.sexp(), cur_depth])
                    for child_node in cur_node.children:
                        if len(child_node.children) != 0:
                            depth = cur_depth + 1
                            node_stack.append([child_node, depth])
                return sub_tree_sexp_list
            cand_sexps = [x[0] for x in get_all_sub_trees(candidate_tree)]
            # print(len(cand_sexps))
            # for i, sub_tree in enumerate(cand_sexps):
            #     print(i, sub_tree)
            # exit()
            ref_sexps = get_all_sub_trees(reference_tree)

            score = 0 - str(candidate_tree.sexp()).count("ERROR")
            # for sub_tree, depth in ref_sexps:
            #     if sub_tree in cand_sexps:
            #          match_count += 1
            # total_count += len(ref_sexps)          
       
    # score = match_count / total_count
    return score
