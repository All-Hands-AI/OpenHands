import json

input_file = 'XXX.jsonl'
output_file = 'YYY.jsonl'

with (
    open(input_file, 'r', encoding='utf-8') as fin,
    open(output_file, 'w', encoding='utf-8') as fout,
):
    for line in fin:
        line = line.strip()
        if not line:
            continue

        data = json.loads(line)
        item = data

        # 提取原始数据
        org = item.get('org', '')
        repo = item.get('repo', '')
        number = str(item.get('number', ''))

        new_item = {}
        new_item['repo'] = f'{org}/{repo}'
        new_item['instance_id'] = f'{org}__{repo}-{number}'
        new_item['problem_statement'] = (
            item['resolved_issues'][0].get('title', '')
            + '\n'
            + item['resolved_issues'][0].get('body', '')
        )
        new_item['FAIL_TO_PASS'] = []
        new_item['PASS_TO_PASS'] = []
        new_item['base_commit'] = item['base'].get('sha', '')
        new_item['version'] = '0.1'  # depends

        output_data = new_item
        fout.write(json.dumps(output_data, ensure_ascii=False) + '\n')
