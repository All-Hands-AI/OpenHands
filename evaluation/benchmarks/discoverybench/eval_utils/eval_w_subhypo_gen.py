import json
import logging

from openai import OpenAI

from .lm_utils import run_chatgpt_query_multi_turn
from .openai_helpers import get_response

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(name)s -   %(message)s',
    datefmt='%m/%d/%Y %H:%M:%S',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def get_score_from_answer(type, answer):
    if type == 'context':
        answer = answer.replace('Answer:', '').strip()
        if answer.startswith('A)'):
            return 1.0
        elif answer.startswith('B)'):
            return 0.0
        return -1.0

    elif type == 'var':
        try:
            var_json = json.loads(answer)
            # print(f"var_json:{var_json}")
            p = 0.0
            r = 0.0
            f1 = 0.0
            if var_json['sizeB']:
                p = var_json['intersection'] / var_json['sizeB']
            if var_json['sizeA']:
                r = var_json['intersection'] / var_json['sizeA']
            if p > 0.0 and r > 0.0:
                f1 = (2 * p * r) / (p + r)
            else:
                f1 = 0.0
            eval_rec = {
                'p': p,
                'r': r,
                'f1': f1,
                'sizeA': var_json['sizeA'],
                'sizeB': var_json['sizeB'],
                'intersection': var_json['intersection'],
                'explanation': var_json['explanation'],
            }
            print(f'var_eval: {eval_rec}')
            return eval_rec
        except Exception:  # COMMENT: added Exception
            return {'p': -1.0, 'r': -1.0, 'f1': -1.0}
    elif type == 'rel':
        print(answer)
        rel_json = json.loads(answer)
        answer_str = rel_json['answer'].strip()
        if answer_str.startswith('A') or 'very similar' in answer_str:
            return 1.0
        elif (
            answer_str.startswith('B') or 'similar but general than HypoA' in answer_str
        ):
            return 0.5
        elif answer_str.startswith('C') or 'different' in answer_str:
            return 0.0
        return -1.0
    return -1.0


def ask_dimension_question(
    query,
    gold_hypo,
    gold_workflow,
    gen_hypo,
    gen_workflow,
    dataset_meta,
    llm_used,
    dimension,
    dataset_type,
    use_column_metadata=True,
):
    dimension_question = ''
    answer = ''
    score = 0.0
    if dimension == 'var':
        score = {'p': -1.0, 'r': -1.0, 'f1': -1.0}
    num_tokens = 256
    num_retries = 1
    json_response = False

    messages = [
        {
            'role': 'system',
            'content': 'You are an AI assistant that helps evaluate a data-driven hypothesis. You are a helpful assistant who is not talkative. You only respond with the exact answer to a query without additional conversation.',
        },
    ]
    if dimension == 'context':
        dimension_question = """\
        Question: Is HypoB defined in the same context as HypoA?
        (Context refers to assumptions/stratification under which the hypotheses are defined.)
        Options: A) same   B) different
        What is your answer?"""
    elif dimension == 'var':
        dimension_question = """\
        Question: For both HypoA and HypoB, what are the different variables found in the hypotheses? \
        Return your answer as a JSON object in the following format:
        ```json
        {{
        "sizeA": num of variables used in HypoA
        "sizeB": num of variables used in HypoB
        "intersection": num of variables common in HypoA and HypoB. Use *fuzzy matching* to determine intersection, accounting for paraphrases or slightly different surface forms
        "explanation": a short text explanation about the variables
        }}```
        Answer:"""
        num_tokens = 512
        num_retries = 1
        json_response = True
    elif dimension == 'rel':
        dimension_question = """\
        Question: Does HypoB exhibit the same relation as HypoA?
        Compare using following example hierarchy of relationships (based on specificity): \
        "there exists a relationship" > "positive relationship" > "positive AND (linear OR quadratic)" > "positive AND linear".
        Options: A) very similar B) similar but general than HypoA C) different
        Return your answer as a JSON object in the following format:
        ```json
        {{
        "answer": one of the options from A) very similar B) similar but general than HypoA C) different
        "explanation": a short text explanation about the relationship comparison
        }}```
        Answer:"""
        num_tokens = 512
        num_retries = 1
        json_response = True

    datasets_json = prepare_dataset_metadata_json(
        dataset_meta, dataset_type=dataset_type, use_column_metadata=use_column_metadata
    )

    dimension_question_str = f"""\
        You are going to compare two natural-language hypotheses HypoA and HypoB accompanied with optional workflows: WorkflowA for HypoA and WorkflowB for HypoB. \
        Both the hypotheses answer the natural language query "QUERY" over the dataset(s) described by dataset description(s) and column description(s) below. \
        Compare HypoA and HypoB in terms of three aspects: Contexts, Variables, and Relations. \
        E.g., for the hypothesis "From 1995 to 2009, the number of sandhill cranes around the tundra (Indigilka River) surged by an astounding ~10X":
        * Contexts refer to stratification of the data under which the given hypothesis is True. E.g., "For all women", "From 1995 to 2009".
        * Variables refer to the set of variables (either dependent or independent) that are mentioned in the hypothesis. E.g., number of sandhill cranes, location.
        * Relations refer to the form of relation between the variables. E.g., "surged by ~10x".

        Answer following questions for a given pair of hypotheses, HypoA and HypoB, along with an explanation grounded on the QUERY and the DATASET(S).

        Here is the metadata for the task:
        ```json
        {{
        "datasets": {datasets_json},
        "query": {query},
        "HypoA": {gold_hypo},
        "WorkflowA": {gold_workflow},
        "HypoB": {gen_hypo},
        "WorkflowB": {gen_workflow}
        }}
        ```

        {dimension_question}"""

    messages.append({'role': 'user', 'content': dimension_question_str})
    for retry in range(num_retries):
        response = run_chatgpt_query_multi_turn(
            messages=messages,
            model_name=llm_used,
            max_tokens=num_tokens,
            temperature=0,  # 0 for greedy best decoding
            json_response=json_response,
        )
        if response is not None:  # COMMENT: changed from != to is not
            break

    if response is not None:  # COMMENT: changed from != to is not
        answer = response.choices[0].message.content.strip()
        score = get_score_from_answer(type=dimension, answer=answer)

    return dimension_question, answer, score


