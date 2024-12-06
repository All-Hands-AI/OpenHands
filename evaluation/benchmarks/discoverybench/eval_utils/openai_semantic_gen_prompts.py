common_hypothesis_features = [
    '1-2 sentences',
    'surprising finding',
    'includes numeric concepts',
    'includes categorical concepts',
    'includes binary concepts',
]
hypothesis_features = [
    ['requires within-cluster analysis'],
    ['requires across-cluster analysis'],
    ['corresponds to a polynomial relationship of some columns'],
    ['corresponds to a ratio between some columns'],
    ['requires temporal analysis'],
    ['relationship is based on descriptive statistics of some columns'],
    ['requires concepts based on percentage or percentiles'],
    ['relationship is only applicable to one cluster in the data and not the others'],
]

column_features = [
    [
        'must have one target column',
        'must have quantifiable columns',
        'must have a few categorical columns',
        'make sure the categorical column values do not contain special characters',
        'include a few distractor columns',
    ]
]

common_pandas_features = [
    'must be executable using python `eval` to create the target column in variable `df` (pandas dataframe)',
    "for e.g., df['A']**2 + 3*df['B'] + 9, np.where(df['A'] > 3, 'Yes', 'No'), etc.",
    'variables in pandas_expression must be from the existing columns listed above',
    'variables in pandas_expression must NOT contain the target column itself',
]
pandas_features = [
    ['expression is a quadratic polynomial'],
    ['expression is a cubic polynomial'],
    ['expression is a ratio of existing columns'],
    ['expression is derived through logical combination of existing columns'],
    # workflow
]
pandas_features = [common_pandas_features + p for p in pandas_features]

common_derived_features = [
    '1-2 sentences',
    'includes numeric concepts',
    'includes categorical concepts',
    'includes binary concepts',
]
derived_features = [common_derived_features + h for h in hypothesis_features]
hypothesis_features = [common_hypothesis_features + h for h in hypothesis_features]

PROMPT_HYP = """\
Given a dataset topic and description, generate an interesting hypothesis based on \
the provided instructions. Be creative and come up with an unusual finding.

```json
{
    "topic": "%s",
    "description": "%s",
    "hypothesis_features": %s,
    "hypothesis": "..."
}```

Give your answer as a new JSON with the following format:
```json
{
    "hypothesis": "..."
}
```"""

PROMPT_COL = """\
Given a dataset topic, its description, and a true hypothesis that can be determined from it, \
generate a list of valid columns based on the provided instructions.

```json
{
    "topic": "%s",
    "description": "%s",
    "hypothesis": "%s",
    "column_instructions": %s,
    "columns": [
        {
            "col_name": "...",  # should be an "_"-separated string
            "description": "...",
            "data_type": "...",  # should be executable using python's `eval` function. E.g., str, float, int, bool
            "data_range": {...},  # should be either {"min": ..., "max": ...} or {"values": [...]}
            "is_distractor": true/false,  # boolean indicating whether this is a distractor that could cause confusion during data analysis
            "is_target": true/false  # boolean indicating whether this is the target variable for the hypothesis; at least one column should be the target
        },
        ...
    ],
    "pandas_instructions": %s,
    "pandas_equation_for_hypothesis": {
        "target_col": "...",
        "target_col_type": "...",
        "target_col_range": {...},
        "independent_cols_in_pandas_expression": [],  # list of column names that will be used to derive the target column
        "pandas_expression": "..."  # expression to derive df[target_col] using df[ind_col1], df[ind_col2], etc.
    }
}```

Give your answer as a new JSON with the "columns" and "pandas_equation_for_hypothesis" keys filled using the following format:
```json
{
    "columns": [...],
    "pandas_equation_for_hypothesis": {...}
}
```"""

PROMPT_DER = """\
Given a dataset topic, description, a true hypothesis that can be determined from the data, \
and a target column from the dataset, generate a hypothesis for the target column using new independent columns not present in the existing columns.

```json
{
    "topic": "%s",
    "description": "%s",
    "hypothesis": "%s",
    "existing_columns": %s,
    "target_column": "%s",
    "new_to_target_instructions": %s,
    "new_to_target_hypothesis": "...",  # describe a relationship between new columns that explains the target column
    "new_columns_for_target": [  # do not repeat any of the existing columns in the dataset
        {
            "col_name": "...",  # should be an "_"-separated string
            "description": "...",
            "data_type": "...",  # should be executable using python's `eval` function. E.g., str, float, int, bool
            "data_range": {...},  # should be either {"min": ..., "max": ...} or {"values": [...]}
        },
        ...
    ],
    "pandas_instructions": %s,
    "pandas_equation_for_new_to_target_hypothesis": {
        "target_col": "...",
        "target_col_type": "...",
        "target_col_range": {...},
        "independent_cols_in_pandas_expression": [],  # list of column names from new_columns_for_target that will be used to derive target_col
        "pandas_expression": "..."  # expression to derive df[target_col] using df[ind_col1], df[ind_col2], etc.
    }
}```

Give your answer as a new JSON with the "new_to_target_hypothesis", "new_columns_for_target", and \
"pandas_equation_for_new_to_target_hypothesis" keys filled using the following format:
```json
{
    "new_to_target_hypothesis": "...",
    "new_columns_for_target": [...],
    "pandas_equation_for_new_to_target_hypothesis": {...}
}
```"""
