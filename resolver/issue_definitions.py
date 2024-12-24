import json
import os
import re
from abc import ABC, abstractmethod
from typing import Any, ClassVar

import jinja2
import requests

from openhands.core.config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.event import Event
from openhands.llm.llm import LLM
from openhands.resolver.github_issue import GithubIssue, ReviewThread


class IssueHandlerInterface(ABC):
    issue_type: ClassVar[str]
    llm: LLM

    @abstractmethod
    def get_converted_issues(
        self, issue_numbers: list[int] | None = None, comment_id: int | None = None
    ) -> list[GithubIssue]:
        """Download issues from GitHub."""
        pass

    @abstractmethod
    def get_instruction(
        self,
        issue: GithubIssue,
        prompt_template: str,
        repo_instruction: str | None = None,
    ) -> tuple[str, list[str]]:
        """Generate instruction and image urls for the agent."""
        pass

    @abstractmethod
    def guess_success(
        self, issue: GithubIssue, history: list[Event]
    ) -> tuple[bool, list[bool] | None, str]:
        """Guess if the issue has been resolved based on the agent's output."""
        pass


class IssueHandler(IssueHandlerInterface):
    issue_type: ClassVar[str] = 'issue'

    def __init__(self, owner: str, repo: str, token: str, llm_config: LLMConfig):
        self.download_url = 'https://api.github.com/repos/{}/{}/issues'
        self.owner = owner
        self.repo = repo
        self.token = token
        self.llm = LLM(llm_config)

    def _download_issues_from_github(self) -> list[Any]:
        url = self.download_url.format(self.owner, self.repo)
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
        }
        params: dict[str, int | str] = {'state': 'open', 'per_page': 100, 'page': 1}
        all_issues = []

        # Get issues, page by page
        while True:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            issues = response.json()

            # No more issues, break the loop
            if not issues:
                break

            # Sanity check - the response is a list of dictionaries
            if not isinstance(issues, list) or any(
                [not isinstance(issue, dict) for issue in issues]
            ):
                raise ValueError('Expected list of dictionaries from Github API.')

            # Add the issues to the final list
            all_issues.extend(issues)
            assert isinstance(params['page'], int)
            params['page'] += 1

        return all_issues

    def _extract_image_urls(self, issue_body: str) -> list[str]:
        # Regular expression to match Markdown image syntax ![alt text](image_url)
        image_pattern = r'!\[.*?\]\((https?://[^\s)]+)\)'
        return re.findall(image_pattern, issue_body)

    def _extract_issue_references(self, body: str) -> list[int]:
        # First, remove code blocks as they may contain false positives
        body = re.sub(r'```.*?```', '', body, flags=re.DOTALL)

        # Remove inline code
        body = re.sub(r'`[^`]*`', '', body)

        # Remove URLs that contain hash symbols
        body = re.sub(r'https?://[^\s)]*#\d+[^\s)]*', '', body)

        # Now extract issue numbers, making sure they're not part of other text
        # The pattern matches #number that:
        # 1. Is at the start of text or after whitespace/punctuation
        # 2. Is followed by whitespace, punctuation, or end of text
        # 3. Is not part of a URL
        pattern = r'(?:^|[\s\[({]|[^\w#])#(\d+)(?=[\s,.\])}]|$)'
        return [int(match) for match in re.findall(pattern, body)]

    def _get_issue_comments(
        self, issue_number: int, comment_id: int | None = None
    ) -> list[str] | None:
        """Retrieve comments for a specific issue from Github.

        Args:
            issue_number: The ID of the issue to get comments for
            comment_id: The ID of a single comment, if provided, otherwise all comments
        """
        url = f'https://api.github.com/repos/{self.owner}/{self.repo}/issues/{issue_number}/comments'
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
        }
        params = {'per_page': 100, 'page': 1}
        all_comments = []

        # Get comments, page by page
        while True:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            comments = response.json()

            if not comments:
                break

            # If a single comment ID is provided, return only that comment
            if comment_id:
                matching_comment = next(
                    (
                        comment['body']
                        for comment in comments
                        if comment['id'] == comment_id
                    ),
                    None,
                )
                if matching_comment:
                    return [matching_comment]
            else:
                # Otherwise, return all comments
                all_comments.extend([comment['body'] for comment in comments])

            params['page'] += 1

        return all_comments if all_comments else None

    def get_converted_issues(
        self, issue_numbers: list[int] | None = None, comment_id: int | None = None
    ) -> list[GithubIssue]:
        """Download issues from Github.

        Args:
            issue_numbers: The numbers of the issues to download
            comment_id: The ID of a single comment, if provided, otherwise all comments

        Returns:
            List of Github issues.
        """

        if not issue_numbers:
            raise ValueError('Unspecified issue number')

        all_issues = self._download_issues_from_github()
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
            # Check for required fields (number and title)
            if any([issue.get(key) is None for key in ['number', 'title']]):
                logger.warning(
                    f'Skipping issue {issue} as it is missing number or title.'
                )
                continue

            # Handle empty body by using empty string
            if issue.get('body') is None:
                issue['body'] = ''

            # Get issue thread comments
            thread_comments = self._get_issue_comments(
                issue['number'], comment_id=comment_id
            )
            # Convert empty lists to None for optional fields
            issue_details = GithubIssue(
                owner=self.owner,
                repo=self.repo,
                number=issue['number'],
                title=issue['title'],
                body=issue['body'],
                thread_comments=thread_comments,
                review_comments=None,  # Initialize review comments as None for regular issues
            )

            converted_issues.append(issue_details)

        return converted_issues

    def get_instruction(
        self,
        issue: GithubIssue,
        prompt_template: str,
        repo_instruction: str | None = None,
    ) -> tuple[str, list[str]]:
        """Generate instruction for the agent.

        Args:
            issue: The issue to generate instruction for
            prompt_template: The prompt template to use
            repo_instruction: The repository instruction if it exists
        """

        # Format thread comments if they exist
        thread_context = ''
        if issue.thread_comments:
            thread_context = '\n\nIssue Thread Comments:\n' + '\n---\n'.join(
                issue.thread_comments
            )

        # Extract image URLs from the issue body and thread comments
        images = []
        images.extend(self._extract_image_urls(issue.body))
        images.extend(self._extract_image_urls(thread_context))

        template = jinja2.Template(prompt_template)
        return (
            template.render(
                body=issue.title + '\n\n' + issue.body + thread_context,
                repo_instruction=repo_instruction,
            ),
            images,
        )

    def guess_success(
        self, issue: GithubIssue, history: list[Event]
    ) -> tuple[bool, None | list[bool], str]:
        """Guess if the issue is fixed based on the history and the issue description.

        Args:
            issue: The issue to check
            history: The agent's history
        """
        last_message = history[-1].message

        # Include thread comments in the prompt if they exist
        issue_context = issue.body
        if issue.thread_comments:
            issue_context += '\n\nIssue Thread Comments:\n' + '\n---\n'.join(
                issue.thread_comments
            )

        # Prepare the prompt
        with open(
            os.path.join(
                os.path.dirname(__file__),
                'prompts/guess_success/issue-success-check.jinja',
            ),
            'r',
        ) as f:
            template = jinja2.Template(f.read())
        prompt = template.render(issue_context=issue_context, last_message=last_message)

        # Get the LLM response and check for 'success' and 'explanation' in the answer
        response = self.llm.completion(messages=[{'role': 'user', 'content': prompt}])

        answer = response.choices[0].message.content.strip()
        pattern = r'--- success\n*(true|false)\n*--- explanation*\n((?:.|\n)*)'
        match = re.search(pattern, answer)
        if match:
            return match.group(1).lower() == 'true', None, match.group(2)

        return False, None, f'Failed to decode answer from LLM response: {answer}'


