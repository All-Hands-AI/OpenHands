import json
import os
from typing import Any, Dict, List, Optional

import pandas as pd


# Placeholder for litellm's get_tokens function
def get_tokens(text: str) -> int:
    """
    Returns the number of tokens in the given text.
    Replace this function with litellm's actual get_tokens implementation.
    """
    # Example implementation (to be replaced)
    return len(text.split())


class EvalOutput:
    def __init__(
        self,
        instance_id: str,
        instruction: str,
        instance: Dict[str, Any],
        test_result: Dict[str, Any],
        metadata: Dict[str, Any],
        history: List[Dict[str, Any]],
        metrics: Optional[Dict[str, Any]] = None,
        llm_completions: Optional[List[Any]] = None,
        error: Optional[str] = None,
    ):
        self.instance_id = instance_id
        self.instruction = instruction
        self.instance = instance
        self.test_result = test_result
        self.metadata = metadata
        self.history = history
        self.metrics = metrics
        self.llm_completions = llm_completions or []
        self.error = error

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'EvalOutput':
        return EvalOutput(
            instance_id=data.get('instance_id', ''),
            instruction=data.get('instruction', ''),
            instance=data.get('instance', {}),
            test_result=data.get('test_result', {}),
            metadata=data.get('metadata', {}),
            history=data.get('history', []),
            metrics=data.get('metrics', None),
            llm_completions=data.get('llm_completions', []),
            error=data.get('error', None),
        )


def load_eval_outputs(jsonl_path: str) -> List[EvalOutput]:
    eval_outputs = []
    with open(jsonl_path, 'r') as file:
        content = file.read()
        try:
            # Try parsing as a single JSON object
            data = json.loads(content)
            eval_output = EvalOutput.from_dict(data)
            eval_outputs.append(eval_output)
        except json.JSONDecodeError:
            # If single JSON parse fails, try parsing as JSON Lines
            file.seek(0)
            for line_number, line in enumerate(file, start=1):
                if line.strip():  # Skip empty lines
                    try:
                        data = json.loads(line)
                        eval_output = EvalOutput.from_dict(data)
                        eval_outputs.append(eval_output)
                    except json.JSONDecodeError as e:
                        print(
                            f'Failed to parse line {line_number} in {jsonl_path}: {e}'
                        )
                        print(
                            f'Problematic line: {line[:100]}...'
                        )  # Print first 100 chars of the line

    if not eval_outputs:
        print(f'Warning: No valid data found in {jsonl_path}')

    return eval_outputs


def process_llm_completions(eval_output: EvalOutput) -> List[Dict[str, Any]]:
    """
    Processes the llm_completions of an EvalOutput to extract prompts (including system prompt) and responses.
    Handles both dictionary and string content formats.

    Args:
        eval_output (EvalOutput): The evaluation output instance.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing 'system_prompt', 'user_prompts', and 'response'.
    """
    completions = []
    for comp in eval_output.llm_completions:
        messages = comp.get('messages', [])
        response_content = comp.get('response', {}).get('choices', [])

        # Initialize prompts and response
        system_prompt = ''
        user_prompts = []
        response = ''

        # Extract system prompt and user prompts
        for message in messages:
            role = message.get('role')
            content = message.get('content', [])

            if role == 'system':
                system_prompt = _extract_text_content(content)
            elif role == 'user':
                user_prompts.append(_extract_text_content(content))

        # Extract the assistant's response
        if response_content and len(response_content) > 0:
            response = response_content[0].get('message', {}).get('content', '').strip()

        completions.append(
            {
                'system_prompt': system_prompt,
                'user_prompts': user_prompts,
                'response': response,
            }
        )
    return completions


def _extract_text_content(content):
    if isinstance(content, list):
        return '\n'.join(
            item.get('text', '').strip()
            for item in content
            if isinstance(item, dict) and item.get('type') == 'text'
        )
    elif isinstance(content, str):
        return content.strip()
    return ''


def create_results_dataframe(eval_outputs: List[EvalOutput]) -> pd.DataFrame:
    records = []
    for eo in eval_outputs:
        completions = process_llm_completions(eo)
        for comp in completions:
            prompt = comp['prompt']
            response = comp['response']
            token_count = get_tokens(prompt)
            records.append(
                {
                    'instance_id': eo.instance_id,
                    'prompt': prompt,
                    'response': response,
                    'token_count': token_count,
                }
            )
    df = pd.DataFrame(records)
    return df


def main():
    swe_bench_dir = 'evaluation/evaluation_outputs/outputs/swe-bench-lite/CodeActAgent/'
    results = []

    # Traverse through all subdirectories to find output.jsonl files
    for root, dirs, files in os.walk(swe_bench_dir):
        for file in files:
            if file.endswith('output.jsonl') or file.endswith('output-pretty.jsonl'):
                jsonl_path = os.path.join(root, file)
                print(f'Processing file: {jsonl_path}')
                try:
                    eval_outputs = load_eval_outputs(jsonl_path)
                    if eval_outputs:
                        df = create_results_dataframe(eval_outputs)
                        results.append(df)
                    else:
                        print(f'No valid data found in {jsonl_path}')
                except Exception as e:
                    print(f'Error processing {jsonl_path}: {e}')

    if results:
        final_df = pd.concat(results, ignore_index=True)
        final_df.to_csv('swe_bench_evaluation_results.csv', index=False)
        print('Results saved to swe_bench_evaluation_results.csv')
    else:
        print('No valid data found in any of the processed files.')


if __name__ == '__main__':
    main()
