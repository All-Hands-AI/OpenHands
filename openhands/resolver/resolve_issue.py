# flake8: noqa: E501

import asyncio
import os
from argparse import Namespace

from pydantic import SecretStr

import openhands
from openhands.core.config import LLMConfig, SandboxConfig
from openhands.integrations.service_types import ProviderType
from openhands.resolver.issue_handler_factory import IssueHandlerFactory
from openhands.resolver.issue_resolver import IssueResolver
from openhands.resolver.utils import (
    get_unique_uid,
    identify_token,
)
from openhands.utils.async_utils import GENERAL_TIMEOUT, call_async_from_sync


def setup_sandbox_config(
    base_container_image: str | None,
    runtime_container_image: str | None,
    is_experimental: bool,
) -> SandboxConfig:
    if runtime_container_image is not None and base_container_image is not None:
        raise ValueError('Cannot provide both runtime and base container images.')

    if (
        runtime_container_image is None
        and base_container_image is None
        and not is_experimental
    ):
        runtime_container_image = (
            f'ghcr.io/all-hands-ai/runtime:{openhands.__version__}-nikolaik'
        )

    # Convert container image values to string or None
    container_base = (
        str(base_container_image) if base_container_image is not None else None
    )
    container_runtime = (
        str(runtime_container_image) if runtime_container_image is not None else None
    )

    sandbox_config = SandboxConfig(
        base_container_image=container_base,
        runtime_container_image=container_runtime,
        enable_auto_lint=False,
        use_host_network=False,
        timeout=300,
    )

    # Configure sandbox for GitLab CI environment
    if os.getenv('GITLAB_CI') == 'true':
        sandbox_config.local_runtime_url = os.getenv(
            'LOCAL_RUNTIME_URL', 'http://localhost'
        )
        user_id = os.getuid() if hasattr(os, 'getuid') else 1000
        if user_id == 0:
            sandbox_config.user_id = get_unique_uid()

    return sandbox_config


def build_from_args(args: Namespace) -> IssueResolver:
    parts = args.selected_repo.rsplit('/', 1)
    if len(parts) < 2:
        raise ValueError('Invalid repository format. Expected owner/repo')
    owner, repo = parts

    token = args.token or os.getenv('GITHUB_TOKEN') or os.getenv('GITLAB_TOKEN')
    username = args.username if args.username else os.getenv('GIT_USERNAME')
    if not username:
        raise ValueError('Username is required.')

    if not token:
        raise ValueError('Token is required.')

    platform = call_async_from_sync(
        identify_token,
        GENERAL_TIMEOUT,
        token,
        args.base_domain,
    )

    api_key = args.llm_api_key or os.environ['LLM_API_KEY']
    model = args.llm_model or os.environ['LLM_MODEL']
    base_url = args.llm_base_url or os.environ.get('LLM_BASE_URL', None)
    api_version = os.environ.get('LLM_API_VERSION', None)
    llm_num_retries = int(os.environ.get('LLM_NUM_RETRIES', '4'))
    llm_retry_min_wait = int(os.environ.get('LLM_RETRY_MIN_WAIT', '5'))
    llm_retry_max_wait = int(os.environ.get('LLM_RETRY_MAX_WAIT', '30'))
    llm_retry_multiplier = int(os.environ.get('LLM_RETRY_MULTIPLIER', 2))
    llm_timeout = int(os.environ.get('LLM_TIMEOUT', 0))

    # Create LLMConfig instance
    llm_config = LLMConfig(
        model=model,
        api_key=SecretStr(api_key) if api_key else None,
        base_url=base_url,
        num_retries=llm_num_retries,
        retry_min_wait=llm_retry_min_wait,
        retry_max_wait=llm_retry_max_wait,
        retry_multiplier=llm_retry_multiplier,
        timeout=llm_timeout,
    )

    # Only set api_version if it was explicitly provided, otherwise let LLMConfig handle it
    if api_version is not None:
        llm_config.api_version = api_version

    repo_instruction = None
    if args.repo_instruction_file:
        with open(args.repo_instruction_file, 'r') as f:
            repo_instruction = f.read()

    issue_type = args.issue_type

    # Read the prompt template
    prompt_file = args.prompt_file
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

    base_domain = args.base_domain
    if base_domain is None:
        base_domain = 'github.com' if platform == ProviderType.GITHUB else 'gitlab.com'

    factory = IssueHandlerFactory(
        owner=owner,
        repo=repo,
        token=token,
        username=username,
        platform=platform,
        base_domain=base_domain,
        issue_type=issue_type,
        llm_config=llm_config,
    )
    issue_handler = factory.create()

    # Setup and validate container images
    sandbox_config = setup_sandbox_config(
        args.base_container_image,
        args.runtime_container_image,
        args.is_experimental,
    )

    return IssueResolver(
        owner=owner,
        repo=repo,
        platform=platform,
        max_iterations=args.max_iterations,
        output_dir=args.output_dir,
        llm_config=llm_config,
        prompt_template=prompt_template,
        issue_type=issue_type,
        repo_instruction=repo_instruction,
        issue_number=args.issue_number,
        comment_id=args.comment_id,
        sandbox_config=sandbox_config,
        issue_handler=issue_handler,
    )


def main() -> None:
    import argparse

    def int_or_none(value: str) -> int | None:
        if value.lower() == 'none':
            return None
        else:
            return int(value)

    parser = argparse.ArgumentParser(description='Resolve a single issue.')
    parser.add_argument(
        '--selected-repo',
        type=str,
        required=True,
        help='repository to resolve issues in form of `owner/repo`.',
    )
    parser.add_argument(
        '--token',
        type=str,
        default=None,
        help='token to access the repository.',
    )
    parser.add_argument(
        '--username',
        type=str,
        default=None,
        help='username to access the repository.',
    )
    parser.add_argument(
        '--base-container-image',
        type=str,
        default=None,
        help='base container image to use.',
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
        '--issue-number',
        type=int,
        required=True,
        help='Issue number to resolve.',
    )
    parser.add_argument(
        '--comment-id',
        type=int_or_none,
        required=False,
        default=None,
        help='Resolve a specific comment',
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
        '--is-experimental',
        type=lambda x: x.lower() == 'true',
        help='Whether to run in experimental mode.',
    )
    parser.add_argument(
        '--base-domain',
        type=str,
        default=None,
        help='Base domain for the git server (defaults to "github.com" for GitHub and "gitlab.com" for GitLab)',
    )

    my_args = parser.parse_args()

    issue_resolver = build_from_args(my_args)
    asyncio.run(issue_resolver.resolve_issue())


if __name__ == '__main__':
    main()
