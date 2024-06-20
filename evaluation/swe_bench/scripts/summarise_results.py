import json
import sys


def extract_test_results(json_file_path):
    passed_instances = set()
    all_instances = set()

    with open(json_file_path, 'r') as file:
        report = json.load(file)

        # Add resolved instances
        for instance_id in report['resolved']:
            passed_instances.add(instance_id)

        # Add all instances in the report
        for _, instance_ids in report.items():
            for instance_id in instance_ids:
                all_instances.add(instance_id)

    return passed_instances, all_instances


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(
            'Usage: poetry run python summarise_results.py <path_to_report_json_file>'
        )
        sys.exit(1)
    json_file_path = sys.argv[1]
    passed_instances, all_instances = extract_test_results(json_file_path)
    succ_rate = len(passed_instances) / len(all_instances)
    print(
        f'\nPassed {len(passed_instances)} tests, total {len(all_instances)} tests, resolve rate = {succ_rate:.2%}'
    )
    print('PASSED TESTS:')
    print(sorted(list(passed_instances)))
    print('FAILED TESTS:')
    print(sorted(list(all_instances - passed_instances)))
