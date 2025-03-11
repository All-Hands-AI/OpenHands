import json


def OPENAI_TOPIC_GEN_MESSAGES(n=10):
    return [
        {
            'role': 'system',
            'content': 'You are a helpful assistant who is not talkative. You only respond with the exact answer to a query without additional conversation.',
        },
        {
            'role': 'user',
            'content': f'Given `n`, come up with a list of `n` distinct topics and their descriptions. The topics can be absolutely anything. Be as creative as possible. Return your answer as a JSON object. \n\nFor example, for `n`=3, a valid answer might be:\n```json\n{{"topics": [\n  {{"id": 1, "topic": "cooking", "description": "Related to recipes, ingredients, chefs, etc."}},\n  {{"id": 2, "topic": "sports", "description": "Related to players, stadiums, trophies, etc."}},\n  {{"id": 3, "topic": "antiquing", "description": "Related to unique items, history, etc."}}\n]}}```\n\nNow, give me a list for `n`={n}. Remember, pick diverse topics from everything possible. No consecutive topics should be broadly similar. Directly respond with the answer JSON object.',
        },
    ]


OPENAI_GEN_HYP = {
    'temperature': 1.0,
    'max_tokens': 4096,
    'top_p': 1.0,
    'frequency_penalty': 0,
    'presence_penalty': 0,
}


def OPENAI_SEMANTICS_GEN_MESSAGES(dependent, relationship, domain, domain_desc):
    return [
        {
            'role': 'system',
            'content': 'You are a helpful assistant who is not talkative. You only respond with the exact answer to a query without additional conversation.',
        },
        {
            'role': 'user',
            'content': f'Given the true relationship in a dataset and a given domain, your task is to come up with an interpretation of some real-world concepts that the relationship could be modeling from the provided domain. It\'s okay to be wrong, but suggest something reasonable. Try as much as possible to make sure that the TARGET is actually derivable from the other variables. Give your answer as a JSON object. Here\'s an example:\n\nRelationship for x2 = "(96.4 * x1 ** 3) + (88.72 * x5 ** 2) + (81.96 * x6 ** -2) + (28.13 * x3)  + (97.0) + (0 * x4)"\nDomain="Sales"\nDomain description="Related to product distribution, revenues, marketing, etc."\n\nBased on this, the following real-world concepts might be applicable:\n```json\n{{\n  "dependent": "x2",\n  "relationship": "(96.4 * x1 ** 3) + (88.72 * x5 ** 2) + (81.96 * x6 ** -2) + (28.13 * x3)  + (97.0) + (0 * x4)",\n  "domain": "Sales",\n  "trends": {{\n    "x1": "Positive, cubic factor",\n    "x2": "TARGET",\n    "x3": "Positive, linear factor",\n    "x4": "No relation",\n    "x5": "Positive quadratic factor",\n    "x6": "Positive, inverse quadratic factor"\n  }},\n  "interpretation": {{\n    "x2": {{"description": "Volume of product sales by area", "name": "sales_area", "is_target": true}},\n    "x1": {{"description": "Population by area", "name": "pop_area"}},\n    "x3": {{"description": "Advertising spending", "name": "ad_spend"}},\n    "x4": {{"description": "Gender ratio of marketing team", "name": "gdr_ratio_mkt_team"}},\n    "x5": {{"description": "Intensity of marketing campaign", "name": "mkt_intensity"}}\n  }},\n    "x6": {{"description": "Distance to distribution center", "name": "dist_to_distr_ctr"}}\n}}```\n\nHere\'s a new test question:\nRelationship for {dependent} = "{relationship}"\nDomain = "{domain}"\nDomain description="{domain_desc}"\n\nRespond only with the answer JSON. Make sure that you do not forget to include the TARGET variable in the interpretation object.',
        },
    ]


