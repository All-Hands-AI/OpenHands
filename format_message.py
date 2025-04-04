import json
import os
import re

# Add selected IDs list
SELECTED_IDS = [
    'astropy__astropy-13236',
    'astropy__astropy-13398',
    'astropy__astropy-13579',
    'astropy__astropy-13977',
    'scikit-learn__scikit-learn-13439',
    'astropy__astropy-14182',
    'astropy__astropy-14598',
    'astropy__astropy-14995',
    'astropy__astropy-7166',
    'astropy__astropy-8707',
    'django__django-10914',
    'django__django-10999',
    'django__django-11099',
    'django__django-11206',
    'django__django-11292',
    'django__django-11490',
    'django__django-11555',
    'django__django-11603',
    'django__django-11734',
    'django__django-11740',
    'django__django-11790',
    'django__django-11848',
    'django__django-11964',
    'django__django-12125',
    'django__django-12209',
    'django__django-12308',
    'django__django-12406',
    'django__django-12713',
    'django__django-12774',
    'django__django-12858',
    'django__django-12965',
    'django__django-13112',
    'django__django-13195',
    'django__django-13212',
    'django__django-13346',
    'django__django-13363',
    'django__django-13449',
    'django__django-13516',
    'django__django-13670',
    'django__django-13741',
    'django__django-13809',
    'django__django-13810',
    'django__django-13821',
    'django__django-13837',
    'django__django-14034',
    'django__django-14089',
    'django__django-14155',
    'django__django-14349',
    'django__django-14373',
    'django__django-14376',
    'django__django-14500',
    'django__django-14608',
    'django__django-14631',
    'django__django-14725',
    'django__django-14752',
    'django__django-14765',
    'django__django-14771',
    'django__django-15037',
    'django__django-15103',
    'django__django-15128',
    'django__django-15268',
    'django__django-15277',
    'django__django-15368',
    'django__django-15375',
    'django__django-15525',
    'django__django-15561',
    'django__django-15563',
    'django__django-15572',
    'django__django-15731',
    'django__django-15741',
    'django__django-15814',
    'django__django-15916',
    'django__django-15957',
    'django__django-15973',
    'django__django-16082',
    'django__django-16100',
    'django__django-16256',
    'django__django-16315',
    'django__django-16333',
    'django__django-16429',
    'django__django-16485',
    'django__django-16493',
    'django__django-16502',
    'django__django-16595',
    'django__django-16612',
    'django__django-16642',
    'django__django-16661',
    'django__django-16667',
    'django__django-16819',
    'django__django-16899',
    'django__django-16938',
    'django__django-16950',
    'django__django-17029',
    'matplotlib__matplotlib-13989',
    'matplotlib__matplotlib-20676',
    'matplotlib__matplotlib-20826',
    'matplotlib__matplotlib-21568',
    'matplotlib__matplotlib-22865',
    'matplotlib__matplotlib-22871',
    'matplotlib__matplotlib-23412',
    'matplotlib__matplotlib-24149',
    'matplotlib__matplotlib-24570',
    'matplotlib__matplotlib-24637',
    'matplotlib__matplotlib-24970',
    'matplotlib__matplotlib-25122',
    'matplotlib__matplotlib-25287',
    'matplotlib__matplotlib-25775',
    'matplotlib__matplotlib-25960',
    'matplotlib__matplotlib-26113',
    'matplotlib__matplotlib-26342',
    'mwaskom__seaborn-3069',
    'psf__requests-1766',
    'psf__requests-5414',
    'psf__requests-6028',
    'pydata__xarray-3095',
    'pydata__xarray-3151',
    'pydata__xarray-3305',
    'pydata__xarray-3993',
    'pydata__xarray-4075',
    'pydata__xarray-4966',
    'pydata__xarray-6599',
    'pydata__xarray-6938',
    'pylint-dev__pylint-4661',
    'pylint-dev__pylint-6386',
    'pylint-dev__pylint-7080',
    'pylint-dev__pylint-8898',
    'pytest-dev__pytest-10356',
    'pytest-dev__pytest-5262',
    'pytest-dev__pytest-5787',
    'pytest-dev__pytest-6197',
    'pytest-dev__pytest-7236',
    'pytest-dev__pytest-7324',
    'pytest-dev__pytest-7571',
    'scikit-learn__scikit-learn-10297',
    'scikit-learn__scikit-learn-10908',
    'scikit-learn__scikit-learn-12973',
    'scikit-learn__scikit-learn-13142',
    'scikit-learn__scikit-learn-14141',
    'scikit-learn__scikit-learn-14894',
    'scikit-learn__scikit-learn-25102',
    'scikit-learn__scikit-learn-25232',
    'scikit-learn__scikit-learn-25747',
    'scikit-learn__scikit-learn-25931',
    'sphinx-doc__sphinx-10449',
    'sphinx-doc__sphinx-10466',
    'sphinx-doc__sphinx-10614',
    'sphinx-doc__sphinx-7440',
    'sphinx-doc__sphinx-7454',
    'sphinx-doc__sphinx-7462',
    'sphinx-doc__sphinx-7748',
    'sphinx-doc__sphinx-7910',
    'sphinx-doc__sphinx-8035',
    'sphinx-doc__sphinx-8056',
    'sphinx-doc__sphinx-8269',
    'sphinx-doc__sphinx-8459',
    'sphinx-doc__sphinx-8548',
    'sphinx-doc__sphinx-8551',
    'sphinx-doc__sphinx-8593',
    'sphinx-doc__sphinx-8638',
    'sphinx-doc__sphinx-9367',
    'sphinx-doc__sphinx-9591',
    'sphinx-doc__sphinx-9602',
    'sphinx-doc__sphinx-9658',
    'sphinx-doc__sphinx-9673',
    'sympy__sympy-11618',
    'sympy__sympy-12096',
    'sympy__sympy-12419',
    'sympy__sympy-12481',
    'sympy__sympy-12489',
    'sympy__sympy-13372',
    'sympy__sympy-13480',
    'sympy__sympy-13551',
    'sympy__sympy-13647',
    'sympy__sympy-13798',
    'sympy__sympy-13974',
    'sympy__sympy-14531',
    'sympy__sympy-14711',
    'sympy__sympy-15017',
    'sympy__sympy-15599',
    'sympy__sympy-15809',
    'sympy__sympy-15875',
    'sympy__sympy-16450',
    'sympy__sympy-17630',
    'sympy__sympy-17655',
    'sympy__sympy-18189',
    'sympy__sympy-18199',
    'sympy__sympy-18763',
    'sympy__sympy-19783',
    'sympy__sympy-19954',
    'sympy__sympy-20154',
    'sympy__sympy-20438',
    'sympy__sympy-20590',
    'sympy__sympy-21379',
    'sympy__sympy-21612',
    'sympy__sympy-21847',
    'sympy__sympy-21930',
    'sympy__sympy-22080',
    'sympy__sympy-22714',
    'sympy__sympy-23413',
    'sympy__sympy-24443',
    'sympy__sympy-24562',
]


