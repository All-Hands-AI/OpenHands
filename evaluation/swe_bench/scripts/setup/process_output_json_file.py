import json
import sys


def process_jsonl(input_file, model_name, output_file):
    try:
        with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
            data = []
            for line in infile:
                if line.strip():  # Ensure the line is not empty
                    json_obj = json.loads(line)
                    # Create new object with required fields and new model_name
                    new_obj = {
                        'instance_id': json_obj['instance_id'],
                        'model_patch': json_obj['git_patch'],
                        'model_name_or_path': model_name,
                    }
                    data.append(new_obj)
            json.dump(
                data, outfile, indent=2
            )  # Write the list of JSON objects to a file
        print(f'Output JSON list created at {output_file}')
    except Exception as e:
        print(f'Error: {str(e)}')


# Usage: python script.py input.jsonl model_name output.json
if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('Usage: python script.py <input_file> <model_name> <output_file>')
    else:
        input_file = sys.argv[1]
        model_name = sys.argv[2]
        output_file = sys.argv[3]
        process_jsonl(input_file, model_name, output_file)
