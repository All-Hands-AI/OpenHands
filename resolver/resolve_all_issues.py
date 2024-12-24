# flake8: noqa: E501

import argparse
import asyncio
import multiprocessing as mp
import os
import pathlib
import subprocess
from typing import Awaitable, TextIO

from tqdm import tqdm

import openhands
from openhands.core.config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.resolver.github_issue import GithubIssue
from openhands.resolver.resolve_issue import (
    issue_handler_factory,
    process_issue,
)
from openhands.resolver.resolver_output import ResolverOutput


def cleanup():
    print('Cleaning up child processes...')
    for process in mp.active_children():
        print(f'Terminating child process: {process.name}')
        process.terminate()
        process.join()


# This function tracks the progress AND write the output to a JSONL file
async def update_progress(
    output: Awaitable[ResolverOutput], output_fp: TextIO, pbar: tqdm
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


async def resolve_issues(
    owner: str,
    repo: str,
    token: str,
    username: str,
    max_iterations: int,
    limit_issues: int | None,
    num_workers: int,
    output_dir: str,
    llm_config: LLMConfig,
    runtime_container_image: str,
    prompt_template: str,
    issue_type: str,
    repo_instruction: str | None,
    issue_numbers: list[int] | None,
) -> None:
    """Resolve multiple github issues.

    Args:
        owner: Github owner of the repo.
        repo: Github repository to resolve issues in form of `owner/repo`.
        token: Github token to access the repository.
        username: Github username to access the repository.
        max_iterations: Maximum number of iterations to run.
        limit_issues: Limit the number of issues to resolve.
        num_workers: Number of workers to use for parallel processing.
        output_dir: Output directory to write the results.
        llm_config: Configuration for the language model.
        runtime_container_image: Container image to use.
        prompt_template: Prompt template to use.
        issue_type: Type of issue to resolve (issue or pr).
        repo_instruction: Repository instruction to use.
        issue_numbers: List of issue numbers to resolve.
    """
    issue_handler = issue_handler_factory(issue_type, owner, repo, token, llm_config)

    # Load dataset
    issues: list[GithubIssue] = issue_handler.get_converted_issues(
        issue_numbers=issue_numbers
    )

    if limit_issues is not None:
        issues = issues[:limit_issues]
        logger.info(f'Limiting resolving to first {limit_issues} issues.')

    # TEST METADATA
    model_name = llm_config.model.split('/')[-1]

    pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)
    pathlib.Path(os.path.join(output_dir, 'infer_logs')).mkdir(
        parents=True, exist_ok=True
    )
    logger.info(f'Using output directory: {output_dir}')

    # checkout the repo
    repo_dir = os.path.join(output_dir, 'repo')
    if not os.path.exists(repo_dir):
        checkout_output = subprocess.check_output(
            [
                'git',
                'clone',
                f'https://{username}:{token}@github.com/{owner}/{repo}',
                f'{output_dir}/repo',
            ]
        ).decode('utf-8')
        if 'fatal' in checkout_output:
            raise RuntimeError(f'Failed to clone repository: {checkout_output}')

    # get the commit id of current repo for reproducibility
    base_commit = (
        subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo_dir)
        .decode('utf-8')
        .strip()
    )
    logger.info(f'Base commit: {base_commit}')

    if repo_instruction is None:
        # Check for .openhands_instructions file in the workspace directory
        openhands_instructions_path = os.path.join(repo_dir, '.openhands_instructions')
        if os.path.exists(openhands_instructions_path):
            with open(openhands_instructions_path, 'r') as f:
                repo_instruction = f.read()

    # OUTPUT FILE
    output_file = os.path.join(output_dir, 'output.jsonl')
    logger.info(f'Writing output to {output_file}')
    finished_numbers = set()
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            for line in f:
                data = ResolverOutput.model_validate_json(line)
                finished_numbers.add(data.issue.number)
        logger.warning(
            f'Output file {output_file} already exists. Loaded {len(finished_numbers)} finished issues.'
        )
    output_fp = open(output_file, 'a')

    logger.info(
        f'Resolving issues with model {model_name}, max iterations {max_iterations}.'
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
    logger.info(f'Using {num_workers} workers.')

    try:
        tasks = []
        for issue in issues:
            # checkout to pr branch
            if issue_type == 'pr':
                logger.info(
                    f'Checking out to PR branch {issue.head_branch} for issue {issue.number}'
                )

                subprocess.check_output(
                    ['git', 'checkout', f'{issue.head_branch}'],
                    cwd=repo_dir,
                )

                base_commit = (
                    subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo_dir)
                    .decode('utf-8')
                    .strip()
                )

            task = update_progress(
                process_issue(
                    issue,
                    base_commit,
                    max_iterations,
                    llm_config,
                    output_dir,
                    runtime_container_image,
                    prompt_template,
                    issue_handler,
                    repo_instruction,
                    bool(num_workers > 1),
                ),
                output_fp,
                pbar,
            )
            tasks.append(task)

        # Use asyncio.gather with a semaphore to limit concurrency
        sem = asyncio.Semaphore(num_workers)

        async def run_with_semaphore(task):
            async with sem:
                return await task

        await asyncio.gather(*[run_with_semaphore(task) for task in tasks])

    except KeyboardInterrupt:
        print('KeyboardInterrupt received. Cleaning up...')
        cleanup()

    output_fp.close()
    logger.info('Finished.')