def get_issue_id_from_path(path, specified_issue_id=None):
    """Extract issue ID from path like '.../astropy__astropy-13236/...'

    Args:
        path: Path to extract issue ID from
        specified_issue_id: Optional issue ID specified via command line argument
    """

    # Otherwise use existing logic to check against SELECTED_IDS
    parts = path.split(os.sep)
    for part in parts:
        if any(selected_id in part for selected_id in SELECTED_IDS):
            return part
    return None


def extract_response_content(item):
    """Extract content from response object."""
    if not item or not isinstance(item, dict):
        return ''
    if 'response' in item:
        response = item['response']
        if isinstance(response, dict) and 'choices' in response:
            choices = response['choices']
            if isinstance(choices, list):
                contents = []
                choice = choices[0]
                if isinstance(choice, dict):
                    # Extract finish_reason if present
                    finish_reason = choice.get('finish_reason', '')

                    if 'message' in choice:
                        message = choice['message']
                        if isinstance(message, dict):
                            # Add content if present
                            if 'content' in message:
                                contents.append(message['content'])

                            # Add tool calls if present
                            if 'tool_calls' in message and isinstance(
                                message['tool_calls'], list
                            ):
                                for tool_call in message['tool_calls']:
                                    if isinstance(tool_call, dict):
                                        if 'function' in tool_call:
                                            func_info = tool_call['function']
                                            if isinstance(func_info, dict):
                                                # Format: Function: name(arguments)
                                                func_name = func_info.get('name', '')
                                                func_args = func_info.get(
                                                    'arguments', ''
                                                )
                                                if func_name and func_args:
                                                    contents.append(
                                                        f'Function: {func_name}({func_args})'
                                                    )

                    # Return both content and finish_reason
                    content = '\n\n'.join(filter(None, contents))
                    return {'content': content, 'finish_reason': finish_reason}
    return {'content': '', 'finish_reason': ''}