def OPENAI_SEMANTICS_GEN_W_MAP_MESSAGES(
    dependent, relationship, domain, domain_desc, mapping
):
    return [
        {
            'role': 'system',
            'content': 'You are a helpful assistant who is not talkative. You only respond with the exact answer to a query without additional conversation.',
        },
        {
            'role': 'user',
            'content': f'Given a partial mapping from variables to real-world concepts and a true relationship in a dataset, your task is to come up with an interpretation of real-world concepts for the variables without any assigned mapping (those starting with x). Suggest something reasonable. The dependent variable must be derivable only from the other variables in the dependent relationship. Give your answer as a JSON object. Here\'s an example:\n\nExample partial mapping and relationship:\n```json\n{{\n  "domain": "Sales",\n  "domain_description": "Related to product distribution, revenues, marketing, etc.",\n  "variable_mapping": {{\n    "x1": {{"description": "Population by area", "name": "pop_area"}},\n    "x2": {{"description": "Volume of product sales by area", "name": "sales_area"}},\n    "x4": {{"description": "Gender ratio of marketing team", "name": "gdr_ratio_mkt_team"}},\n    "x6": {{"description": "Distance to distribution center", "name": "dist_to_distr_ctr"}}\n  }},\n  "dependent_variable": "sales_area",\n  "dependent_relationship": "(96.4 * pop_area ** 3) + (88.72 * x5 ** 2) + (81.96 * dist_to_distr_ctr ** -2) + (28.13 * x3)  + (97.0)"\n}}```\nBased on this, an example answer would be:\n```json\n{{\n  "dependent_variable": "sales_area",\n  "missing_mapping": ["x3", "x5"],\n  "trends": {{\n    "x3": "Positive, linear factor",\n    "x5": "Positive quadratic factor"\n  }},\n  "interpretation": {{\n    "x3": {{"description": "Advertising spending", "name": "ad_spend"}},\n    "x5": {{"description": "Intensity of marketing campaign", "name": "mkt_intensity"}}\n  }}\n}}```\n\nHere\'s a new test question:\n```json\n{{\n  "domain": "{domain}",\n  "domain_description": "{domain_desc}",\n  "variable_mapping": {json.dumps(mapping, indent=2)},\n  "dependent_variable": "{dependent}",\n  "dependent_relationship": "{relationship}"\n}}```\nRespond only with the answer JSON.',
        },
    ]


def OPENAI_SEMANTICS_GEN_SUMMARY_MESSAGES(dataset):
    return [
        {
            'role': 'system',
            'content': 'You are a helpful assistant who is not talkative. You only respond with the exact answer to a query without additional conversation.',
        },
        {
            'role': 'user',
            'content': f'Given the following descriptions of the columns of a dataset, your task is to come up with a natural language overview of the dataset, which should include (1) what the dataset is about, (2) how the data was collected, (3) when the data was collected, and (3) for what purpose the data was collected. Be specific and creative.\n\nExample dataset:\n```json\n{{  \n  "dataset": {{                                                                                                                                                                                       \n    "x6": {{"description": "Ancient artifact significance score", "name": "artifact_significance_score", "is_target": true}},\n    "x1": {{"description": "Distance to ancient city center", "name": "dist_to_ancient_city_ctr"}},\n    "x2": {{"description": "Quantity of discovered relics", "name": "relic_discovery_qty"}},\n    "x3": {{"description": "Years since last archaeological expedition", "name": "years_since_exp"}},\n    "x4": {{"description": "Number of artifacts in excavation site", "name": "artifact_qty"}},\n    "x5": {{"description": "Soil fertility coefficient", "name": "soil_fertility_coef"}},\n    "x7": {{"description": "Distance to ancient burial grounds", "name": "dist_to_burial_grounds"}},\n    "x8": {{"description": "Population estimate of ancient civilization", "name": "ancient_civilization_pop_estimate"}},\n    "x9": {{"description": "Temperature variation in excavation region", "name": "temp_variation"}}\n  }}\n}}```\nExample description:\nThis dataset is about archaeological explorations and findings linked to ancient civilizations. The data was collected in the form of field metrics during various archaeological expeditions during the late mid-20th century. The purpose of the data collection is to evaluate the significance of ancient artifacts discovered during excavations.\n\nHere is a new test dataset.\n{json.dumps(dataset, indent=2)}\nProvide only the description.',
        },
    ]


