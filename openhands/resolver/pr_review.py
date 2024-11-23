"""PR review functionality for OpenHands."""

import json
import os
from typing import Any

import jinja2
import litellm

from openhands.core.config import LLMConfig
from openhands.events.event import Event
from openhands.resolver.github_issue import GithubIssue


def get_pr_review_instruction(
    issue: GithubIssue,
    prompt_template: str,
    repo_instruction: str | None = None,
) -> tuple[str, list[str]]:
    """Generate instruction for the PR review agent."""
    # Format thread comments if they exist
    thread_context = ''
    if issue.thread_comments:
        thread_context = '\n\nIssue Thread Comments:\n' + '\n---\n'.join(
            issue.thread_comments
        )

    # Format review comments if they exist
    review_comments = ''
    if issue.review_comments:
        review_comments = '\n\nReview Comments:\n' + '\n---\n'.join(
            issue.review_comments
        )

    # Format review threads if they exist
    review_threads = ''
    if issue.review_threads:
        thread_messages = []
        for thread in issue.review_threads:
            thread_messages.append(f'File: {", ".join(thread.files)}\n{thread.comment}')
        review_threads = '\n\nReview Threads:\n' + '\n---\n'.join(thread_messages)

    images = []
    images.extend(_extract_image_urls(issue.body))
    images.extend(_extract_image_urls(thread_context))
    images.extend(_extract_image_urls(review_comments))
    images.extend(_extract_image_urls(review_threads))

    template = jinja2.Template(prompt_template)
    return (
        template.render(
            body=issue.title + '\n\n' + issue.body + thread_context + review_comments + review_threads,
            repo_instruction=repo_instruction,
        ),
        images,
    )


def guess_pr_review_success(
    issue: GithubIssue, history: list[Event], llm_config: LLMConfig
) -> tuple[bool, None | list[bool], str]:
    """Guess if the PR review is successful based on the history and the issue description."""
    last_message = history[-1].message
    # Include thread comments in the prompt if they exist
    issue_context = issue.body
    if issue.thread_comments:
        issue_context += '\n\nIssue Thread Comments:\n' + '\n---\n'.join(
            issue.thread_comments
        )

    # Include review comments in the prompt if they exist
    if issue.review_comments:
        issue_context += '\n\nReview Comments:\n' + '\n---\n'.join(
            issue.review_comments
        )

    # Include review threads in the prompt if they exist
    if issue.review_threads:
        thread_messages = []
        for thread in issue.review_threads:
            thread_messages.append(f'File: {", ".join(thread.files)}\n{thread.comment}')
        issue_context += '\n\nReview Threads:\n' + '\n---\n'.join(thread_messages)

    with open(
        os.path.join(
            os.path.dirname(__file__),
            'prompts/guess_success/issue-success-check.jinja',
        ),
        'r',
    ) as f:
        template = jinja2.Template(f.read())
    prompt = template.render(issue_context=issue_context, last_message=last_message)

    response = litellm.completion(
        model=llm_config.model,
        messages=[{'role': 'user', 'content': prompt}],
        api_key=llm_config.api_key,
        base_url=llm_config.base_url,
    )

    answer = response.choices[0].message.content.strip()
    pattern = r'--- success\n*(true|false)\n*--- explanation*\n((?:.|\n)*)'
    match = re.search(pattern, answer)
    if match:
        return match.group(1).lower() == 'true', None, match.group(2)

    return False, None, f'Failed to decode answer from LLM response: {answer}'
