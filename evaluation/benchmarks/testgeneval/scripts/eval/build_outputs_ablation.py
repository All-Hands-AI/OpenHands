import argparse
import copy
import difflib
import json
import os
import traceback


def insert_line_in_string(input_string, new_str, insert_line):
    """Inserts a new line into a string at the specified line number.

    :param input_string: The original string.
    :param new_str: The string to insert.
    :param insert_line: The line number at which to insert (1-based index).
    :return: The modified string.
    """
    file_text = input_string.expandtabs()
    new_str = new_str.expandtabs()

    file_text_lines = file_text.split('\n')

    new_str_lines = new_str.split('\n')
    new_file_text_lines = (
        file_text_lines[:insert_line] + new_str_lines + file_text_lines[insert_line:]
    )

    return '\n'.join(new_file_text_lines)


def print_string_diff(original, modified):
    """Prints the differences between two strings line by line.

    :param original: The original string.
    :param modified: The modified string.
    """
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)

    diff = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile='original',
        tofile='modified',
        lineterm='',
    )

    print(''.join(diff))


def parse_json_files(root_dir, output_dir, metadata_objs, preds_objs):
    final_output = {i: [] for i in range(25)}

    for subdir in sorted(os.listdir(root_dir)):  # Sorting ensures consistent order
        subdir_path = os.path.join(root_dir, subdir)
        # subdir_instance = subdir.rsplit('-', 1)[0]
        metadata = metadata_objs[subdir]
        orig_test_suite = metadata['test_result']['test_suite']

        if os.path.isdir(subdir_path):  # Check if it's a directory
            print(f'Processing subdirectory: {subdir}')

            # Now loop through the JSON files in this subdirectory
            i = 0
            test_suite = preds_objs[subdir] if subdir in preds_objs else ''
            for file in sorted(
                os.listdir(subdir_path)
            ):  # Sorting ensures consistent order
                metadata_copy = copy.deepcopy(metadata)
                if file.endswith('.json'):  # Check for JSON files
                    file_path = os.path.join(subdir_path, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)  # Load JSON data
                            try:
                                tool_calls = data['response']['choices'][0]['message'][
                                    'tool_calls'
                                ]
                                if tool_calls is not None:
                                    for tool_call in tool_calls:
                                        tool_call_dict = eval(
                                            tool_call['function']['arguments']
                                        )

                                        if (
                                            tool_call_dict is not None
                                            and tool_call_dict != {}
                                        ):
                                            command = tool_call_dict['command']
                                            if command == 'create':
                                                test_suite = tool_call_dict['file_text']
                                            if (
                                                command != 'str_replace'
                                                and command != 'insert'
                                                and 'coverage' not in command
                                            ):
                                                print(command)
                                            if command == 'insert':
                                                test_suite_new = insert_line_in_string(
                                                    test_suite,
                                                    tool_call_dict['new_str'],
                                                    tool_call_dict['insert_line'],
                                                )
                                                test_suite = test_suite_new
                                            if command == 'str_replace':
                                                if (
                                                    test_suite.count(
                                                        tool_call_dict['old_str']
                                                    )
                                                    == 1
                                                ):
                                                    test_suite_new = test_suite.replace(
                                                        tool_call_dict['old_str'],
                                                        tool_call_dict['new_str'],
                                                    )
                                                else:
                                                    continue
                                                test_suite = test_suite_new
                            except Exception:
                                print(traceback.format_exc())
                                continue

                            metadata_copy['test_result']['test_suite'] = test_suite
                            if i < 25:
                                final_output[i].append(metadata_copy)
                                i += 1
                    except Exception as e:
                        print(traceback.format_exc())
                        print(f'  Error loading {file_path}: {e}')

            for j in range(i, 24):
                final_output[j].append(metadata_copy)
            metadata_orig = copy.deepcopy(metadata)
            metadata_orig['test_result']['test_suite'] = orig_test_suite
            final_output[24].append(metadata_orig)

    for i in range(25):
        output_file = os.path.join(output_dir, f'output_{i}.jsonl')
        with open(output_file, 'w') as f:
            for metadata in final_output[i]:
                f.write(json.dumps(metadata) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parse JSON file')
    parser.add_argument('--root_dir', type=str, help='Root directory', required=True)
    parser.add_argument(
        '--output_dir', type=str, help='Output directory', required=True
    )
    parser.add_argument(
        '--starting_preds_file', type=str, help='Starting predictions', default=None
    )
    args = parser.parse_args()

    output_file = os.path.join(args.output_dir, 'output.jsonl')
    metadata_objs = {}
    with open(output_file, 'r') as f:
        content = f.readlines()
        for line in content:
            metadata = json.loads(line)
            metadata_objs[metadata['instance_id']] = metadata

    starting_preds_file = args.starting_preds_file
    preds_objs = {}
    if starting_preds_file is not None:
        with open(starting_preds_file, 'r') as f:
            content = f.readlines()
            for line in content:
                pred = json.loads(line)
                preds_objs[pred['id']] = pred['preds']['full'][0]

    parse_json_files(args.root_dir, args.output_dir, metadata_objs, preds_objs)