def get_timestamp_from_filename(filename):
    """Extract timestamp from filename like openai__o1-preview-1731707326.567636.json"""
    match = re.search(r'(\d+\.\d+)\.json$', filename)
    return float(match.group(1)) if match else 0


def get_last_user_message(json_data):
    """Extract the last user message from the messages array."""
    message_to_return = ''

    if 'messages' in json_data:
        messages = json_data['messages']
        if isinstance(messages, list):
            # get last user message
            msg = messages[-1]
            if isinstance(msg, dict) and 'content' in msg:
                if isinstance(msg['content'], str):
                    message_to_return += msg['content']
                elif isinstance(msg['content'], list):
                    # Handle case where content is a list of dicts with 'text' field
                    message_parts = []
                    for c in msg['content']:
                        if isinstance(c, dict) and 'text' in c:
                            message_parts.append(c['text'])
                    if message_parts:
                        message_to_return += '\n'.join(message_parts)

    return message_to_return


def get_first_user_message(json_data):
    """Extract the initial messages (user/system) from the messages array until a different role is encountered."""
    message_to_return = []
    if 'messages' in json_data:
        messages = json_data['messages']
        if isinstance(messages, list):
            for msg in messages:
                if not isinstance(msg, dict) or 'role' not in msg:
                    break
                if msg['role'] not in ['user', 'system']:
                    break
                if 'content' in msg:
                    if isinstance(msg['content'], str):
                        message_to_return.append(msg['content'])
                    elif isinstance(msg['content'], list):
                        # Handle case where content is a list of dicts with 'text' field
                        message_parts = []
                        for c in msg['content']:
                            if isinstance(c, dict) and 'text' in c:
                                message_parts.append(c['text'])
                        if message_parts:
                            message_to_return.append('\n'.join(message_parts))
    return '\n\n'.join(message_to_return)


def clean_observation(observation):
    """Clean and format the observation text."""
    try:
        # If observation is already a list (parsed JSON)
        if isinstance(observation, list):
            texts = []
            for item in observation:
                if isinstance(item, dict) and 'text' in item:
                    text = item['text']
                    texts.append(text)
            return '\n'.join(texts).strip()

        # If observation is a string that looks like a list of dicts
        elif (
            isinstance(observation, str)
            and observation.startswith('[')
            and observation.endswith(']')
        ):
            try:
                # Parse the string as JSON
                data = json.loads(observation)
                return clean_observation(data)  # Recursively process the parsed list
            except json.JSONDecodeError:
                return observation

        return observation

    except Exception as e:
        print(f'Error cleaning observation: {str(e)}')
        return observation


def count_valid_files(folder_path):
    """Count valid JSON files that represent model interactions."""
    count = 0
    for file in os.listdir(folder_path):
        # Skip if not json or contains draft_editor
        if not file.endswith('.json') or 'draft_editor' in file:
            continue
        # Skip metadata and responses_observations files
        if file == 'metadata.json' or 'responses_observations' in file:
            continue
        # If we get here, it's a valid file
        count += 1
    return count


def get_descriptive_finish_reason(finish_reason):
    """Convert basic finish reasons into more descriptive ones."""
    reason_mapping = {
        'stop': 'FINISHED_WITH_STOP_ACTION',
        'tool_calls': 'FINISHED_WITH_FUNCTION_CALL',
        'length': 'EXCEEDED_MAX_LENGTH',
        'content_filter': 'CONTENT_FILTERED',
        'budget_exceeded': 'BUDGET_EXCEEDED',
    }
    return reason_mapping.get(finish_reason, finish_reason.upper())


