"""
Calculate the cdc score for line and block
"""

import json
import math
import os
import re

# warnings.filterwarnings("ignore", category=SyntaxWarning)


def is_code_valid(code):
    try:
        compile(code, '<string>', 'exec')
        return True
    except Exception:
        return False


def is_correct_parameter_count(function_name, correct_code, test_code):
    """
    判断参数数量是否一致
    :param function_name:
    :param correct_code:
    :param test_code:
    :return:
    """
    # 获取正确代码中的参数数量
    # return True
    pattern = rf'{function_name}\((.*?)\)'
    correct_match = re.search(pattern, correct_code)

    if correct_match:
        correct_params = correct_match.group(1).strip()
        correct_param_list = [p.strip() for p in correct_params.split(',') if p.strip()]
        expected_count = len(correct_param_list)
    else:
        expected_count = 0  # 如果没有参数，期望数量为0

    # 在需要判断的代码中查找函数调用
    test_match = re.search(pattern, test_code)

    if test_match:
        test_params = test_match.group(1).strip()
        test_param_list = [p.strip() for p in test_params.split(',') if p.strip()]
        return len(test_param_list) == expected_count  # 检查参数数量
    else:
        # 如果没有括号，检查函数名是否在字符串中
        return expected_count == 0 and function_name in test_code


def check_keyword_parameters(function_name, correct_code, test_code):
    """
    判断关键词参数赋值是否正确使用
    :param function_name:
    :param correct_code:
    :param test_code:
    :return:
    """
    # 正则表达式匹配正确代码中的函数调用
    # return True
    pattern = rf'{function_name}\((.*?)\)'
    correct_match = re.search(pattern, correct_code)

    if correct_match:
        correct_params = correct_match.group(1).strip()
        correct_param_list = [p.strip() for p in correct_params.split(',') if p.strip()]

        # 检查待检测代码中的函数调用
        test_match = re.search(pattern, test_code)

        if test_match:
            test_params = test_match.group(1).strip()
            test_param_list = [p.strip() for p in test_params.split(',') if p.strip()]

            # 确保待检测的每个参数都以关键字参数形式赋值
            for correct_param in correct_param_list:
                if '=' in correct_param:  # 仅当正确代码中有关键词参数
                    param_name = correct_param.split('=')[0].strip()
                    if not any(
                        param_name in test_param and '=' in test_param
                        for test_param in test_param_list
                    ):
                        return False  # 如果对应参数不是关键词参数，则返回False

            return True  # 所有关键字参数匹配

    return False  # 如果没有匹配，返回False


def with_correct(answer_code: str, model_output: str) -> bool:
    """
    当answer是with结构时，判断模型生成的是不是with结构
    :param answer_code:
    :param model_output:
    :return:
    """
    # return True
    if not answer_code.startswith('with') and not model_output.startswith('with'):
        return True
    elif answer_code.startswith('with') and model_output.startswith('with'):
        return True
    else:
        return False


def compute_line_score_k(
    answer: str, model_output: list, k: int, model_filled_code, core_line
):
    c = 0
    n = len(model_output)
    for index, code in enumerate(model_output):
        if (
            re.search(rf'\b{re.escape(answer)}\b', code)
            and is_code_valid(model_filled_code[index])
            and is_correct_parameter_count(answer, core_line, code)
            and with_correct(core_line, code)
            and check_keyword_parameters(answer, core_line, code)
        ):  # line
            c += 1
    if n - c < k:
        return 1.0

    score = 1 - (math.comb(n - c, k)) / (math.comb(n, k))

    return score


def compute_block_score_k(
    answer: str,
    model_output: list,
    k: int,
    model_filled_code,
    core_line_in_core_block,
    core_line_in_output_clear,
):
    c = 0
    n = len(model_output)
    for index, code in enumerate(model_output):
        if (
            re.search(rf'\b{re.escape(answer)}\b', code)
            and is_code_valid(model_filled_code[index])
            and is_correct_parameter_count(
                answer, core_line_in_core_block, core_line_in_output_clear[index]
            )
            and with_correct(core_line_in_core_block, core_line_in_output_clear[index])
            and check_keyword_parameters(
                answer, core_line_in_core_block, core_line_in_output_clear[index]
            )
        ):  # block
            c += 1
    if n - c < k:
        return 1.0

    score = 1 - (math.comb(n - c, k)) / (math.comb(n, k))

    return score


def compute_score_k(answer: str, model_output: list, k: int):
    c = 0
    n = len(model_output)
    for index, code in enumerate(model_output):
        if re.search(rf'\b{re.escape(answer)}\b', code) and is_code_valid(
            code
        ):  # block
            # if re.search(rf'\b{re.escape(answer)}\b', code):#line
            c += 1
    if n - c < k:
        return 1.0

    score = 1 - (math.comb(n - c, k)) / (math.comb(n, k))

    return score


k = 3  # cdc@k
task = 'block'  # line or block
json_name = f'Versicode_{task}_completion.json'

folder_path = f'../data/result_data/{task}_completion'
model_list = os.listdir(folder_path)

for model in model_list:
    model_json_path = os.path.join(folder_path, model, json_name)
    with open(model_json_path, 'r', encoding='utf-8') as fr:
        lodict = json.load(fr)
    data_list = lodict

    if task == 'line':
        score_list = []
        for data in data_list:
            answer = data['core_token']
            model_output = eval(data['model_output_clear'])
            model_filled_code = [
                data['masked_code'].replace('<mask>', i) for i in model_output
            ]
            core_line = data['core_line']
            score_list.append(
                compute_line_score_k(
                    answer, model_output, k, model_filled_code, core_line
                )
            )
    else:
        score_list = []
        for data in data_list:
            answer = data['core_token']
            model_output = eval(data['model_output_clear'])
            model_filled_code = eval(data['model_output_clear'])
            core_line = data['core_line']
            core_line_in_output_clear = data['core_line_in_output_clear']
            score_list.append(
                compute_block_score_k(
                    answer,
                    model_output,
                    k,
                    model_filled_code,
                    core_line,
                    core_line_in_output_clear,
                )
            )

    final_score = sum(score_list) / len(score_list)
    print(f'{model}, {task} completion task, cdc@{k} score: {final_score}')
