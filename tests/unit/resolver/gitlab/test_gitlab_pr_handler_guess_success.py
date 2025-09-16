import json
from unittest.mock import MagicMock, patch

import pytest

from openhands.core.config import LLMConfig
from openhands.events.action.message import MessageAction
from openhands.llm.llm import LLM
from openhands.resolver.interfaces.gitlab import GitlabPRHandler
from openhands.resolver.interfaces.issue import Issue, ReviewThread
from openhands.resolver.interfaces.issue_definitions import ServiceContextPR


@pytest.fixture
def pr_handler():
    llm_config = LLMConfig(model='test-model')
    handler = ServiceContextPR(
        GitlabPRHandler('test-owner', 'test-repo', 'test-token'), llm_config
    )
    return handler


@pytest.fixture
def mock_llm_success_response():
    return MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content="""--- success
true

--- explanation
The changes look good"""
                )
            )
        ]
    )


def test_guess_success_review_threads_litellm_call():
    """Test that the completion() call for review threads contains the expected content."""
    # Create a PR handler instance
    llm_config = LLMConfig(model='test', api_key='test')
    handler = ServiceContextPR(
        GitlabPRHandler('test-owner', 'test-repo', 'test-token'), llm_config
    )

    # Create a mock issue with review threads
    issue = Issue(
        owner='test-owner',
        repo='test-repo',
        number=1,
        title='Test PR',
        body='Test Body',
        thread_comments=None,
        closing_issues=['Issue 1 description', 'Issue 2 description'],
        review_comments=None,
        review_threads=[
            ReviewThread(
                comment='Please fix the formatting\n---\nlatest feedback:\nAdd docstrings',
                files=['/src/file1.py', '/src/file2.py'],
            ),
            ReviewThread(
                comment='Add more tests\n---\nlatest feedback:\nAdd test cases',
                files=['/tests/test_file.py'],
            ),
        ],
        thread_ids=['1', '2'],
        head_branch='test-branch',
    )

    # Create mock history with a detailed response
    history = [
        MessageAction(
            content="""I have made the following changes:
1. Fixed formatting in file1.py and file2.py
2. Added docstrings to all functions
3. Added test cases in test_file.py"""
        )
    ]

    # Create mock LLM config
    llm_config = LLMConfig(model='test-model', api_key='test-key')

    # Mock the LLM response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="""--- success
true

--- explanation
The changes successfully address the feedback."""
            )
        )
    ]

    # Test the guess_success method
    with patch.object(LLM, 'completion') as mock_completion:
        mock_completion.return_value = mock_response
        success, success_list, explanation = handler.guess_success(issue, history)

        # Verify the completion() calls
        assert mock_completion.call_count == 2  # One call per review thread

        # Check first call
        first_call = mock_completion.call_args_list[0]
        first_prompt = first_call[1]['messages'][0]['content']
        assert (
            'Issue descriptions:\n'
            + json.dumps(['Issue 1 description', 'Issue 2 description'], indent=4)
            in first_prompt
        )
        assert (
            'Feedback:\nPlease fix the formatting\n---\nlatest feedback:\nAdd docstrings'
            in first_prompt
        )
        assert (
            'Files locations:\n'
            + json.dumps(['/src/file1.py', '/src/file2.py'], indent=4)
            in first_prompt
        )
        assert 'Last message from AI agent:\n' + history[0].content in first_prompt

        # Check second call
        second_call = mock_completion.call_args_list[1]
        second_prompt = second_call[1]['messages'][0]['content']
        assert (
            'Issue descriptions:\n'
            + json.dumps(['Issue 1 description', 'Issue 2 description'], indent=4)
            in second_prompt
        )
        assert (
            'Feedback:\nAdd more tests\n---\nlatest feedback:\nAdd test cases'
            in second_prompt
        )
        assert (
            'Files locations:\n' + json.dumps(['/tests/test_file.py'], indent=4)
            in second_prompt
        )
        assert 'Last message from AI agent:\n' + history[0].content in second_prompt

        assert len(json.loads(explanation)) == 2


def test_guess_success_thread_comments_litellm_call():
    """Test that the completion() call for thread comments contains the expected content."""
    # Create a PR handler instance
    llm_config = LLMConfig(model='test', api_key='test')
    handler = ServiceContextPR(
        GitlabPRHandler('test-owner', 'test-repo', 'test-token'), llm_config
    )

    # Create a mock issue with thread comments
    issue = Issue(
        owner='test-owner',
        repo='test-repo',
        number=1,
        title='Test PR',
        body='Test Body',
        thread_comments=[
            'Please improve error handling',
            'Add input validation',
            'latest feedback:\nHandle edge cases',
        ],
        closing_issues=['Issue 1 description', 'Issue 2 description'],
        review_comments=None,
        thread_ids=None,
        head_branch='test-branch',
    )

    # Create mock history with a detailed response
    history = [
        MessageAction(
            content="""I have made the following changes:
