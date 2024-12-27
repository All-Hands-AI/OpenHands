import json
import os
import re
from typing import Any, ClassVar

import jinja2

from openhands.core.config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.event import Event
from openhands.llm.llm import LLM
from openhands.resolver.issue import Issue, ReviewThread
from openhands.resolver.utils import extract_image_urls


# Strategy context interface
class ServiceContextPR:
    issue_type: ClassVar[str] = 'pr'

    def __init__(self, strategy, llm_config: LLMConfig):
        self._strategy = strategy
        self.llm = LLM(llm_config)

    def set_strategy(self, strategy):
        self._strategy = strategy

    def get_clone_url(self):
        return self._strategy.get_clone_url()

    def download_issues(self) -> list[Any]:
        return self._strategy.download_issues()

    def guess_success(
        self, issue: Issue, history: list[Event]
    ) -> tuple[bool, None | list[bool], str]:
        """Guess if the issue is fixed based on the history and the issue description."""
        last_message = history[-1].message
        issues_context = json.dumps(issue.closing_issues, indent=4)
        success_list = []
        explanation_list = []

        # Handle PRs with file-specific review comments
        if issue.review_threads:
            for review_thread in issue.review_threads:
                if issues_context and last_message:
                    success, explanation = self._check_review_thread(
                        review_thread, issues_context, last_message
                    )
                else:
                    success, explanation = False, 'Missing context or message'
                success_list.append(success)
                explanation_list.append(explanation)
        # Handle PRs with only thread comments (no file-specific review comments)
        elif issue.thread_comments:
            if issue.thread_comments and issues_context and last_message:
                success, explanation = self._check_thread_comments(
                    issue.thread_comments, issues_context, last_message
                )
            else:
                success, explanation = (
                    False,
                    'Missing thread comments, context or message',
                )
            success_list.append(success)
            explanation_list.append(explanation)
        elif issue.review_comments:
            # Handle PRs with only review comments (no file-specific review comments or thread comments)
            if issue.review_comments and issues_context and last_message:
                success, explanation = self._check_review_comments(
                    issue.review_comments, issues_context, last_message
                )
            else:
                success, explanation = (
                    False,
                    'Missing review comments, context or message',
                )
            success_list.append(success)
            explanation_list.append(explanation)
        else:
            # No review comments, thread comments, or file-level review comments found
            return False, None, 'No feedback was found to process'

        # Return overall success (all must be true) and explanations
        if not success_list:
            return False, None, 'No feedback was processed'
        return all(success_list), success_list, json.dumps(explanation_list)

    def get_converted_issues(
        self, issue_numbers: list[int] | None = None, comment_id: int | None = None
    ) -> list[Issue]:
        if not issue_numbers:
            raise ValueError('Unspecified issue numbers')

        all_issues = self.download_issues()
        logger.info(f'Limiting resolving to issues {issue_numbers}.')
        all_issues = [issue for issue in all_issues if issue['number'] in issue_numbers]

        converted_issues = []
        for issue in all_issues:
            # For PRs, body can be None
            if any([issue.get(key) is None for key in ['number', 'title']]):
                logger.warning(f'Skipping #{issue} as it is missing number or title.')
                continue

            # Handle None body for PRs
            body = issue.get('body') if issue.get('body') is not None else ''
            (
                closing_issues,
                closing_issues_numbers,
                review_comments,
                review_threads,
                thread_ids,
            ) = self.__download_pr_metadata(issue['number'], comment_id=comment_id)
            head_branch = issue['head']['ref']

            # Get PR thread comments
            thread_comments = self._get_pr_comments(
                issue['number'], comment_id=comment_id
            )

            closing_issues = self.__get_context_from_external_issues_references(
                closing_issues,
                closing_issues_numbers,
                body,
                review_comments,
                review_threads,
                thread_comments,
            )

            issue_details = Issue(
                owner=self._strategy.owner,
                repo=self._strategy.repo,
                number=issue['number'],
                title=issue['title'],
                body=body,
                closing_issues=closing_issues,
                review_comments=review_comments,
                review_threads=review_threads,
                thread_ids=thread_ids,
                head_branch=head_branch,
                thread_comments=thread_comments,
            )

            converted_issues.append(issue_details)

        return converted_issues

    def get_instruction(
        self,
        issue: Issue,
        prompt_template: str,
        repo_instruction: str | None = None,
    ) -> tuple[str, list[str]]:
        """Generate instruction for the agent."""
        template = jinja2.Template(prompt_template)
        images = []

        issues_str = None
        if issue.closing_issues:
            issues_str = json.dumps(issue.closing_issues, indent=4)
            images.extend(extract_image_urls(issues_str))

        # Handle PRs with review comments
        review_comments_str = None
        if issue.review_comments:
            review_comments_str = json.dumps(issue.review_comments, indent=4)
            images.extend(extract_image_urls(review_comments_str))

        # Handle PRs with file-specific review comments
        review_thread_str = None
        review_thread_file_str = None
        if issue.review_threads:
            review_threads = [
                review_thread.comment for review_thread in issue.review_threads
            ]
            review_thread_files = []
            for review_thread in issue.review_threads:
                review_thread_files.extend(review_thread.files)
            review_thread_str = json.dumps(review_threads, indent=4)
            review_thread_file_str = json.dumps(review_thread_files, indent=4)
            images.extend(extract_image_urls(review_thread_str))

        # Format thread comments if they exist
        thread_context = ''
        if issue.thread_comments:
            thread_context = '\n---\n'.join(issue.thread_comments)
            images.extend(extract_image_urls(thread_context))

        instruction = template.render(
            issues=issues_str,
            review_comments=review_comments_str,
            review_threads=review_thread_str,
            files=review_thread_file_str,
            thread_context=thread_context,
            repo_instruction=repo_instruction,
        )
        return instruction, images

    def _check_feedback_with_llm(self, prompt: str) -> tuple[bool, str]:
        """Helper function to check feedback with LLM and parse response."""
        response = self.llm.completion(messages=[{'role': 'user', 'content': prompt}])

        answer = response.choices[0].message.content.strip()
        pattern = r'--- success\n*(true|false)\n*--- explanation*\n((?:.|\n)*)'
        match = re.search(pattern, answer)
        if match:
            return match.group(1).lower() == 'true', match.group(2).strip()
        return False, f'Failed to decode answer from LLM response: {answer}'

    def _check_review_thread(
        self,
        review_thread: ReviewThread,
        issues_context: str,
        last_message: str,
    ) -> tuple[bool, str]:
        """Check if a review thread's feedback has been addressed."""
        files_context = json.dumps(review_thread.files, indent=4)

        with open(
            os.path.join(
                os.path.dirname(__file__),
                'prompts/guess_success/pr-feedback-check.jinja',
            ),
            'r',
        ) as f:
            template = jinja2.Template(f.read())

        prompt = template.render(
            issue_context=issues_context,
            feedback=review_thread.comment,
            files_context=files_context,
            last_message=last_message,
        )

        return self._check_feedback_with_llm(prompt)

    def _check_thread_comments(
        self, thread_comments: list[str], issues_context: str, last_message: str
    ) -> tuple[bool, str]:
        """Check if thread comments feedback has been addressed."""
        thread_context = '\n---\n'.join(thread_comments)

        with open(
            os.path.join(
                os.path.dirname(__file__), 'prompts/guess_success/pr-thread-check.jinja'
            ),
            'r',
        ) as f:
            template = jinja2.Template(f.read())

        prompt = template.render(
            issue_context=issues_context,
            thread_context=thread_context,
            last_message=last_message,
        )

        return self._check_feedback_with_llm(prompt)

    def _check_review_comments(
        self, review_comments: list[str], issues_context: str, last_message: str
    ) -> tuple[bool, str]:
        """Check if review comments feedback has been addressed."""
        review_context = '\n---\n'.join(review_comments)

        with open(
            os.path.join(
                os.path.dirname(__file__), 'prompts/guess_success/pr-review-check.jinja'
            ),
            'r',
        ) as f:
            template = jinja2.Template(f.read())

        prompt = template.render(
            issue_context=issues_context,
            review_context=review_context,
            last_message=last_message,
        )

        return self._check_feedback_with_llm(prompt)

    def __download_pr_metadata(
        self, pull_number: int, comment_id: int | None = None
    ) -> tuple[list[str], list[int], list[str], list[ReviewThread], list[str]]:
        return self._strategy.download_pr_metadata(pull_number, comment_id)

    def _get_pr_comments(
        self, pr_number: int, comment_id: int | None = None
    ) -> list[str] | None:
        return self._strategy.get_pr_comments(pr_number, comment_id)

    def __get_context_from_external_issues_references(
        self,
        closing_issues: list[str],
        closing_issue_numbers: list[int],
        issue_body: str,
        review_comments: list[str],
        review_threads: list[ReviewThread],
        thread_comments: list[str] | None,
    ):
        return self._strategy.get_context_from_external_issues_references(
            closing_issues,
            closing_issue_numbers,
            issue_body,
            review_comments,
            review_threads,
            thread_comments,
        )


