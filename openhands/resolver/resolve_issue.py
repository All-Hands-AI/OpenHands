# flake8: noqa: E501

import asyncio

from openhands.resolver.issue_resolver import IssueResolver


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

    issue_resolver = IssueResolver(my_args)
    asyncio.run(issue_resolver.resolve_issue())


if __name__ == '__main__':
    main()