1. Added try/catch blocks for error handling
2. Added input validation checks
3. Added handling for edge cases"""
        )
    ]

    # Create mock LLM config
    llm_config = LLMConfig(model='test-model', api_key='test-key')

    # Mock the LLM response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="""--- success
true

--- explanation
The changes successfully address the feedback."""
            )
        )
    ]

    # Test the guess_success method
    with patch.object(LLM, 'completion') as mock_completion:
        mock_completion.return_value = mock_response
        success, success_list, explanation = handler.guess_success(issue, history)

        # Verify the completion() call
        mock_completion.assert_called_once()
        call_args = mock_completion.call_args
        prompt = call_args[1]['messages'][0]['content']

        # Check prompt content
        assert (
            'Issue descriptions:\n'
            + json.dumps(['Issue 1 description', 'Issue 2 description'], indent=4)
            in prompt
        )
        assert 'PR Thread Comments:\n' + '\n---\n'.join(issue.thread_comments) in prompt
        assert 'Last message from AI agent:\n' + history[0].content in prompt

        assert len(json.loads(explanation)) == 1


def test_check_feedback_with_llm():
    """Test the _check_feedback_with_llm helper function."""
    # Create a PR handler instance
    llm_config = LLMConfig(model='test', api_key='test')
    handler = ServiceContextPR(
        GitlabPRHandler('test-owner', 'test-repo', 'test-token'), llm_config
    )

    # Test cases for different LLM responses
    test_cases = [
        {
            'response': '--- success\ntrue\n--- explanation\nChanges look good',
            'expected': (True, 'Changes look good'),
        },
        {
            'response': '--- success\nfalse\n--- explanation\nNot all issues fixed',
            'expected': (False, 'Not all issues fixed'),
        },
        {
            'response': 'Invalid response format',
            'expected': (
                False,
                'Failed to decode answer from LLM response: Invalid response format',
            ),
        },
        {
            'response': '--- success\ntrue\n--- explanation\nMultiline\nexplanation\nhere',
            'expected': (True, 'Multiline\nexplanation\nhere'),
        },
    ]

    for case in test_cases:
        # Mock the LLM response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=case['response']))]

        # Test the function
        with patch.object(LLM, 'completion', return_value=mock_response):
            success, explanation = handler._check_feedback_with_llm('test prompt')
            assert (success, explanation) == case['expected']


def test_check_review_thread_with_git_patch():
    """Test that git patch from complete_runtime is included in the prompt."""
    # Create a PR handler instance
    llm_config = LLMConfig(model='test', api_key='test')
    handler = ServiceContextPR(
        GitlabPRHandler('test-owner', 'test-repo', 'test-token'), llm_config
    )

    # Create test data
    review_thread = ReviewThread(
        comment='Please fix the formatting\n---\nlatest feedback:\nAdd docstrings',
        files=['/src/file1.py', '/src/file2.py'],
    )
    issues_context = json.dumps(
        ['Issue 1 description', 'Issue 2 description'], indent=4
    )
    last_message = 'I have fixed the formatting and added docstrings'
    git_patch = 'diff --git a/src/file1.py b/src/file1.py\n+"""Added docstring."""\n'

    # Mock the LLM response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="""--- success
true

--- explanation
Changes look good"""
            )
        )
    ]

    # Test the function
    with patch.object(LLM, 'completion') as mock_completion:
        mock_completion.return_value = mock_response
        success, explanation = handler._check_review_thread(
            review_thread, issues_context, last_message, git_patch
        )

        # Verify the completion() call
        mock_completion.assert_called_once()
        call_args = mock_completion.call_args
        prompt = call_args[1]['messages'][0]['content']

        # Check prompt content
        assert 'Issue descriptions:\n' + issues_context in prompt
        assert 'Feedback:\n' + review_thread.comment in prompt
        assert (
            'Files locations:\n' + json.dumps(review_thread.files, indent=4) in prompt
        )
        assert 'Last message from AI agent:\n' + last_message in prompt
        assert 'Changes made (git patch):\n' + git_patch in prompt

        # Check result
        assert success is True
        assert explanation == 'Changes look good'


def test_check_review_thread():
    """Test the _check_review_thread helper function."""
    # Create a PR handler instance
    llm_config = LLMConfig(model='test', api_key='test')
    handler = ServiceContextPR(
        GitlabPRHandler('test-owner', 'test-repo', 'test-token'), llm_config
    )

    # Create test data
    review_thread = ReviewThread(
        comment='Please fix the formatting\n---\nlatest feedback:\nAdd docstrings',
        files=['/src/file1.py', '/src/file2.py'],
    )
    issues_context = json.dumps(
        ['Issue 1 description', 'Issue 2 description'], indent=4
    )
    last_message = 'I have fixed the formatting and added docstrings'

    # Mock the LLM response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="""--- success
