import json
import sys


def extract_test_results(json_file_path):
    passed_tests = []
    failed_tests = []
    with open(json_file_path, 'r') as file:
        for line in file:
            data = json.loads(line.strip())
            instance_id = data['instance_id']
            resolved = False
            if 'fine_grained_report' in data:
                resolved = data['fine_grained_report']['resolved']
            else:
                resolved = data['test_result']['result']['resolved']
            if resolved:
                passed_tests.append(instance_id)
            else:
                failed_tests.append(instance_id)
    return passed_tests, failed_tests


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(
            'Usage: poetry run python summarise_results.py <path_to_output_merged_jsonl_file>'
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
