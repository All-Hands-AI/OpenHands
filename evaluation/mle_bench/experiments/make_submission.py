import argparse
import json
from logging import Logger
from pathlib import Path

import pandas as pd
from mlebench.utils import get_logger


def main(
    metadata_path: Path,
    output: Path,
    rel_log_path: Path,
    rel_code_path: Path,
    logger: Logger,
):
    run_statuses = []
    submission_lines = []

    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    for run_id in metadata['runs']:
        run_dir = metadata_path.parent / run_id
        # run_id is something like f"{comp_id}_bfa0c73d"
        comp_id = run_id.split('_')[0]

        log_path = run_dir / rel_log_path
        has_log = log_path.exists()
        code_path = run_dir / rel_code_path
        has_code = code_path.exists()
        submission_path = run_dir / 'submission/submission.csv'
        submitted = submission_path.exists()

        submission_lines.append(
            {
                'competition_id': comp_id,
                'submission_path': submission_path.as_posix() if submitted else None,
                'logs_path': log_path.as_posix() if has_log else None,
                'code_path': code_path.as_posix() if has_code else None,
            }
        )

        run_status = {
            'competition_id': comp_id[:20],
            'has_log': has_log,
            'has_code': has_code,
            'submitted': submitted,
        }
        run_statuses.append(run_status)

    status_df = pd.DataFrame(run_statuses)
    logger.info(f'All runs:\n{status_df.to_string()}')

    # Create submission.jsonl
    with open(output, 'w') as f:
        for line in submission_lines:
            f.write(f'{json.dumps(line)}\n')
    logger.info(f'Written sorted submission to {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Makes a submission.jsonl for mlebench grade from a mlebench run group'
    )

    parser.add_argument(
        '--metadata',
        type=str,
        help='Path to metadata.json file',
        required=True,
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Path to the output jsonl file which can be used for `mlebench grade`',
        default='submission.jsonl',
    )
    parser.add_argument(
        '--rel-log-path',
        type=str,
        help='Path to logfile for analysis, relative to a run checkpoint. For example, if your logs are at `{runs_dir}/{run_id}/{checkpoint}/logs/agent.log`, this should be `logs/agent.log`.',
        default='logs/agent.log',
    )
    parser.add_argument(
        '--rel-code-path',
        type=str,
        help='Path to code file for analysis, relative to a run checkpoint. For example, if your code is at `{runs_dir}/{run_id}/{checkpoint}/code/train.py`, this should be `code/train.py`.',
        default='code/train.py',
    )

    args = parser.parse_args()
    logger = get_logger(__name__)

    main(
        metadata_path=Path(args.metadata),
        output=Path(args.output),
        rel_log_path=Path(args.rel_log_path),
        rel_code_path=Path(args.rel_code_path),
        logger=logger,
    )