def prepare_dataset_metadata_json(dataset_meta, dataset_type, use_column_metadata=True):
    if dataset_meta is None:  # COMMENT: changed from == to is None
        return [
            {
                'dataset_description': '',
                'columns': [],
            }
        ]
    datasets_json = []
    if dataset_type == 'real':
        for d in dataset_meta['datasets']:
            datasets_json.append(
                {
                    'dataset_description': d['description'],
                    'columns': [
                        {'name': col['name'], 'description': col['description']}
                        for col in d['columns']['raw']
                    ]
                    if use_column_metadata
                    else [],
                }
            )
    else:
        for d in dataset_meta['datasets']:
            datasets_json.append(
                {
                    'dataset_description': d['description'],
                    'columns': [
                        {'name': col['name'], 'description': col['description']}
                        for col in d['columns']
                    ]
                    if use_column_metadata
                    else [],
                }
            )
    return datasets_json


def get_sub_hypotheses(
    query,
    hypo,
    workflow,
    dataset_meta,
    llm_used,
    dataset_type,
    use_column_metadata=True,
):
    client = OpenAI()
    extraction_prompt = """\
        Given a set of dataset columns, a ground-truth hypothesis, and the analysis workflow used, your task is to extract three dimensions that define the hypothesis: Context, Variables, and Relations. \
        Here are the definitions for these dimensions:
        - Contexts: Boundary conditions that limit the scope of a hypothesis. E.g., “for men over \
        the age of 30”, “in Asia and Europe”. If the context applies to the full dataset, then extract the context from the dataset_descrption.
        - Variables: Known concepts that interact in a meaningful way under a given context to \
        produce the hypothesis. E.g., gender, age, income, or "None" if there is no interacting variable.
        - Relations: Interactions between a given set of variables under a given context to produce \
        the hypothesis. E.g., “quadratic relationship”, “inversely proportional”, piecewise conditionals, \
        or "None" if there is no interacting relationship.
        Make sure to only use the information present in the hypothesis and the workflow. Do not add any new information. \
        For each dimension, be specific, and do not omit any important details.

        Here is the metadata for the task:
        ```json
        {
        "datasets": %s,
        "hypothesis": "%s",
        "workflow": "%s"
        }
        ```

        Return your answer as a JSON object in the following format:
        ```json
        {
        "sub_hypo": [
            {
                "text": the hypothesis in natural language,
                "context": a short text description of the context of the hypothesis,
                "variables": a list of columns involved in the hypothesis,
                "relations": a short text description of the relationship between the variables of the hypothesis
            },
            ...
        ]
        }```
        """
    datasets_json = prepare_dataset_metadata_json(
        dataset_meta, dataset_type, use_column_metadata=use_column_metadata
    )
    _prompt = extraction_prompt % (datasets_json, hypo, workflow)
    sub_hypo_json = get_response(client, _prompt, model=llm_used, max_retry=1)

    if sub_hypo_json is not None:  # COMMENT: changed from != to is not
        # print(f"full hypothesis: {hypo}")
        print(f'sub_hypo_json: {sub_hypo_json}')
    else:
        sub_hypo_json = {
            'sub_hypo': [],
        }

    sub_hypo_json['full_hypo'] = hypo

    return sub_hypo_json