def OPENAI_GEN_HYPO_MESSAGES(dataset):
    return [
        {
            'role': 'system',
            'content': 'You are a helpful assistant who is not talkative. You only respond with the exact answer to a query without additional conversation.',
        },
        {
            'role': 'user',
            'content': f'Given a dataset with its descriptions and the true functional relationship between its variables, your task is to generate 3 levels of hypotheses for the stated relationship in plain English. The three levels are "broad", "medium" and "narrow". Make sure that the hypotheses sound natural. *Only include concepts for variables that are present in the provided functional relationship.* Give your answer as a JSON.\n\nFor example, an example dataset might be the following:\n```json\n{{\n  "domain": "cybersecurity",\n  "summary": "This dataset is about measuring cybersecurity threats in a system. The data was collected by monitoring various cybersecurity metrics in a network environment. The purpose of the data collection is to assess and predict potential cybersecurity risks and vulnerabilities.",\n  "variables": [\n    {{\n      "description": "Level of cybersecurity threat",\n      "name": "cybersecurity_threat",\n      "is_target": true\n    }},\n    {{\n      "description": "Number of failed login attempts",\n      "name": "failed_login_attempts"\n    }},\n    {{\n      "description": "Amount of encrypted data",\n      "name": "encrypted_data"\n    }},\n    {{\n      "description": "Frequency of software updates",\n      "name": "software_updates"\n    }},\n    {{\n      "description": "Number of antivirus software installed",\n      "name": "antivirus_software"\n    }},\n    {{\n      "description": "Quality of firewall protection",\n      "name": "firewall_quality"\n    }}\n  ],\n  "relationship": {{\n    "dependent": "cybersecurity_threat",\n    "relation": "-53.5*encrypted_data**2 - 53.85*failed_login_attempts**2 + 67.75*firewall_quality - 92.16 - 36.68/software_updates**3"\n  }}\n}}```\nGiven this dataset, the following is a valid answer:\n```json\n{{\n  "broad": {{\n    "instruction": "Be vague. Only indicate which concepts might be related but not how they are related",\n    "hypothesis": "Threat to cybersecurity is influenced by several factors including the amount of encrypted data, the number of failed login attempts, the quality of the firewall, as well as how often the software is updated."\n  }},\n  "medium": {{\n    "instruction": "Be slightly more specific. For each factor, indicate carefully whether it positively or negatively affects the relationship, but do not indicate what the exponent is.",\n    "hypothesis": "Cybersecurity threat tends to decrease with the amount of data encryption, the number of failed login attempts, as well as the frequency of software updates to some extent, while improvement in the firewall quality has a positive effect."\n  }},\n  "narrow": {{\n    "instruction": "Be specific. Communicate the concepts, whether there is a positive or negative effect (be careful), and the meaning of the exponent",\n    "hypothesis": "The threat to cybersecurity interacts in a complex manner with various factors. As the amount of encrypted data increases, there is a quadratic decrease in threat. Similarly for the number of failed login attempts, there is a negative quadratic relationship. The quality of the firewall protection on the other hand demonstrates a positive and linear relationship. Finally, the frequency of software updates has an inverse cubic relationship to the threat."\n  }},\n}}\n```\n\nBased on this, provide an answer for the following test dataset:\n```json\n{dataset}```\nRespond only with a JSON.',
        },
    ]


def create_prompt(usr_msg):
    return [
        {
            'role': 'system',
            'content': 'You are a helpful assistant who is not talkative. You only respond with the exact answer to a query without additional conversation.',
        },
        {'role': 'user', 'content': usr_msg},
    ]


def get_response(client, prompt, max_retry=5, model='gpt-3.5-turbo', verbose=False):
    n_try = 0
    while n_try < max_retry:
        response = client.chat.completions.create(
            model=model, messages=create_prompt(prompt), **OPENAI_GEN_HYP
        )

        # COMMENT: changed from
        # response.choices[0].message.content.strip().strip('```json').strip('```')
        content = response.choices[0].message.content
        cleaned_content = content.split('```json')[1].split('```')[0].strip()
        output = cleaned_content
        try:
            response_json = json.loads(output)
            return response_json
        except ValueError:
            if verbose:
                print(f'Bad JSON output:\n\n{output}')
            n_try += 1
            if n_try < max_retry:
                if verbose:
                    print('Retrying...')
            else:
                if verbose:
                    print('Retry limit reached')
    return None


def get_code_fix(
    client, code, error, max_retry=5, model='gpt-3.5-turbo', verbose=False
):
    prompt = f"""\
Given the following code snippet and error message, provide a single-line fix for the error. \
Note that the code is going to be executed using python `eval`. \
The code should be executable and should not produce the error message. Be as specific as possible.

Here's the code and the error:
{{
    "code": "{code}",
    "error": "{error}"
}}

Return only a JSON object with the fixed code in the following format:
```json
{{
    "fixed_code": "..."
}}"""
    response = get_response(
        client, prompt, max_retry=max_retry, model=model, verbose=verbose
    )
    return response


def get_new_hypothesis(
    client, target, old, expr, cols, model='gpt-3.5-turbo', verbose=False
):
    prompt = f"""\
Given a target column from a dataset, a pandas expression to derive the column from existing columns, a list of \
existing columns, and a previously written hypothesis text, carefully check if the hypothesis text is consistent with \
the pandas expression or not. If it is consistent, simply return the hypothesis as it is. If it is not consistent, \
provide a new natural language hypothesis that is consistent with the pandas expression using only the provided \
information. Be specific.

Here's the information:
```json
{{
    "target_column": "{target}",
    "pandas_expression": "{expr}",
    "existing_columns": {json.dumps(cols, indent=4)}
    "old_hypothesis": "{old}",
}}```

Give your answer as a new JSON with the following format:
```json
{{
    "hypothesis": "..."
}}"""
    response = get_response(client, prompt, model=model, verbose=verbose)
    return response


def replace_variable(client, expr, old, new, model='gpt-3.5-turbo', verbose=False):
    prompt = f"""\
Given a pandas "expression", replace mentions of the "old" column with its "new" value such that the resultant \
expression is equivalent to the original expression.

Here's the information:
```json
{{
    "expression": "{expr}",
    "old": "{old}",
    "new": "{new}"
}}```

Give your answer as a new JSON with the following format:
```json
{{
    "new_expression": "..."
}}"""
    response = get_response(client, prompt, model=model, verbose=verbose)
    return response