class ServiceContext:
    issue_type: ClassVar[str] = 'issue'

    def __init__(self, strategy, llm_config: LLMConfig):
        self._strategy = strategy
        self.llm = LLM(llm_config)

    def set_strategy(self, strategy):
        self._strategy = strategy

    def get_base_url(self):
        return self._strategy.get_base_url()

    def get_download_url(self):
        return self._strategy.get_download_url()

    def get_clone_url(self):
        return self._strategy.get_clone_url()

    def get_headers(self):
        return self._strategy.get_headers()

    def get_compare_url(self, branch_name):
        return self._strategy.get_compare_url(branch_name)

    def download_issues(self) -> list[Any]:
        return self._strategy.download_issues()

    def get_branch_name(
        self,
        base_branch_name: str,
        headers: dict,
    ):
        return self._strategy.get_branch_name(base_branch_name, headers)

    def branch_exists(self, branch_name: str, headers: dict):
        return self._strategy.branch_exists(branch_name, headers)

    def get_issue_comments(
        self, issue_number: int, comment_id: int | None = None
    ) -> list[str] | None:
        return self._strategy.get_issue_comments(issue_number, comment_id)

    def get_instruction(
        self,
        issue: Issue,
        prompt_template: str,
        repo_instruction: str | None = None,
    ) -> tuple[str, list[str]]:
        """Generate instruction for the agent."""
        # Format thread comments if they exist
        thread_context = ''
        if issue.thread_comments:
            thread_context = '\n\nIssue Thread Comments:\n' + '\n---\n'.join(
                issue.thread_comments
            )

        images = []
        images.extend(extract_image_urls(issue.body))
        images.extend(extract_image_urls(thread_context))

        template = jinja2.Template(prompt_template)
        return (
            template.render(
                body=issue.title + '\n\n' + issue.body + thread_context,
                repo_instruction=repo_instruction,
            ),
            images,
        )

    def guess_success(
        self, issue: Issue, history: list[Event]
    ) -> tuple[bool, None | list[bool], str]:
        """Guess if the issue is fixed based on the history and the issue description."""
        last_message = history[-1].message
        # Include thread comments in the prompt if they exist
        issue_context = issue.body
        if issue.thread_comments:
            issue_context += '\n\nIssue Thread Comments:\n' + '\n---\n'.join(
                issue.thread_comments
            )

        with open(
            os.path.join(
                os.path.dirname(__file__),
                'prompts/guess_success/issue-success-check.jinja',
            ),
            'r',
        ) as f:
            template = jinja2.Template(f.read())
        prompt = template.render(issue_context=issue_context, last_message=last_message)

        response = self.llm.completion(messages=[{'role': 'user', 'content': prompt}])

        answer = response.choices[0].message.content.strip()
        pattern = r'--- success\n*(true|false)\n*--- explanation*\n((?:.|\n)*)'
        match = re.search(pattern, answer)
        if match:
            return match.group(1).lower() == 'true', None, match.group(2)

        return False, None, f'Failed to decode answer from LLM response: {answer}'

    def get_converted_issues(
        self, issue_numbers: list[int] | None = None, comment_id: int | None = None
    ) -> list[Issue]:
        """Download issues

        Returns:
            List issues.
        """

        if not issue_numbers:
            raise ValueError('Unspecified issue number')

        all_issues = self.download_issues()
        logger.info(f'Limiting resolving to issues {issue_numbers}.')
        all_issues = [
            issue
            for issue in all_issues
            if issue['number'] in issue_numbers and 'pull_request' not in issue
        ]

        if len(issue_numbers) == 1 and not all_issues:
            raise ValueError(f'Issue {issue_numbers[0]} not found')

        converted_issues = []
        for issue in all_issues:
            if any([issue.get(key) is None for key in ['number', 'title']]):
                logger.warning(
                    f'Skipping issue {issue} as it is missing number or title.'
                )
                continue

            # Handle empty body by using empty string
            if issue.get('body') is None:
                issue['body'] = ''

            # Get issue thread comments
            thread_comments = self.get_issue_comments(
                issue['number'], comment_id=comment_id
            )
            # Convert empty lists to None for optional fields
            issue_details = Issue(
                owner=self._strategy.owner,
                repo=self._strategy.repo,
                number=issue['number'],
                title=issue['title'],
                body=issue['body'],
                thread_comments=thread_comments,
                review_comments=None,  # Initialize review comments as None for regular issues
            )

            converted_issues.append(issue_details)

        return converted_issues