def match_context_with_gpt(
    gold_hyp, gold_context, pred_hyp, pred_context, model='gpt-3.5-turbo'
):
    prompt = f"""\
        Given a gold hypothesis, a gold context, a predicted hypothesis, and a predicted context, your task is \
        to determine if the predicted context semantically matches the ground-truth context. \
        Here is the definition for Context: Boundary conditions that limit the scope of a sub-hypothesis. E.g., “for men over the age of 30”, “in Asia and Europe”. If the context applies to the full dataset, then the context is derived from the dataset_descrption. \
        Here is the definition for Context: Boundary conditions that limit the scope of a sub-hypothesis. E.g., “for men over the age of 30”, “in Asia and Europe”. If the context applies to the full dataset, then the context is derived from the dataset_descrption. \
        If the predicted context matches the gold context, return true, otherwise return false.
        If both gold and predicted hypotheses are defined over the context of the full dataset, then also return true.
        If both gold and predicted hypotheses are defined over the context of the full dataset, then also return true.

        Here is the metadata for the task:
        ```json
        {{
            "gold_hypothesis": "{gold_hyp}",
            "gold_context": "{gold_context}",
            "predicted_hypothesis": "{pred_hyp}",
            "predicted_context": "{pred_context}"
        }}
        ```

        Return your answer as a JSON object in the following format:
        ```json
        {{
            "match": true or false
        }}
        ```"""

    client = OpenAI()
    output = get_response(client, prompt, model=model)
    return output.get('match', False)


def is_matching_context(gold_hyp, gold_context, pred_hyp, pred_context, llm_used):
    if gold_context == pred_context:
        return True
    if 'None' in [gold_context, pred_context]:
        return False
    return match_context_with_gpt(
        gold_hyp, gold_context, pred_hyp, pred_context, model=llm_used
    )


def run_eval_gold_vs_gen_NL_subhypo(
    query,
    gold_hypo,
    gold_workflow,
    gen_hypo,
    gen_workflow,
    dataset_meta,
    llm_used,
    context_score,
    dataset_type,
    use_column_metadata=True,
):
    # GPT-4 based evaluation to evaluate generated hypothesis in terms of context, variables, relation

    eval_rec = {
        'query': query,
        'HypoA': gold_hypo,
        'WorkflowA': gold_workflow,
        'HypoB': gen_hypo,
        'WorkflowB': gen_workflow,
    }

    for dimension in ['var', 'rel']:
        question, answer, score = ask_dimension_question(
            query,
            gold_hypo,
            gold_workflow,
            gen_hypo,
            gen_workflow,
            dataset_meta,
            llm_used,
            dimension=dimension,
            dataset_type=dataset_type,
            use_column_metadata=use_column_metadata,
        )

        eval_rec[dimension] = {'question': question, 'answer': answer, 'score': score}

    eval_rec['context'] = context_score
    eval_rec['accuracy_score'] = (
        1.0
        * eval_rec['context']['score']
        * eval_rec['var']['score']['f1']
        * eval_rec['rel']['score']
    )

    return eval_rec


