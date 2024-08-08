import argparse


def get_changed_code(target_filepath, line_start, include_signature=False):
    # copies changed code into /testing_files/
    # Note that this does NOT copy the function signature
    selected_lines = []
    offset = 1 if include_signature else 0

    with open('/testing_files/first_line_after_removed.txt', 'r') as f:
        first_line_after_removed = f.read()
    if first_line_after_removed is None:
        print('First line after removed is None')

    with open(target_filepath, 'r') as f:
        lines = f.read().split('\n')
        for i in range(line_start - offset, len(lines)):
            if lines[i].strip() == first_line_after_removed.strip():
                break
            selected_lines.append(lines[i])
    text = '\n'.join(selected_lines)
    return text


def copy_changed_code(
    target_filepath, generated_code_filepath, line_start, include_signature=False
):
    changed_code = get_changed_code(target_filepath, line_start, include_signature)
    with open(generated_code_filepath, 'w') as f:
        f.write(changed_code)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--target_filepath', type=str, required=True)
    parser.add_argument('--generated_code_filepath', type=str, required=True)
    parser.add_argument('--line_start', type=int, required=True)
    parser.add_argument('--include_signature', action='store_true')
    args = parser.parse_args()
    copy_changed_code(
        args.target_filepath,
        args.generated_code_filepath,
        args.line_start,
        args.include_signature,
    )
