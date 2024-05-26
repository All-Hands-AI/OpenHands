# Copyright (c) Microsoft Corporation. 
# Licensed under the MIT license.

from codebleu.parser import DFG_python
from codebleu.parser import (remove_comments_and_docstrings,
                   tree_to_token_index,
                   index_to_code_token,
                   tree_to_variable_index)
from tree_sitter import Language, Parser
import pdb

dfg_function={
    'python':DFG_python
}

def calc_dataflow_match(references, candidate, lang):
    """
    Calculate the dataflow match score for a candidate code against references.
    
    Args:
        references (list): A list of reference code samples.
        candidate (str): The candidate code to be evaluated.
        lang (str): The programming language of the code samples.

    Returns:
        float: The dataflow match score.
    """
    return corpus_dataflow_match([references], [candidate], lang)

def corpus_dataflow_match(references, candidates, lang):  
    """
    Calculate the corpus-level dataflow match score for candidates against references.
    
    Args:
        references (list): A list of lists of reference code samples.
        candidates (list): A list of candidate code samples.
        lang (str): The programming language of the code samples.

    Returns:
        float: The corpus-level dataflow match score.
    """
    LANGUAGE = Language('codebleu/parser/my-languages.so', lang)
    parser = Parser()
    parser.set_language(LANGUAGE)
    parser = [parser,dfg_function[lang]]
    match_count = 0
    total_count = 0

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

            cand_dfg = get_data_flow(candidate, parser)
            ref_dfg = get_data_flow(reference, parser)
            
            normalized_cand_dfg = normalize_dataflow(cand_dfg)
            normalized_ref_dfg = normalize_dataflow(ref_dfg)

            if len(normalized_ref_dfg) > 0:
                total_count += len(normalized_ref_dfg)
                for dataflow in normalized_ref_dfg:
                    if dataflow in normalized_cand_dfg:
                            match_count += 1
                            normalized_cand_dfg.remove(dataflow)    

    if total_count == 0:
        return 0

    score = match_count / total_count
    return score

def get_data_flow(code, parser):
    """
    Extract the dataflow graph (DFG) from the given code using the parser.

    Args:
        code (str): The code from which to extract the DFG.
        parser (list): A list containing the language parser and DFG function.

    Returns:
        list: The extracted dataflow graph.
    """
    try:
        tree = parser[0].parse(bytes(code,'utf8'))    
        root_node = tree.root_node  
        tokens_index=tree_to_token_index(root_node)     
        code=code.split('\n')
        code_tokens=[index_to_code_token(x,code) for x in tokens_index]  
        index_to_code={}
        for idx,(index,code) in enumerate(zip(tokens_index,code_tokens)):
            index_to_code[index]=(idx,code)  
        try:
            DFG,_=parser[1](root_node,index_to_code,{}) 
        except:
            DFG=[]
        DFG=sorted(DFG,key=lambda x:x[1])
        indexs=set()
        for d in DFG:
            if len(d[-1])!=0:
                indexs.add(d[1])
            for x in d[-1]:
                indexs.add(x)
        new_DFG=[]
        for d in DFG:
            if d[1] in indexs:
                new_DFG.append(d)
        codes=code_tokens
        dfg=new_DFG
    except:
        codes=code.split()
        dfg=[]
    #merge nodes
    dic={}
    for d in dfg:
        if d[1] not in dic:
            dic[d[1]]=d
        else:
            dic[d[1]]=(d[0],d[1],d[2],list(set(dic[d[1]][3]+d[3])),list(set(dic[d[1]][4]+d[4])))
    DFG=[]
    for d in dic:
        DFG.append(dic[d])
    dfg=DFG
    return dfg

def normalize_dataflow_item(dataflow_item):
    """
    Normalize a single dataflow item.

    Args:
        dataflow_item (tuple): A dataflow item tuple.

    Returns:
        tuple: The normalized dataflow item.
    """
    var_name = dataflow_item[0]
    var_pos = dataflow_item[1]
    relationship = dataflow_item[2]
    par_vars_name_list = dataflow_item[3]
    par_vars_pos_list = dataflow_item[4]

    var_names = list(set(par_vars_name_list+[var_name]))
    norm_names = {}
    for i in range(len(var_names)):
        norm_names[var_names[i]] = 'var_'+str(i)

    norm_var_name = norm_names[var_name]
    relationship = dataflow_item[2]
    norm_par_vars_name_list = [norm_names[x] for x in par_vars_name_list]

    return (norm_var_name, relationship, norm_par_vars_name_list)

def normalize_dataflow(dataflow):
    """
    Normalize a list of dataflow items.

    Args:
        dataflow (list): A list of dataflow items.

    Returns:
        list: The normalized list of dataflow items.
    """
    var_dict = {}
    i = 0
    normalized_dataflow = []
    for item in dataflow:
        var_name = item[0]
        relationship = item[2]
        par_vars_name_list = item[3]
        for name in par_vars_name_list:
            if name not in var_dict:
                var_dict[name] = 'var_'+str(i)
                i += 1
        if var_name not in var_dict:
            var_dict[var_name] = 'var_'+str(i)
            i+= 1
        normalized_dataflow.append((var_dict[var_name], relationship, [var_dict[x] for x in par_vars_name_list]))
    return normalized_dataflow