true

--- explanation
Changes look good"""
            )
        )
    ]

    # Test the function
    with patch.object(LLM, 'completion') as mock_completion:
        mock_completion.return_value = mock_response
        success, explanation = handler._check_review_thread(
            review_thread, issues_context, last_message
        )

        # Verify the completion() call
        mock_completion.assert_called_once()
        call_args = mock_completion.call_args
        prompt = call_args[1]['messages'][0]['content']

        # Check prompt content
        assert 'Issue descriptions:\n' + issues_context in prompt
        assert 'Feedback:\n' + review_thread.comment in prompt
        assert (
            'Files locations:\n' + json.dumps(review_thread.files, indent=4) in prompt
        )
        assert 'Last message from AI agent:\n' + last_message in prompt

        # Check result
        assert success is True
        assert explanation == 'Changes look good'


def test_check_thread_comments_with_git_patch():
    """Test that git patch from complete_runtime is included in the prompt."""
    # Create a PR handler instance
    llm_config = LLMConfig(model='test', api_key='test')
    handler = ServiceContextPR(
        GitlabPRHandler('test-owner', 'test-repo', 'test-token'), llm_config
    )

    # Create test data
    thread_comments = [
        'Please improve error handling',
        'Add input validation',
        'latest feedback:\nHandle edge cases',
    ]
    issues_context = json.dumps(
        ['Issue 1 description', 'Issue 2 description'], indent=4
    )
    last_message = 'I have added error handling and input validation'
    git_patch = 'diff --git a/src/file1.py b/src/file1.py\n+try:\n+    validate_input()\n+except ValueError:\n+    handle_error()\n'

    # Mock the LLM response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="""--- success
true

--- explanation
Changes look good"""
            )
        )
    ]

    # Test the function
    with patch.object(LLM, 'completion') as mock_completion:
        mock_completion.return_value = mock_response
        success, explanation = handler._check_thread_comments(
            thread_comments, issues_context, last_message, git_patch
        )

        # Verify the completion() call
        mock_completion.assert_called_once()
        call_args = mock_completion.call_args
        prompt = call_args[1]['messages'][0]['content']

        # Check prompt content
        assert 'Issue descriptions:\n' + issues_context in prompt
        assert 'PR Thread Comments:\n' + '\n---\n'.join(thread_comments) in prompt
        assert 'Last message from AI agent:\n' + last_message in prompt
        assert 'Changes made (git patch):\n' + git_patch in prompt

        # Check result
        assert success is True
        assert explanation == 'Changes look good'


def test_check_thread_comments():
    """Test the _check_thread_comments helper function."""
    # Create a PR handler instance
    llm_config = LLMConfig(model='test', api_key='test')
    handler = ServiceContextPR(
        GitlabPRHandler('test-owner', 'test-repo', 'test-token'), llm_config
    )

    # Create test data
    thread_comments = [
        'Please improve error handling',
        'Add input validation',
        'latest feedback:\nHandle edge cases',
    ]
    issues_context = json.dumps(
        ['Issue 1 description', 'Issue 2 description'], indent=4
    )
    last_message = 'I have added error handling and input validation'

    # Mock the LLM response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="""--- success
true

--- explanation
Changes look good"""
            )
        )
    ]

    # Test the function
    with patch.object(LLM, 'completion') as mock_completion:
        mock_completion.return_value = mock_response
        success, explanation = handler._check_thread_comments(
            thread_comments, issues_context, last_message
        )

        # Verify the completion() call
        mock_completion.assert_called_once()
        call_args = mock_completion.call_args
        prompt = call_args[1]['messages'][0]['content']

        # Check prompt content
        assert 'Issue descriptions:\n' + issues_context in prompt
        assert 'PR Thread Comments:\n' + '\n---\n'.join(thread_comments) in prompt
        assert 'Last message from AI agent:\n' + last_message in prompt

        # Check result
        assert success is True
        assert explanation == 'Changes look good'


def test_check_review_comments_with_git_patch():
    """Test that git patch from complete_runtime is included in the prompt."""
    # Create a PR handler instance
    llm_config = LLMConfig(model='test', api_key='test')
    handler = ServiceContextPR(
        GitlabPRHandler('test-owner', 'test-repo', 'test-token'), llm_config
    )

    # Create test data
    review_comments = [
        'Please fix the code style',
        'Add more test cases',
        'latest feedback:\nImprove documentation',
    ]
    issues_context = json.dumps(
        ['Issue 1 description', 'Issue 2 description'], indent=4
    )
    last_message = 'I have fixed the code style and added tests'
    git_patch = 'diff --git a/src/file1.py b/src/file1.py\n+"""This module does X."""\n+def func():\n+    """Do Y."""\n'

    # Mock the LLM response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="""--- success
