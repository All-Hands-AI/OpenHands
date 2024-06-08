TASK_INFO_MAP = {
    # === Reasoning ===
    'gsm8k': {'class': 'ReasoningTask', 'type': 'reasoning'},
    'math': {'class': 'ReasoningTask', 'type': 'reasoning'},
    'mmlu': {'class': 'MultipleChoiceTask', 'type': 'reasoning'},
    'theoremqa': {'class': 'TheoremqaTask', 'type': 'reasoning'},
    'mbpp': {'class': 'MBPPTask', 'type': 'code_generation'},
    'humaneval': {'class': 'HumanEvalTask', 'type': 'code_generation'},
}
