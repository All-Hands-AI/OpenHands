import argparse
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file')
    parser.add_argument('output_file')

    args = parser.parse_args()
    input_file = args.input_file
    output_file = args.output_file
    model_name = 'claude-3.7-sonnet'
    output_list = []
    with open(input_file, 'r') as f:
        for idx, line_val in enumerate(f.readlines()):
            data = json.loads(line_val.strip())

            instance_id = data['instance_id']
            model_patch = ''
            if 'git_patch' in data:
                model_patch = data['git_patch']
            elif 'test_result' in data and 'git_patch' in data['test_result']:
                model_patch = data['test_result']['git_patch']
            if model_patch == '':
                continue
            answer = {}
            answer['instance_id'] = instance_id
            answer['model_patch'] = model_patch
            answer['model_name_or_path'] = model_name
            output_list.append(answer)

    with open(output_file, 'w') as f:
        json.dump(output_list, f)


if __name__ == '__main__':
    main()