def process_files_with_observations(folder_path, error_dict=None):
    """Process JSON files and combine responses with observations for a single folder."""

    # Check if we exceeded budget
    total_files = count_valid_files(folder_path)
    exceeded_budget = total_files >= 30

    # Get issue ID and check if it's in selected list
    issue_id = get_issue_id_from_path(folder_path)
    if issue_id not in SELECTED_IDS:
        return  # Skip processing if not in selected list

    # Get all JSON files in this specific folder (not recursive)
    json_files = []
    for file in os.listdir(folder_path):
        if (
            file.endswith('.json')
            and 'draft_editor' not in file
            and file != 'metadata.json'
            and 'responses_observations' not in file
        ):
            full_path = os.path.join(folder_path, file)
            timestamp = get_timestamp_from_filename(file)
            json_files.append((full_path, timestamp))

    if not json_files:
        print(f'No valid JSON files found in {folder_path}')
        return

    # Sort files by timestamp
    json_files.sort(key=lambda x: x[1])

    # Prepare the output JSON structure
    output_data = {
        'initial_issue': '',
        'interactions': [],
        'final_response': '',
        'final_finish_reason': '',
    }

    # Get the initial issue from the first file
    try:
        with open(json_files[0][0], 'r', encoding='utf-8') as f:
            first_data = json.load(f)
            output_data['initial_issue'] = get_first_user_message(first_data)
    except Exception as e:
        print(f'Error getting initial issue: {str(e)}')

    # Process files in pairs
    for i in range(len(json_files) - 1):
        current_file_path, _ = json_files[i]
        next_file_path, _ = json_files[i + 1]

        try:
            # print(f"Processing pair: {os.path.basename(current_file_path)} -> {os.path.basename(next_file_path)}")

            # Load current file for response
            with open(current_file_path, 'r', encoding='utf-8') as f:
                current_data = json.load(f)

            # Load next file for observation
            with open(next_file_path, 'r', encoding='utf-8') as f:
                next_data = json.load(f)

            # Extract response from current file
            response = extract_response_content(current_data)

            # Extract last user message from next file as observation
            observation = get_last_user_message(next_data)
            observation = clean_observation(observation)

            if response['content']:
                # Add to interactions array
                output_data['interactions'].append(
                    {'response': response['content'], 'observation': observation}
                )
                # print(f"Added response-observation pair")
            else:
                print(f'No response found in {os.path.basename(current_file_path)}')

        except Exception as e:
            print(
                f'Error processing files {current_file_path} and {next_file_path}: {str(e)}'
            )

    # Handle the last file's response
    try:
        last_file_path, _ = json_files[-1]

        with open(last_file_path, 'r', encoding='utf-8') as f:
            last_data = json.load(f)
            last_response = extract_response_content(last_data)
            if last_response['content']:
                output_data['final_response'] = last_response['content']

                # Check if this issue has a loop error
                if error_dict and issue_id in error_dict:
                    output_data['final_finish_reason'] = error_dict[issue_id]
                # Otherwise use the existing logic
                elif exceeded_budget:
                    output_data['final_finish_reason'] = 'budget_exceeded'
                else:
                    output_data['final_finish_reason'] = get_descriptive_finish_reason(
                        last_response['finish_reason']
                    )
    except Exception as e:
        print(f'Error processing last file {last_file_path}: {str(e)}')

    if (
        output_data['initial_issue']
        or output_data['interactions']
        or output_data['final_response']
    ):
        # Save both JSON and TXT versions
        base_path = os.path.join(folder_path, 'responses_observations')

        # Save JSON version
        try:
            with open(f'{base_path}.json', 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2)
            print(f'Successfully wrote JSON to {base_path}.json')
        except Exception as e:
            print(f'Error writing JSON file: {str(e)}')

        # Save TXT version (formatted)
        try:
            with open(f'{base_path}.txt', 'w', encoding='utf-8') as f:
                # Write initial issue
                f.write(f"{'#' * 80}\n")
                f.write('INITIAL ISSUE:\n')
                f.write(f"{'#' * 80}\n")
                f.write(f"{output_data['initial_issue']}\n")
                f.write(f"{'#' * 80}\n\n")

                # Write interactions
                for interaction in output_data['interactions']:
                    f.write(f"\n{'=' * 80}\n")
                    f.write(f"RESPONSE:\n{interaction['response']}\n\n")
                    f.write(f"{'-' * 40} OBSERVATION {'-' * 40}\n")
                    f.write(f"{interaction['observation']}\n")

                # Write final response if exists
                if output_data['final_response']:
                    f.write(f"\n{'=' * 80}\n")
                    f.write(f"LAST RESPONSE:\n{output_data['final_response']}\n")
                    if output_data['final_finish_reason']:
                        f.write(
                            f"\nFINISH REASON: {output_data['final_finish_reason'].upper()}\n"
                        )

            print(f'Successfully wrote TXT to {base_path}.txt')
        except Exception as e:
            print(f'Error writing TXT file: {str(e)}')
    else:
        print(f'No content to write for {folder_path}')