def run_eval_gold_vs_gen_NL_hypo_workflow(
    query,
    gold_hypo,
    gold_workflow,
    gen_hypo,
    gen_workflow,
    dataset_meta,
    llm_used,
    dataset_type,
    use_column_metadata=True,
):
    # Input: Dataset Metadata, Query, Gold {Hg, Wg}, Predicted {Hp, Wp}
    # Output: eval_rec json includes final_score

    # Procedure:
    # Dataset Metadata, Query, Gold {Hg, Wg}, Pred {Hg, Wg}
    # Gold: [Hg1, Hg2] (compute on the fly) Hg1 is a NL form of subhypothesis
    # Predicted: [Hp1, Hp2] (compute on the fly)

    # Compute Intersection: [(Hg_i, Hp_j), …]  # tuples of (gold,pred) that matched with context (do this w/o explicit extraction)
    # # filter so that a gold context and a predicted context are only attached to one tuple
    # Compute recall_context (programmatically)

    # r_v_list = []
    # For (Hg_i, Hp_j) in the intersection:
    #             With Hg_i, Hp_j in NL, ask GPT4 → #variables and #intersection and a paragraph explanation and programmatically calculate f1_v
    # Hg_i, Hp_j in NL, ask GPT4 → matching score (0, 0.5 or 1) : A) very similar B) similar but general than HypoA C) different + explanation
    # 	r_v_list ← f1_v * score_r
    # accuracy_score = mean(r_v_list)
    # score =   [ recall_context * mean over predicted context(context_score * var_score *rel_score )]

    # recall_context = 1.0  # COMMENT: never used
    eval_rec = {
        'query': query,
        'HypoA': gold_hypo,
        'WorkflowA': gold_workflow,
        'HypoB': gen_hypo,
        'WorkflowB': gen_workflow,
    }

    gold_sub_hypo_json = get_sub_hypotheses(
        query=query,
        hypo=gold_hypo,
        workflow=gold_workflow,
        dataset_meta=dataset_meta,
        llm_used=llm_used,
        dataset_type=dataset_type,
        use_column_metadata=use_column_metadata,
    )
    if len(gold_sub_hypo_json['sub_hypo']) == 0:
        gold_sub_hypo_json['sub_hypo'] = [
            {
                'text': gold_hypo,
                'context': 'None',
                'variables': [],
                'relations': '',
                'explanation': 'unable to segment',
            }
        ]
    print(f'gold_sub_hypo_json: {gold_sub_hypo_json}')

    gen_sub_hypo_json = get_sub_hypotheses(
        query=query,
        hypo=gen_hypo,
        workflow=gen_workflow,
        dataset_meta=dataset_meta,
        llm_used=llm_used,
        dataset_type=dataset_type,
        use_column_metadata=use_column_metadata,
    )
    if len(gen_sub_hypo_json['sub_hypo']) == 0:
        gen_sub_hypo_json['sub_hypo'] = [
            {
                'text': gen_hypo,
                'context': 'None',
                'variables': [],
                'relations': '',
                'explanation': 'unable to segment',
            }
        ]
    print(f'gen_sub_hypo_json: {gen_sub_hypo_json}')

    eval_rec['gold_sub_hypo'] = gold_sub_hypo_json
    eval_rec['gen_sub_hypo'] = gen_sub_hypo_json

    gold_subh_covered = []
    gen_subh_to_gold_subh = dict()
    gen_gold_subh_to_context = dict()

    for p_id, gen_subh in enumerate(gen_sub_hypo_json['sub_hypo']):
        gen_subh_to_gold_subh[p_id] = -1

        for g_id, gold_subh in enumerate(gold_sub_hypo_json['sub_hypo']):
            if g_id in gold_subh_covered:
                continue

            # match context
            context_bool = is_matching_context(
                gold_subh['text'],
                gold_subh.get('context', ''),
                gen_subh['text'],
                gen_subh.get('context', ''),
                llm_used,
            )
            if context_bool:
                context_score = 1.0
            else:
                context_score = 0.0

            if context_score == 1.0:  # match only when context_score = 1.0
                gen_subh_to_gold_subh[p_id] = g_id
                gold_subh_covered.append(g_id)
                gen_gold_subh_to_context[f'P{p_id}||G{g_id}'] = {
                    'question': f"""Comapring: GoldH: {gold_subh['text']}, GoldC: {gold_subh['context']}\nGenH: {gen_subh['text']}, GenC: {gen_subh['context']}""",
                    'answer': context_bool,
                    'score': context_score,
                }
                break

    print(f'gen_subh_to_gold_subh: {gen_subh_to_gold_subh}')
    eval_rec['gen_subh_to_gold_subh'] = gen_subh_to_gold_subh
    eval_rec['gold_subh_covered'] = gold_subh_covered
    matched_gold_gen_subh_evals = dict()
    sum_accuracy_score = 0.0
    for p_id, g_id in gen_subh_to_gold_subh.items():
        if g_id >= 0:
            key = f'P{p_id}||G{g_id}'
            context_score = gen_gold_subh_to_context[key]
            subh_eval_rec = run_eval_gold_vs_gen_NL_subhypo(
                query,
                gold_hypo,
                gold_workflow,
                gen_hypo,
                gen_workflow,
                dataset_meta,
                llm_used,
                context_score,
                dataset_type=dataset_type,
                use_column_metadata=use_column_metadata,
            )
            sum_accuracy_score += subh_eval_rec['accuracy_score']
            matched_gold_gen_subh_evals[key] = subh_eval_rec

    eval_rec['matched_gold_gen_subh_evals'] = matched_gold_gen_subh_evals
    eval_rec['recall_context'] = (
        len(gold_subh_covered) / len(gold_sub_hypo_json['sub_hypo'])
        if len(gold_sub_hypo_json['sub_hypo'])
        else 0.0
    )
    mean_accuracy_score = (
        sum_accuracy_score / len(gen_subh_to_gold_subh)
        if len(gen_subh_to_gold_subh)
        else 0.0
    )
    eval_rec['mean_accuracy_score'] = mean_accuracy_score
    final_score = eval_rec['recall_context'] * mean_accuracy_score
    eval_rec['final_score'] = final_score
    print(f'eval_rec: {json.dumps(eval_rec, indent=2)}')

    return eval_rec