true

--- explanation
Changes look good"""
            )
        )
    ]

    # Test the function
    with patch.object(LLM, 'completion') as mock_completion:
        mock_completion.return_value = mock_response
        success, explanation = handler._check_review_comments(
            review_comments, issues_context, last_message, git_patch
        )

        # Verify the completion() call
        mock_completion.assert_called_once()
        call_args = mock_completion.call_args
        prompt = call_args[1]['messages'][0]['content']

        # Check prompt content
        assert 'Issue descriptions:\n' + issues_context in prompt
        assert 'PR Review Comments:\n' + '\n---\n'.join(review_comments) in prompt
        assert 'Last message from AI agent:\n' + last_message in prompt
        assert 'Changes made (git patch):\n' + git_patch in prompt

        # Check result
        assert success is True
        assert explanation == 'Changes look good'


def test_check_review_comments():
    """Test the _check_review_comments helper function."""
    # Create a PR handler instance
    llm_config = LLMConfig(model='test', api_key='test')
    handler = ServiceContextPR(
        GitlabPRHandler('test-owner', 'test-repo', 'test-token'), llm_config
    )

    # Create test data
    review_comments = [
        'Please improve code readability',
        'Add comments to complex functions',
        'Follow PEP 8 style guide',
    ]
    issues_context = json.dumps(
        ['Issue 1 description', 'Issue 2 description'], indent=4
    )
    last_message = 'I have improved code readability and added comments'

    # Mock the LLM response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="""--- success
true

--- explanation
Changes look good"""
            )
        )
    ]

    # Test the function
    with patch.object(LLM, 'completion') as mock_completion:
        mock_completion.return_value = mock_response
        success, explanation = handler._check_review_comments(
            review_comments, issues_context, last_message
        )

        # Verify the completion() call
        mock_completion.assert_called_once()
        call_args = mock_completion.call_args
        prompt = call_args[1]['messages'][0]['content']

        # Check prompt content
        assert 'Issue descriptions:\n' + issues_context in prompt
        assert 'PR Review Comments:\n' + '\n---\n'.join(review_comments) in prompt
        assert 'Last message from AI agent:\n' + last_message in prompt

        # Check result
        assert success is True
        assert explanation == 'Changes look good'


def test_guess_success_review_comments_litellm_call():
    """Test that the completion() call for review comments contains the expected content."""
    # Create a PR handler instance
    llm_config = LLMConfig(model='test', api_key='test')
    handler = ServiceContextPR(
        GitlabPRHandler('test-owner', 'test-repo', 'test-token'), llm_config
    )

    # Create a mock issue with review comments
    issue = Issue(
        owner='test-owner',
        repo='test-repo',
        number=1,
        title='Test PR',
        body='Test Body',
        thread_comments=None,
        closing_issues=['Issue 1 description', 'Issue 2 description'],
        review_comments=[
            'Please improve code readability',
            'Add comments to complex functions',
            'Follow PEP 8 style guide',
        ],
        thread_ids=None,
        head_branch='test-branch',
    )

    # Create mock history with a detailed response
    history = [
        MessageAction(
            content="""I have made the following changes:
1. Improved code readability by breaking down complex functions
2. Added detailed comments to all complex functions
3. Fixed code style to follow PEP 8"""
        )
    ]

    # Mock the LLM response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="""--- success
true

--- explanation
The changes successfully address the feedback."""
            )
        )
    ]

    with patch.object(LLM, 'completion') as mock_completion:
        mock_completion.return_value = mock_response
        success, success_list, explanation = handler.guess_success(issue, history)

        # Verify the completion() call
        mock_completion.assert_called_once()
        call_args = mock_completion.call_args
        prompt = call_args[1]['messages'][0]['content']

        # Check prompt content
        assert (
            'Issue descriptions:\n'
            + json.dumps(['Issue 1 description', 'Issue 2 description'], indent=4)
            in prompt
        )
        assert 'PR Review Comments:\n' + '\n---\n'.join(issue.review_comments) in prompt
        assert 'Last message from AI agent:\n' + history[0].content in prompt

        assert len(json.loads(explanation)) == 1
