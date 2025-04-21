# flake8: noqa: E501

import argparse
import asyncio
import multiprocessing as mp
import os
import pathlib
import subprocess
from argparse import Namespace
from typing import Any, Awaitable, TextIO

from tqdm import tqdm

from openhands.core.logger import openhands_logger as logger
from openhands.resolver.interfaces.issue import Issue
from openhands.resolver.resolve_issue import IssueResolver
from openhands.resolver.resolver_output import ResolverOutput


class AllIssueResolver(IssueResolver):
    def __init__(self, my_args: Namespace) -> None:
        """Initialize the AllIssueResolver with the given parameters."""

        self.my_args = my_args

        super().__init__(my_args)
        issue_numbers = None
        if my_args.issue_numbers:
            issue_numbers = [int(number) for number in my_args.issue_numbers.split(',')]

        self.issue_numbers = issue_numbers
        self.num_workers = my_args.num_workers
        self.limit_issues = my_args.limit_issues

    def cleanup(self) -> None:
        logger.info('Cleaning up child processes...')
        for process in mp.active_children():
            logger.info(f'Terminating child process: {process.name}')
            process.terminate()
            process.join()

    # This function tracks the progress AND write the output to a JSONL file
    async def update_progress(
        self, output: Awaitable[ResolverOutput], output_fp: TextIO, pbar: tqdm
    ) -> None:
        resolved_output = await output
        pbar.update(1)
        pbar.set_description(f'issue {resolved_output.issue.number}')
        pbar.set_postfix_str(
            f'Test Result: {resolved_output.metrics.get("test_result", "N/A") if resolved_output.metrics else "N/A"}'
        )
        logger.info(
            f'Finished issue {resolved_output.issue.number}: {resolved_output.metrics.get("test_result", "N/A") if resolved_output.metrics else "N/A"}'
        )
        output_fp.write(resolved_output.model_dump_json() + '\n')
        output_fp.flush()

    async def resolve_issues(self) -> None:
        """Resolve multiple github or gitlab issues using the instance variables."""
        issue_handler = self.issue_handler_factory()

        # Load dataset
        issues: list[Issue] = issue_handler.get_converted_issues(
            issue_numbers=self.issue_numbers
        )

        if self.limit_issues is not None:
            issues = issues[: self.limit_issues]
            logger.info(f'Limiting resolving to first {self.limit_issues} issues.')

        # TEST METADATA
        model_name = self.llm_config.model.split('/')[-1]

        pathlib.Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        pathlib.Path(os.path.join(self.output_dir, 'infer_logs')).mkdir(
            parents=True, exist_ok=True
        )
        logger.info(f'Using output directory: {self.output_dir}')

        # checkout the repo
        repo_dir = os.path.join(self.output_dir, 'repo')
        if not os.path.exists(repo_dir):
            checkout_output = subprocess.check_output(  # noqa: ASYNC101
                [
                    'git',
                    'clone',
                    issue_handler.get_clone_url(),
                    f'{self.output_dir}/repo',
                ]
            ).decode('utf-8')
            if 'fatal' in checkout_output:
                raise RuntimeError(f'Failed to clone repository: {checkout_output}')

        # get the commit id of current repo for reproducibility
        base_commit = (
            subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo_dir)  # noqa: ASYNC101
            .decode('utf-8')
            .strip()
        )
        logger.info(f'Base commit: {base_commit}')

        if self.repo_instruction is None:
            # Check for .openhands_instructions file in the workspace directory
            openhands_instructions_path = os.path.join(
                repo_dir, '.openhands_instructions'
            )
            if os.path.exists(openhands_instructions_path):
                with open(openhands_instructions_path, 'r') as f:  # noqa: ASYNC101
                    self.repo_instruction = f.read()

        # OUTPUT FILE
        output_file = os.path.join(self.output_dir, 'output.jsonl')
        logger.info(f'Writing output to {output_file}')
        finished_numbers = set()
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:  # noqa: ASYNC101
                for line in f:
                    data = ResolverOutput.model_validate_json(line)
                    finished_numbers.add(data.issue.number)
            logger.warning(
                f'Output file {output_file} already exists. Loaded {len(finished_numbers)} finished issues.'
            )
        output_fp = open(output_file, 'a')  # noqa: ASYNC101

        logger.info(
            f'Resolving issues with model {model_name}, max iterations {self.max_iterations}.'
        )

        # =============================================
        # filter out finished issues
        new_issues = []
        for issue in issues:
            if issue.number in finished_numbers:
                logger.info(f'Skipping issue {issue.number} as it is already finished.')
                continue
            new_issues.append(issue)
        logger.info(
            f'Finished issues: {len(finished_numbers)}, Remaining issues: {len(issues)}'
        )
        # =============================================

        pbar = tqdm(total=len(issues))

        # This sets the multi-processing
        logger.info(f'Using {self.num_workers} workers.')

        try:
            tasks = []
            for issue in issues:
                # checkout to pr branch
                if self.issue_type == 'pr':
                    logger.info(
                        f'Checking out to PR branch {issue.head_branch} for issue {issue.number}'
                    )

                    subprocess.check_output(  # noqa: ASYNC101
                        ['git', 'checkout', f'{issue.head_branch}'],
                        cwd=repo_dir,
                    )

                    base_commit = (
                        subprocess.check_output(  # noqa: ASYNC101
                            ['git', 'rev-parse', 'HEAD'], cwd=repo_dir
                        )
                        .decode('utf-8')
                        .strip()
                    )

                issue_resolver = IssueResolver(self.my_args)
                task = self.update_progress(
                    issue_resolver.process_issue(
                        issue,
                        base_commit,
                        issue_handler,
                        bool(self.num_workers > 1),
                    ),
                    output_fp,
                    pbar,
                )
                tasks.append(task)

            # Use asyncio.gather with a semaphore to limit concurrency
            sem = asyncio.Semaphore(self.num_workers)

            async def run_with_semaphore(task: Awaitable[Any]) -> Any:
                async with sem:
                    return await task

            await asyncio.gather(*[run_with_semaphore(task) for task in tasks])

        except KeyboardInterrupt:
            logger.info('KeyboardInterrupt received. Cleaning up...')
            self.cleanup()

        output_fp.close()
        logger.info('Finished.')


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Resolve multiple issues from Github or Gitlab.'
    )
    parser.add_argument(
        '--selected-repo',
        type=str,
        required=True,
        help='Github or Gitlab repository to resolve issues in form of `owner/repo`.',
    )
    parser.add_argument(
        '--token',
        type=str,
        default=None,
        help='Github or Gitlab token to access the repository.',
    )
    parser.add_argument(
        '--username',
        type=str,
        default=None,
        help='Github or Gitlab username to access the repository.',
    )
    parser.add_argument(
        '--runtime-container-image',
        type=str,
        default=None,
        help='Container image to use.',
    )
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=50,
        help='Maximum number of iterations to run.',
    )
    parser.add_argument(
        '--limit-issues',
        type=int,
        default=None,
        help='Limit the number of issues to resolve.',
    )
    parser.add_argument(
        '--issue-numbers',
        type=str,
        default=None,
        help='Comma separated list of issue numbers to resolve.',
    )
    parser.add_argument(
        '--num-workers',
        type=int,
        default=1,
        help='Number of workers to use for parallel processing.',
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='output',
        help='Output directory to write the results.',
    )
    parser.add_argument(
        '--llm-model',
        type=str,
        default=None,
        help='LLM model to use.',
    )
    parser.add_argument(
        '--llm-api-key',
        type=str,
        default=None,
        help='LLM API key to use.',
    )
    parser.add_argument(
        '--llm-base-url',
        type=str,
        default=None,
        help='LLM base URL to use.',
    )
    parser.add_argument(
        '--prompt-file',
        type=str,
        default=None,
        help='Path to the prompt template file in Jinja format.',
    )
    parser.add_argument(
        '--repo-instruction-file',
        type=str,
        default=None,
        help='Path to the repository instruction file in text format.',
    )
    parser.add_argument(
        '--issue-type',
        type=str,
        default='issue',
        choices=['issue', 'pr'],
        help='Type of issue to resolve, either open issue or pr comments.',
    )
    parser.add_argument(
        '--base-domain',
        type=str,
        default='github.com',
        help='Base domain for GitHub Enterprise (default: github.com)',
    )

    my_args = parser.parse_args()
    all_issue_resolver = AllIssueResolver(my_args)

    asyncio.run(all_issue_resolver.resolve_issues())


if __name__ == '__main__':
    main()
