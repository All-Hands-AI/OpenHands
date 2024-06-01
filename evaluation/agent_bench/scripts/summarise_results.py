import json
import sys


def extract_test_results(res_file_path: str) -> tuple[list[str], list[str]]:
    passed = []
    failed = []
    with open(res_file_path, 'r') as file:
        for line in file:
            data = json.loads(line.strip())
            instance_id = data['instance_id']
            resolved = False
            if 'test_result' in data and 'result' in data['test_result']:
                resolved = data['test_result']['result']
            if resolved:
                passed.append(instance_id)
            else:
                failed.append(instance_id)
    return passed, failed


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(
            'Usage: poetry run python summarise_results.py <path_to_output_jsonl_file>'
        )
        sys.exit(1)
    json_file_path = sys.argv[1]
    passed_tests, failed_tests = extract_test_results(json_file_path)
    succ_rate = len(passed_tests) / (len(passed_tests) + len(failed_tests))
    print(
        f'\nPassed {len(passed_tests)} tests, failed {len(failed_tests)} tests, resolve rate = {succ_rate}'
    )
    print('PASSED TESTS:')
    print(passed_tests)
    print('FAILED TESTS:')
    print(failed_tests)