def main():
    parser = argparse.ArgumentParser(description='Resolve multiple issues from Github.')
    parser.add_argument(
        '--repo',
        type=str,
        required=True,
        help='Github repository to resolve issues in form of `owner/repo`.',
    )
    parser.add_argument(
        '--token',
        type=str,
        default=None,
        help='Github token to access the repository.',
    )
    parser.add_argument(
        '--username',
        type=str,
        default=None,
        help='Github username to access the repository.',
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

    my_args = parser.parse_args()

    runtime_container_image = my_args.runtime_container_image
    if runtime_container_image is None:
        runtime_container_image = (
            f'ghcr.io/all-hands-ai/runtime:{openhands.__version__}-nikolaik'
        )

    owner, repo = my_args.repo.split('/')
    token = my_args.token if my_args.token else os.getenv('GITHUB_TOKEN')
    username = my_args.username if my_args.username else os.getenv('GITHUB_USERNAME')
    if not username:
        raise ValueError('Github username is required.')

    if not token:
        raise ValueError('Github token is required.')

    llm_config = LLMConfig(
        model=my_args.llm_model or os.environ['LLM_MODEL'],
        api_key=my_args.llm_api_key or os.environ['LLM_API_KEY'],
        base_url=my_args.llm_base_url or os.environ.get('LLM_BASE_URL', None),
    )

    repo_instruction = None
    if my_args.repo_instruction_file:
        with open(my_args.repo_instruction_file, 'r') as f:
            repo_instruction = f.read()

    issue_numbers = None
    if my_args.issue_numbers:
        issue_numbers = [int(number) for number in my_args.issue_numbers.split(',')]

    issue_type = my_args.issue_type

    # Read the prompt template
    prompt_file = my_args.prompt_file
    if prompt_file is None:
        if issue_type == 'issue':
            prompt_file = os.path.join(
                os.path.dirname(__file__), 'prompts/resolve/basic-with-tests.jinja'
            )
        else:
            prompt_file = os.path.join(
                os.path.dirname(__file__), 'prompts/resolve/basic-followup.jinja'
            )
    with open(prompt_file, 'r') as f:
        prompt_template = f.read()

    asyncio.run(
        resolve_issues(
            owner=owner,
            repo=repo,
            token=token,
            username=username,
            runtime_container_image=runtime_container_image,
            max_iterations=my_args.max_iterations,
            limit_issues=my_args.limit_issues,
            num_workers=my_args.num_workers,
            output_dir=my_args.output_dir,
            llm_config=llm_config,
            prompt_template=prompt_template,
            issue_type=issue_type,
            repo_instruction=repo_instruction,
            issue_numbers=issue_numbers,
        )
    )


if __name__ == '__main__':
    main()
