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
            try:
                resolved = data['test_result']['result']['resolved']
            except Exception:
                print(
                    f'Test {instance_id} has no "resolved" attribute, error message is: {data["error"]}'
                )
            if resolved:
                passed_tests.append(instance_id)
            else:
                failed_tests.append(instance_id)
    return passed_tests, failed_tests


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(
            'Usage: poetry run python summarise_results.py <path_to_output.jsonl_file>'
        )
        print(
            'Example: poetry run python summarise_results.py ../evaluation_outputs/outputs/swe_bench_lite/CodeActSWEAgent/gpt-4o-2024-05-13_maxiter_50_N_v1.5-no-hint/output.jsonl'
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
