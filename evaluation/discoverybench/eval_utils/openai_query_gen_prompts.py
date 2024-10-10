PROMPT_QUERY = """\
Given a dataset and a known true hypothesis that can be proven from it, construct a hard question \
that tests someone's ability to find the true hypothesis using data analysis. \
Make sure to not reveal the true hypothesis in the question. \
Do not provide too many details. You may start your question in the following manner: \
"What is the relationship between...", "Is there a relationship...", "How does...", "What might...".

Dataset and hypothesis:
```json
{
    "domain": "%s",
    "description": "%s",
    "columns": %s,
    "true_hypothesis": "%s"
}
```

Give your answer as a new JSON with the following format:
```json
{
    "question": "..."
}
```"""

PROMPT_QUERY_VARIABLE = """\
Given a dataset and a known true hypothesis that can be proven using that dataset, we want to construct questions to \
test whether someone can find this true hypothesis given only the dataset. Generate a set of questions revealing \
different amounts of information making sure to not reveal_in_question the true hypothesis. For each question, we will \
provide an instruction of what information to hold back. You may start your question text in the following manner: \
"What is the relationship between...", "Is there a relationship...", "How does...", "What might...". \
Make sure that the question is not leading (i.e. it does not indicate what the true answer is). \

Dataset and hypothesis:
```json
{
    "domain": "%s",
    "description": "%s",
    "columns": %s,
    "hypothesis": {
        "text": "%s",
        "target_col": "%s",
        "target_col_derivation": "%s"
    },
    "questions": [
        {
            "reveal_in_question": [],
            "hide_in_question": ["target concept", "concepts that affect the target concept", "specific sub-group(s), if any, the relationship is applicable to"],
            "text": "..."
        },
        {
            "reveal_in_question": ["target concept"],
            "hide_in_question": ["concepts that affect the target concept", "specific sub-group(s), if any, the relationship is applicable to"],
            "text": "..."
        },
        {
            "reveal_in_question": ["target concept", "concepts that affect the target concept"],
            "hide_in_question": ["specific sub-group(s), if any, the relationship is applicable to"],
            "text": "..."
        },
        {
            "reveal_in_question": ["target concept", "concepts that affect the target concept", "specific sub-group(s), if any, the relationship is applicable to"],
            "hide_in_question": [],
            "text": "..."
        }
    ]
}```

Give your answer as a new JSON with the following format:
```json
{
    "questions": [
        {"text": "..."},
        {"text": "..."},
        ...
    ]
}```"""


PROMPT_QUERY_RELATIONSHIP = """\
Given a dataset and a known true hypothesis that can be proven using that dataset, we want to construct questions to \
test whether someone can find this true hypothesis given only the dataset. Generate a set of questions revealing \
different amounts of information making sure to not reveal the true hypothesis. For each question, we will provide an \
instruction of what information to hold back. You may start your question text in the following manner: "What is the \
relationship between...", "Is there a relationship...", "How does...", "What might...". Make sure that the question is \
not leading (i.e. it does not indicate what the true answer is).

Dataset and hypothesis:
```json
{
    "domain": "%s",
    "description": "%s",
    "columns": %s,
    "hypothesis": {
        "text": "%s",
        "target_col": "%s",
        "target_col_derivation": "%s"
    },
    "questions": [
        {
            "reveal_in_question": [],
            "hide_in_question": ["any information about the relationship between the interacting concepts"],
            "text": "..."
        },
        {
            "reveal_in_question": ["nature of the relationship (e.g., positive/negative, increase/decrease, etc.)", "numerics of the relationship (e.g. quadratic relationship, change by x amount, etc.)"],
            "hide_in_question": [],
            "text": "..."
        }
    ]
}```

Give your answer as a new JSON with the following format:
```json
{
    "questions": [
        {"text": "..."},
        {"text": "..."},
        ...
    ]
}
```"""
