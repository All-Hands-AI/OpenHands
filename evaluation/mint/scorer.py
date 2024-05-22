def question_scorer(model_answer: str, ground_truth: str) -> bool:
    try:
        if float(model_answer) == float(ground_truth):
            return True
    except ValueError:
        pass

    if model_answer == ground_truth:
        return True