class PRHandler(IssueHandler):
    issue_type: ClassVar[str] = 'pr'

    def __init__(self, owner: str, repo: str, token: str, llm_config: LLMConfig):
        super().__init__(owner, repo, token, llm_config)
        self.download_url = 'https://api.github.com/repos/{}/{}/pulls'

    def __download_pr_metadata(
        self, pull_number: int, comment_id: int | None = None
    ) -> tuple[list[str], list[int], list[str], list[ReviewThread], list[str]]:
        """Run a GraphQL query against the GitHub API for information.

        Retrieves information about:
            1. unresolved review comments
            2. referenced issues the pull request would close

        Args:
            pull_number: The number of the pull request to query.
            comment_id: Optional ID of a specific comment to focus on.
            query: The GraphQL query as a string.
            variables: A dictionary of variables for the query.
            token: Your GitHub personal access token.

        Returns:
            The JSON response from the GitHub API.
        """
        # Using graphql as REST API doesn't indicate resolved status for review comments
        # TODO: grabbing the first 10 issues, 100 review threads, and 100 coments; add pagination to retrieve all
        query = """
                query($owner: String!, $repo: String!, $pr: Int!) {
                    repository(owner: $owner, name: $repo) {
                        pullRequest(number: $pr) {
                            closingIssuesReferences(first: 10) {
                                edges {
                                    node {
                                        body
                                        number
                                    }
                                }
                            }
                            url
                            reviews(first: 100) {
                                nodes {
                                    body
                                    state
                                    fullDatabaseId
                                }
                            }
                            reviewThreads(first: 100) {
                                edges{
                                    node{
                                        id
                                        isResolved
                                        comments(first: 100) {
                                            totalCount
                                            nodes {
                                                body
                                                path
                                                fullDatabaseId
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            """

        variables = {'owner': self.owner, 'repo': self.repo, 'pr': pull_number}

        # Run the query
        url = 'https://api.github.com/graphql'
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
        }

        response = requests.post(
            url, json={'query': query, 'variables': variables}, headers=headers
        )
        response.raise_for_status()
        response_json = response.json()

        # Parse the response to get closing issue references and unresolved review comments
        pr_data = (
            response_json.get('data', {}).get('repository', {}).get('pullRequest', {})
        )

        # Get closing issues
        closing_issues = pr_data.get('closingIssuesReferences', {}).get('edges', [])
        closing_issues_bodies = [issue['node']['body'] for issue in closing_issues]
        closing_issue_numbers = [
            issue['node']['number'] for issue in closing_issues
        ]  # Extract issue numbers

        # Get review comments
        reviews = pr_data.get('reviews', {}).get('nodes', [])
        if comment_id is not None:
            reviews = [
                review
                for review in reviews
                if int(review['fullDatabaseId']) == comment_id
            ]
        review_bodies = [review['body'] for review in reviews]

        # Get unresolved review threads
        review_threads = []
        thread_ids = []  # Store thread IDs; agent replies to the thread
        raw_review_threads = pr_data.get('reviewThreads', {}).get('edges', [])
        for thread in raw_review_threads:
            node = thread.get('node', {})
            if not node.get(
                'isResolved', True
            ):  # Check if the review thread is unresolved
                id = node.get('id')
                thread_contains_comment_id = False
                my_review_threads = node.get('comments', {}).get('nodes', [])
                message = ''
                files = []
                for i, review_thread in enumerate(my_review_threads):
                    if (
                        comment_id is not None
                        and int(review_thread['fullDatabaseId']) == comment_id
                    ):
                        thread_contains_comment_id = True

                    if (
                        i == len(my_review_threads) - 1
                    ):  # Check if it's the last thread in the thread
                        if len(my_review_threads) > 1:
                            message += '---\n'  # Add "---" before the last message if there's more than one thread
                        message += 'latest feedback:\n' + review_thread['body'] + '\n'
                    else:
                        message += (
                            review_thread['body'] + '\n'
                        )  # Add each thread in a new line

                    # Source files on which the comments were made
                    file = review_thread.get('path')
                    if file and file not in files:
                        files.append(file)

                # If the comment ID is not provided or the thread contains the comment ID, add the thread to the list
                if comment_id is None or thread_contains_comment_id:
                    unresolved_thread = ReviewThread(comment=message, files=files)
                    review_threads.append(unresolved_thread)
                    thread_ids.append(id)

        return (
            closing_issues_bodies,
            closing_issue_numbers,
            review_bodies,
            review_threads,
            thread_ids,
        )

    # Override processing of downloaded issues
    def _get_pr_comments(
        self, pr_number: int, comment_id: int | None = None
    ) -> list[str] | None:
        """Download comments for a specific pull request from Github."""
        url = f'https://api.github.com/repos/{self.owner}/{self.repo}/issues/{pr_number}/comments'
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
        }
        params = {'per_page': 100, 'page': 1}
        all_comments = []

        while True:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            comments = response.json()

            if not comments:
                break

            if comment_id is not None:
                matching_comment = next(
                    (
                        comment['body']
                        for comment in comments
                        if comment['id'] == comment_id
                    ),
                    None,
                )
                if matching_comment:
                    return [matching_comment]
            else:
                all_comments.extend([comment['body'] for comment in comments])

            params['page'] += 1

        return all_comments if all_comments else None

    def __get_context_from_external_issues_references(
        self,
        closing_issues: list[str],
        closing_issue_numbers: list[int],
        issue_body: str,
        review_comments: list[str],
        review_threads: list[ReviewThread],
        thread_comments: list[str] | None,
    ):
        new_issue_references = []

        if issue_body:
            new_issue_references.extend(self._extract_issue_references(issue_body))

        if review_comments:
            for comment in review_comments:
                new_issue_references.extend(self._extract_issue_references(comment))

        if review_threads:
            for review_thread in review_threads:
                new_issue_references.extend(
                    self._extract_issue_references(review_thread.comment)
                )

        if thread_comments:
            for thread_comment in thread_comments:
                new_issue_references.extend(
                    self._extract_issue_references(thread_comment)
                )

        non_duplicate_references = set(new_issue_references)
        unique_issue_references = non_duplicate_references.difference(
            closing_issue_numbers
        )

        for issue_number in unique_issue_references:
            try:
                url = f'https://api.github.com/repos/{self.owner}/{self.repo}/issues/{issue_number}'
                headers = {
                    'Authorization': f'Bearer {self.token}',
                    'Accept': 'application/vnd.github.v3+json',
                }
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                issue_data = response.json()
                issue_body = issue_data.get('body', '')
                if issue_body:
                    closing_issues.append(issue_body)
            except requests.exceptions.RequestException as e:
                logger.warning(f'Failed to fetch issue {issue_number}: {str(e)}')

        return closing_issues

    def get_converted_issues(
        self, issue_numbers: list[int] | None = None, comment_id: int | None = None
    ) -> list[GithubIssue]:
        if not issue_numbers:
            raise ValueError('Unspecified issue numbers')

        all_issues = self._download_issues_from_github()
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

            issue_details = GithubIssue(
                owner=self.owner,
                repo=self.repo,
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
        issue: GithubIssue,
        prompt_template: str,
        repo_instruction: str | None = None,
    ) -> tuple[str, list[str]]:
        """Generate instruction for the agent."""
        template = jinja2.Template(prompt_template)
        images = []

        issues_str = None
        if issue.closing_issues:
            issues_str = json.dumps(issue.closing_issues, indent=4)
            images.extend(self._extract_image_urls(issues_str))

        # Handle PRs with review comments
        review_comments_str = None
        if issue.review_comments:
            review_comments_str = json.dumps(issue.review_comments, indent=4)
            images.extend(self._extract_image_urls(review_comments_str))

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
            images.extend(self._extract_image_urls(review_thread_str))

        # Format thread comments if they exist
        thread_context = ''
        if issue.thread_comments:
            thread_context = '\n---\n'.join(issue.thread_comments)
            images.extend(self._extract_image_urls(thread_context))

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
        self,
        thread_comments: list[str],
        issues_context: str,
        last_message: str,
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
        self,
        review_comments: list[str],
        issues_context: str,
        last_message: str,
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

    def guess_success(
        self, issue: GithubIssue, history: list[Event]
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
