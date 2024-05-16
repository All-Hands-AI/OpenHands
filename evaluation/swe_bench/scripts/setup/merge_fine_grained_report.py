import argparse
import json


def merge_fine_grained_report(od_output_file, fine_grained_report_file):
    merged_od_output_file = od_output_file.replace('.jsonl', '.merged.jsonl')
    merged_report = []
    fine_grained_report = json.load(open(fine_grained_report_file))
    for line in open(od_output_file):
        line = json.loads(line)
        instance_id = line['instance_id']
        line['fine_grained_report'] = fine_grained_report[instance_id]
        merged_report.append(line)
    # dump the merged report as a jsonl file
    with open(merged_od_output_file, 'w') as f:
        for line in merged_report:
            f.write(json.dumps(line) + '\n')
    print(f'Agent output with report merged created at {merged_od_output_file}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--od_output_file', help='Path to the OD output file')
    parser.add_argument(
        '--fine_grained_report_file', help='Path to the fine grained report file'
    )
    args = parser.parse_args()

    merge_fine_grained_report(args.od_output_file, args.fine_grained_report_file)
