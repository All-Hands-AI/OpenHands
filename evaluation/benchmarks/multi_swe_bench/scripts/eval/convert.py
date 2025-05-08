import json
import re

IN_FILE = 'output.jsonl'
OUT_FILE = 'patch.jsonl'


def main():
    with open(IN_FILE, 'r') as fin:
        with open(OUT_FILE, 'w') as fout:
            for line in fin:
                data = json.loads(line)
                groups = re.match(r'(.*)__(.*)-(.*)', data['instance_id'])
                patch = {
                    'org': groups.group(1),
                    'repo': groups.group(2),
                    'number': groups.group(3),
                    'fix_patch': data['test_result']['git_patch'],
                }
                fout.write(json.dumps(patch) + '\n')


if __name__ == '__main__':
    main()