def clean_existing_observations(root_directory):
    """Remove all existing responses_observations files regardless of selection."""
    for root, _, _ in os.walk(root_directory):
        base_path = os.path.join(root, 'responses_observations')
        if os.path.exists(f'{base_path}.txt'):
            os.remove(f'{base_path}.txt')
        if os.path.exists(f'{base_path}.json'):
            os.remove(f'{base_path}.json')


def find_issue_folder(root_directory, issue_id):
    """Find the folder path containing the specified issue_id.
    Specifically looks in llm_completions directories and skips evals."""
    # First, find all llm_completions directories
    for root, dirs, _ in os.walk(root_directory):
        # If we find llm_completions directory
        if 'llm_completions' in dirs:
            llm_path = os.path.join(root, 'llm_completions')
            # Look for issue_id inside llm_completions
            for issue_root, _, _ in os.walk(llm_path):
                if issue_id in issue_root:
                    return issue_root
    return None


def load_error_messages(root_directory):
    """Load error messages from output.jsonl file."""
    error_dict = {}
    output_path = os.path.join(root_directory, 'output.jsonl')

    if not os.path.exists(output_path):
        import pdb

        pdb.set_trace()
        print(f'Warning: output.jsonl not found at {output_path}')
        return error_dict

    with open(output_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                instance_id = data.get('instance_id')
                error = data.get('error')

                if instance_id and 'Agent got stuck in a loop' in error:
                    error_dict[instance_id] = 'AGENT_STUCK_IN_LOOP'
            except Exception:
                continue

    return error_dict


def process_model_variants(root_directory, issue_id=None):
    """Process all model variants in the root directory or a specific issue."""
    print(f'Starting processing from root directory: {root_directory}')

    try:
        # First, clean all existing observation files
        clean_existing_observations(root_directory)

        # If issue_id is provided, process only that folder
        if issue_id:
            error_dict = load_error_messages(root_directory)
            issue_folder = find_issue_folder(root_directory, issue_id)
            if issue_folder:
                print(f'Processing issue folder: {issue_folder}')
                process_files_with_observations(issue_folder, error_dict)
                return
            else:
                print(f'Could not find folder for issue: {issue_id}')
                return

        # Otherwise, look for model variants and llm_completions
        model_variants = [
            d
            for d in os.listdir(root_directory)
            if os.path.isdir(os.path.join(root_directory, d))
        ]

        if not model_variants:
            print('No model variants found!')
            return

        # Process each model variant
        for variant in model_variants:
            variant_path = os.path.join(root_directory, variant)
            print(f'\nProcessing model variant: {variant}')

            error_dict = load_error_messages(variant_path)

            # Look for llm_completions
            llm_path = os.path.join(variant_path, 'llm_completions')

            if os.path.exists(llm_path):
                print(f'Found llm_completions folder in {variant}')
                for root, dirs, files in os.walk(llm_path):
                    issue_id = get_issue_id_from_path(root)
                    if issue_id in SELECTED_IDS:
                        process_files_with_observations(root, error_dict)
            else:
                print(f'No llm_completions folder found in {variant}')

    except Exception as e:
        print(f'Error processing model variants: {str(e)}')


def main(root_directory, issue_id=None):
    """Main entry point for processing."""
    try:
        if not os.path.exists(root_directory):
            print(f'Error: Directory does not exist: {root_directory}')
            return

        print(f'Found root directory: {root_directory}')
        process_model_variants(root_directory, issue_id)

    except Exception as e:
        print(f'Error in main: {str(e)}')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Process model outputs')
    parser.add_argument('root_dir', help='Root directory containing the outputs')
    parser.add_argument('--issue-id', help='Specific issue ID to process')

    args = parser.parse_args()

    print(len(SELECTED_IDS))
    main(args.root_dir, args.issue_id)
