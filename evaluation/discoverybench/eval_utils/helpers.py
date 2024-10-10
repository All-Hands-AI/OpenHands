import atexit
import json
import logging
import os
from itertools import chain, combinations

import numpy as np
from sympy import preorder_traversal
from sympy.core.numbers import Float as SympyFloat


def setup_logger(run_id, log_dir='./logs'):
    os.makedirs(log_dir, exist_ok=True)
    log_fname = f'{log_dir}/{run_id}.log'
    logger = logging.getLogger()  # get root logger
    file_handler = logging.FileHandler(log_fname, mode='a', delay=False)
    file_handler.setFormatter(
        logging.Formatter(
            fmt='%(asctime)s - %(levelname)s - %(name)s -   %(message)s',
            datefmt='%m/%d/%Y %H:%M:%S',
        )
    )
    file_handler.setLevel(logging.INFO)
    logger.addHandler(
        file_handler
    )  # all other loggers propagate to root; write to one log file from root
    print(f'Log path: {log_fname}')
    atexit.register(lambda: print(f'Log path: {log_fname}'))


def deep_get(obj, *keys, default):
    default = default if default is not None else {}
    rtn = obj
    if not isinstance(rtn, dict):  # COMMENT: changed from type(rtn) is not dict
        return default
    for k in keys:
        rtn = rtn.get(k, default)
        if not isinstance(rtn, dict):  # COMMENT: changed from type(rtn) is not dict
            return rtn
    return rtn


def printj(obj, indent=2, logger=None):
    fn = print if logger is None else logger
    fn(json.dumps(obj, indent=indent))


def extract_bracket_substrings(input_str):
    substrings = []
    stack = []

    for i, char in enumerate(input_str):
        if char == '(':
            stack.append(i)
        elif char == ')':
            if stack:
                start_index = stack.pop()
                substrings.append(input_str[start_index : i + 1])

    return substrings


def extract_variable(input_str, var_prefix='x'):
    split = input_str.split()
    rtn = []
    for s in split:
        _s = s.strip().strip('(').strip(')')
        if _s.startswith(var_prefix):
            rtn.append(_s)
    return rtn


def round_sympy_expr(expr, precision=2):
    new = expr
    for a in preorder_traversal(expr):
        if isinstance(a, SympyFloat):
            new = new.subs(a, round(a, precision))
    return new


def powerset(iterable):
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))


def get_const_from_sympy(sym):
    return [arg for arg in sym.args if arg not in sym.free_symbols][0]


def safe_exp(expr, exp, default=0.0):
    if exp < 0:
        return np.where(expr != 0, np.power(expr, exp), default)
    return np.power(expr, exp)
