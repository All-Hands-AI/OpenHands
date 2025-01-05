import os
import tempfile
from unittest.mock import MagicMock, call, patch

import pytest

from openhands.core.config import LLMConfig
from openhands.resolver.github_issue import ReviewThread
from openhands.resolver.resolver_output import GithubIssue, ResolverOutput
from openhands.resolver.send_pull_request import (
    apply_patch,
    initialize_repo,
    load_single_resolver_output,
    make_commit,
    process_all_successful_issues,
    process_single_issue,
    reply_to_comment,
    send_pull_request,
    update_existing_pull_request,
)


@pytest.fixture
def mock_output_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = os.path.join(temp_dir, 'repo')
        # Initialize a GitHub repo in "repo" and add a commit with "README.md"
        os.makedirs(repo_path)
        os.system(f'git init {repo_path}')
        readme_path = os.path.join(repo_path, 'README.md')
        with open(readme_path, 'w') as f:
            f.write('hello world')
        os.system(f'git -C {repo_path} add README.md')
        os.system(f"git -C {repo_path} commit -m 'Initial commit'")
        yield temp_dir


@pytest.fixture
def mock_github_issue():
    return GithubIssue(
        number=42,
        title='Test Issue',
        owner='test-owner',
        repo='test-repo',
        body='Test body',
    )


@pytest.fixture
def mock_llm_config():
    return LLMConfig()


def test_load_single_resolver_output():
    mock_output_jsonl = 'tests/unit/resolver/mock_output/output.jsonl'

    # Test loading an existing issue
    resolver_output = load_single_resolver_output(mock_output_jsonl, 5)
    assert isinstance(resolver_output, ResolverOutput)
    assert resolver_output.issue.number == 5
    assert resolver_output.issue.title == 'Add MIT license'
    assert resolver_output.issue.owner == 'neubig'
    assert resolver_output.issue.repo == 'pr-viewer'

    # Test loading a non-existent issue
    with pytest.raises(ValueError):
        load_single_resolver_output(mock_output_jsonl, 999)


def test_apply_patch(mock_output_dir):
    # Create a sample file in the mock repo
    sample_file = os.path.join(mock_output_dir, 'sample.txt')
    with open(sample_file, 'w') as f:
        f.write('Original content')

    # Create a sample patch
    patch_content = """
diff --git a/sample.txt b/sample.txt
index 9daeafb..b02def2 100644
--- a/sample.txt
+++ b/sample.txt
@@ -1 +1,2 @@
-Original content
+Updated content
+New line
"""

    # Apply the patch
    apply_patch(mock_output_dir, patch_content)

    # Check if the file was updated correctly
    with open(sample_file, 'r') as f:
        updated_content = f.read()

    assert updated_content.strip() == 'Updated content\nNew line'.strip()


def test_apply_patch_preserves_line_endings(mock_output_dir):
    # Create sample files with different line endings
    unix_file = os.path.join(mock_output_dir, 'unix_style.txt')
    dos_file = os.path.join(mock_output_dir, 'dos_style.txt')

    with open(unix_file, 'w', newline='\n') as f:
        f.write('Line 1\nLine 2\nLine 3')

    with open(dos_file, 'w', newline='\r\n') as f:
        f.write('Line 1\r\nLine 2\r\nLine 3')

    # Create patches for both files
    unix_patch = """
diff --git a/unix_style.txt b/unix_style.txt
index 9daeafb..b02def2 100644
--- a/unix_style.txt
+++ b/unix_style.txt
@@ -1,3 +1,3 @@
 Line 1
-Line 2
+Updated Line 2
 Line 3
"""

    dos_patch = """
diff --git a/dos_style.txt b/dos_style.txt
index 9daeafb..b02def2 100644
--- a/dos_style.txt
+++ b/dos_style.txt
@@ -1,3 +1,3 @@
 Line 1
-Line 2
+Updated Line 2
 Line 3
"""

    # Apply patches
    apply_patch(mock_output_dir, unix_patch)
    apply_patch(mock_output_dir, dos_patch)

    # Check if line endings are preserved
    with open(unix_file, 'rb') as f:
        unix_content = f.read()
    with open(dos_file, 'rb') as f:
        dos_content = f.read()

    assert (
        b'\r\n' not in unix_content
    ), 'Unix-style line endings were changed to DOS-style'
    assert b'\r\n' in dos_content, 'DOS-style line endings were changed to Unix-style'

    # Check if content was updated correctly
    assert unix_content.decode('utf-8').split('\n')[1] == 'Updated Line 2'
    assert dos_content.decode('utf-8').split('\r\n')[1] == 'Updated Line 2'


def test_apply_patch_create_new_file(mock_output_dir):
    # Create a patch that adds a new file
    patch_content = """
diff --git a/new_file.txt b/new_file.txt
new file mode 100644
index 0000000..3b18e51
--- /dev/null
+++ b/new_file.txt
@@ -0,0 +1 @@
+hello world
"""

    # Apply the patch
    apply_patch(mock_output_dir, patch_content)

    # Check if the new file was created
    new_file_path = os.path.join(mock_output_dir, 'new_file.txt')
    assert os.path.exists(new_file_path), 'New file was not created'

    # Check if the file content is correct
    with open(new_file_path, 'r') as f:
        content = f.read().strip()
    assert content == 'hello world', 'File content is incorrect'


def test_apply_patch_rename_file(mock_output_dir):
    # Create a sample file in the mock repo
    old_file = os.path.join(mock_output_dir, 'old_name.txt')
    with open(old_file, 'w') as f:
        f.write('This file will be renamed')

    # Create a patch that renames the file
    patch_content = """diff --git a/old_name.txt b/new_name.txt
similarity index 100%
rename from old_name.txt
rename to new_name.txt"""

    # Apply the patch
    apply_patch(mock_output_dir, patch_content)

    # Check if the file was renamed
    new_file = os.path.join(mock_output_dir, 'new_name.txt')
    assert not os.path.exists(old_file), 'Old file still exists'
    assert os.path.exists(new_file), 'New file was not created'

    # Check if the content is preserved
    with open(new_file, 'r') as f:
        content = f.read()
    assert content == 'This file will be renamed'


def test_apply_patch_delete_file(mock_output_dir):
    # Create a sample file in the mock repo
    sample_file = os.path.join(mock_output_dir, 'to_be_deleted.txt')
    with open(sample_file, 'w') as f:
        f.write('This file will be deleted')

    # Create a patch that deletes the file
    patch_content = """
diff --git a/to_be_deleted.txt b/to_be_deleted.txt
deleted file mode 100644
index 9daeafb..0000000
--- a/to_be_deleted.txt
+++ /dev/null
@@ -1 +0,0 @@
-This file will be deleted
"""

    # Apply the patch
    apply_patch(mock_output_dir, patch_content)

    # Check if the file was deleted
    assert not os.path.exists(sample_file), 'File was not deleted'


def test_initialize_repo(mock_output_dir):
    issue_type = 'issue'
    # Copy the repo to patches
    ISSUE_NUMBER = 3
    initialize_repo(mock_output_dir, ISSUE_NUMBER, issue_type)
    patches_dir = os.path.join(mock_output_dir, 'patches', f'issue_{ISSUE_NUMBER}')

    # Check if files were copied correctly
    assert os.path.exists(os.path.join(patches_dir, 'README.md'))

    # Check file contents
    with open(os.path.join(patches_dir, 'README.md'), 'r') as f:
        assert f.read() == 'hello world'


@patch('openhands.resolver.send_pull_request.reply_to_comment')
@patch('requests.post')
@patch('subprocess.run')
@patch('openhands.resolver.send_pull_request.LLM')
def test_update_existing_pull_request(
    mock_llm_class,
    mock_subprocess_run,
    mock_requests_post,
    mock_reply_to_comment,
):
    # Arrange: Set up test data
    github_issue = GithubIssue(
        owner='test-owner',
        repo='test-repo',
        number=1,
        title='Test PR',
        body='This is a test PR',
        thread_ids=['comment1', 'comment2'],
        head_branch='test-branch',
    )
    github_token = 'test-token'
    github_username = 'test-user'
    patch_dir = '/path/to/patch'
    additional_message = '["Fixed bug in function A", "Updated documentation for B"]'

    # Mock the subprocess.run call for git push
    mock_subprocess_run.return_value = MagicMock(returncode=0)

    # Mock the requests.post call for adding a PR comment
    mock_requests_post.return_value.status_code = 201

    # Mock LLM instance and completion call
    mock_llm_instance = MagicMock()
    mock_completion_response = MagicMock()
    mock_completion_response.choices = [
        MagicMock(message=MagicMock(content='This is an issue resolution.'))
    ]
    mock_llm_instance.completion.return_value = mock_completion_response
    mock_llm_class.return_value = mock_llm_instance

    llm_config = LLMConfig()

    # Act: Call the function without comment_message to test auto-generation
    result = update_existing_pull_request(
        github_issue,
        github_token,
        github_username,
        patch_dir,
        llm_config,
        comment_message=None,
        additional_message=additional_message,
    )

    # Assert: Check if the git push command was executed
    push_command = (
        f'git -C {patch_dir} push '
        f'https://{github_username}:{github_token}@github.com/'
        f'{github_issue.owner}/{github_issue.repo}.git {github_issue.head_branch}'
    )
    mock_subprocess_run.assert_called_once_with(
        push_command, shell=True, capture_output=True, text=True
    )

    # Assert: Check if the auto-generated comment was posted to the PR
    comment_url = f'https://api.github.com/repos/{github_issue.owner}/{github_issue.repo}/issues/{github_issue.number}/comments'
    expected_comment = 'This is an issue resolution.'
    mock_requests_post.assert_called_once_with(
        comment_url,
        headers={
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json',
        },
        json={'body': expected_comment},
    )

    # Assert: Check if the reply_to_comment function was called for each thread ID
    mock_reply_to_comment.assert_has_calls(
        [
            call(github_token, 'comment1', 'Fixed bug in function A'),
            call(github_token, 'comment2', 'Updated documentation for B'),
        ]
    )

    # Assert: Check the returned PR URL
    assert (
        result
        == f'https://github.com/{github_issue.owner}/{github_issue.repo}/pull/{github_issue.number}'
    )


@pytest.mark.parametrize(
    'pr_type,target_branch,pr_title',
    [
        ('branch', None, None),
        ('draft', None, None),
        ('ready', None, None),
        ('branch', 'feature', None),
        ('draft', 'develop', None),
        ('ready', 'staging', None),
        ('ready', None, 'Custom PR Title'),
        ('draft', 'develop', 'Another Custom Title'),
    ],
)
@patch('subprocess.run')
@patch('requests.post')
@patch('requests.get')
def test_send_pull_request(
    mock_get,
    mock_post,
    mock_run,
    mock_github_issue,
    mock_output_dir,
    pr_type,
    target_branch,
    pr_title,
):
    repo_path = os.path.join(mock_output_dir, 'repo')

    # Mock API responses based on whether target_branch is specified
    if target_branch:
        mock_get.side_effect = [
            MagicMock(status_code=404),  # Branch doesn't exist
            MagicMock(status_code=200),  # Target branch exists
        ]
    else:
        mock_get.side_effect = [
            MagicMock(status_code=404),  # Branch doesn't exist
            MagicMock(json=lambda: {'default_branch': 'main'}),  # Get default branch
        ]

    mock_post.return_value.json.return_value = {
        'html_url': 'https://github.com/test-owner/test-repo/pull/1'
    }

    # Mock subprocess.run calls
    mock_run.side_effect = [
        MagicMock(returncode=0),  # git checkout -b
        MagicMock(returncode=0),  # git push
    ]

    # Call the function
    result = send_pull_request(
        github_issue=mock_github_issue,
        github_token='test-token',
        github_username='test-user',
        patch_dir=repo_path,
        pr_type=pr_type,
        target_branch=target_branch,
        pr_title=pr_title,
    )

    # Assert API calls
    expected_get_calls = 2
    assert mock_get.call_count == expected_get_calls

    # Check branch creation and push
    assert mock_run.call_count == 2
    checkout_call, push_call = mock_run.call_args_list

    assert checkout_call == call(
        ['git', '-C', repo_path, 'checkout', '-b', 'openhands-fix-issue-42'],
        capture_output=True,
        text=True,
    )
    assert push_call == call(
        [
            'git',
            '-C',
            repo_path,
            'push',
            'https://test-user:test-token@github.com/test-owner/test-repo.git',
            'openhands-fix-issue-42',
        ],
        capture_output=True,
        text=True,
    )

    # Check PR creation based on pr_type
    if pr_type == 'branch':
        assert (
            result
            == 'https://github.com/test-owner/test-repo/compare/openhands-fix-issue-42?expand=1'
        )
        mock_post.assert_not_called()
    else:
        assert result == 'https://github.com/test-owner/test-repo/pull/1'
        mock_post.assert_called_once()
        post_data = mock_post.call_args[1]['json']
        expected_title = pr_title if pr_title else 'Fix issue #42: Test Issue'
        assert post_data['title'] == expected_title
        assert post_data['body'].startswith('This pull request fixes #42.')
        assert post_data['head'] == 'openhands-fix-issue-42'
        assert post_data['base'] == (target_branch if target_branch else 'main')
        assert post_data['draft'] == (pr_type == 'draft')


@patch('subprocess.run')
@patch('requests.post')
@patch('requests.get')
def test_send_pull_request_with_reviewer(
    mock_get, mock_post, mock_run, mock_github_issue, mock_output_dir
):
    repo_path = os.path.join(mock_output_dir, 'repo')
    reviewer = 'test-reviewer'

    # Mock API responses
    mock_get.side_effect = [
        MagicMock(status_code=404),  # Branch doesn't exist
        MagicMock(json=lambda: {'default_branch': 'main'}),  # Get default branch
    ]

    # Mock PR creation response
    mock_post.side_effect = [
        MagicMock(
            status_code=201,
            json=lambda: {
                'html_url': 'https://github.com/test-owner/test-repo/pull/1',
                'number': 1,
            },
        ),  # PR creation
        MagicMock(status_code=201),  # Reviewer request
    ]

    # Mock subprocess.run calls
    mock_run.side_effect = [
        MagicMock(returncode=0),  # git checkout -b
        MagicMock(returncode=0),  # git push
    ]

    # Call the function with reviewer
    result = send_pull_request(
        github_issue=mock_github_issue,
        github_token='test-token',
        github_username='test-user',
        patch_dir=repo_path,
        pr_type='ready',
        reviewer=reviewer,
    )

    # Assert API calls
    assert mock_get.call_count == 2
    assert mock_post.call_count == 2

    # Check PR creation
    pr_create_call = mock_post.call_args_list[0]
    assert pr_create_call[1]['json']['title'] == 'Fix issue #42: Test Issue'

    # Check reviewer request
    reviewer_request_call = mock_post.call_args_list[1]
    assert (
        reviewer_request_call[0][0]
        == 'https://api.github.com/repos/test-owner/test-repo/pulls/1/requested_reviewers'
    )
    assert reviewer_request_call[1]['json'] == {'reviewers': ['test-reviewer']}

    # Check the result URL
    assert result == 'https://github.com/test-owner/test-repo/pull/1'


@patch('requests.get')
def test_send_pull_request_invalid_target_branch(
    mock_get, mock_github_issue, mock_output_dir
):
    """Test that an error is raised when specifying a non-existent target branch"""
    repo_path = os.path.join(mock_output_dir, 'repo')

    # Mock API response for non-existent branch
    mock_get.side_effect = [
        MagicMock(status_code=404),  # Branch doesn't exist
        MagicMock(status_code=404),  # Target branch doesn't exist
    ]

    # Test that ValueError is raised when target branch doesn't exist
    with pytest.raises(
        ValueError, match='Target branch nonexistent-branch does not exist'
    ):
        send_pull_request(
            github_issue=mock_github_issue,
            github_token='test-token',
            github_username='test-user',
            patch_dir=repo_path,
            pr_type='ready',
            target_branch='nonexistent-branch',
        )

    # Verify API calls
    assert mock_get.call_count == 2


@patch('subprocess.run')
@patch('requests.post')
@patch('requests.get')
def test_send_pull_request_git_push_failure(
    mock_get, mock_post, mock_run, mock_github_issue, mock_output_dir
):
    repo_path = os.path.join(mock_output_dir, 'repo')

    # Mock API responses
    mock_get.return_value = MagicMock(json=lambda: {'default_branch': 'main'})

    # Mock the subprocess.run calls
    mock_run.side_effect = [
        MagicMock(returncode=0),  # git checkout -b
        MagicMock(returncode=1, stderr='Error: failed to push some refs'),  # git push
    ]

    # Test that RuntimeError is raised when git push fails
    with pytest.raises(
        RuntimeError, match='Failed to push changes to the remote repository'
    ):
        send_pull_request(
            github_issue=mock_github_issue,
            github_token='test-token',
            github_username='test-user',
            patch_dir=repo_path,
            pr_type='ready',
        )

    # Assert that subprocess.run was called twice
    assert mock_run.call_count == 2

    # Check the git checkout -b command
    checkout_call = mock_run.call_args_list[0]
    assert checkout_call[0][0] == [
        'git',
        '-C',
        repo_path,
        'checkout',
        '-b',
        'openhands-fix-issue-42',
    ]

    # Check the git push command
    push_call = mock_run.call_args_list[1]
    assert push_call[0][0] == [
        'git',
        '-C',
        repo_path,
        'push',
        'https://test-user:test-token@github.com/test-owner/test-repo.git',
        'openhands-fix-issue-42',
    ]

    # Assert that no pull request was created
    mock_post.assert_not_called()


@patch('subprocess.run')
@patch('requests.post')
@patch('requests.get')
def test_send_pull_request_permission_error(
    mock_get, mock_post, mock_run, mock_github_issue, mock_output_dir
):
    repo_path = os.path.join(mock_output_dir, 'repo')

    # Mock API responses
    mock_get.return_value = MagicMock(json=lambda: {'default_branch': 'main'})
    mock_post.return_value.status_code = 403

    # Mock subprocess.run calls
    mock_run.side_effect = [
        MagicMock(returncode=0),  # git checkout -b
        MagicMock(returncode=0),  # git push
    ]

    # Test that RuntimeError is raised when PR creation fails due to permissions
    with pytest.raises(
        RuntimeError, match='Failed to create pull request due to missing permissions.'
    ):
        send_pull_request(
            github_issue=mock_github_issue,
            github_token='test-token',
            github_username='test-user',
            patch_dir=repo_path,
            pr_type='ready',
        )

    # Assert that the branch was created and pushed
    assert mock_run.call_count == 2
    mock_post.assert_called_once()


@patch('requests.post')
def test_reply_to_comment(mock_post):
    # Arrange: set up the test data
    github_token = 'test_token'
    comment_id = 'test_comment_id'
    reply = 'This is a test reply.'

    # Mock the response from the GraphQL API
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'data': {
            'addPullRequestReviewThreadReply': {
                'comment': {
                    'id': 'test_reply_id',
                    'body': 'Openhands fix success summary\n\n\nThis is a test reply.',
                    'createdAt': '2024-10-01T12:34:56Z',
                }
            }
        }
    }

    mock_post.return_value = mock_response

    # Act: call the function
    reply_to_comment(github_token, comment_id, reply)

    # Assert: check that the POST request was made with the correct parameters
    query = """
            mutation($body: String!, $pullRequestReviewThreadId: ID!) {
                addPullRequestReviewThreadReply(input: { body: $body, pullRequestReviewThreadId: $pullRequestReviewThreadId }) {
                    comment {
                        id
                        body
                        createdAt
                    }
                }
            }
            """

    expected_variables = {
        'body': 'Openhands fix success summary\n\n\nThis is a test reply.',
        'pullRequestReviewThreadId': comment_id,
    }

    # Check that the correct request was made to the API
    mock_post.assert_called_once_with(
        'https://api.github.com/graphql',
        json={'query': query, 'variables': expected_variables},
        headers={
            'Authorization': f'Bearer {github_token}',
            'Content-Type': 'application/json',
        },
    )

    # Check that the response status was checked (via response.raise_for_status)
    mock_response.raise_for_status.assert_called_once()


@patch('openhands.resolver.send_pull_request.initialize_repo')
@patch('openhands.resolver.send_pull_request.apply_patch')
@patch('openhands.resolver.send_pull_request.update_existing_pull_request')
@patch('openhands.resolver.send_pull_request.make_commit')
def test_process_single_pr_update(
    mock_make_commit,
    mock_update_existing_pull_request,
    mock_apply_patch,
    mock_initialize_repo,
    mock_output_dir,
    mock_llm_config,
):
    # Initialize test data
    github_token = 'test_token'
    github_username = 'test_user'
    pr_type = 'draft'

    resolver_output = ResolverOutput(
        issue=GithubIssue(
            owner='test-owner',
            repo='test-repo',
            number=1,
            title='Issue 1',
            body='Body 1',
            closing_issues=[],
            review_threads=[
                ReviewThread(comment='review comment for feedback', files=[])
            ],
            thread_ids=['1'],
            head_branch='branch 1',
        ),
        issue_type='pr',
        instruction='Test instruction 1',
        base_commit='def456',
        git_patch='Test patch 1',
        history=[],
        metrics={},
        success=True,
        comment_success=None,
        result_explanation='[Test success 1]',
        error=None,
    )

    mock_update_existing_pull_request.return_value = (
        'https://github.com/test-owner/test-repo/pull/1'
    )
    mock_initialize_repo.return_value = f'{mock_output_dir}/patches/pr_1'

    process_single_issue(
        mock_output_dir,
        resolver_output,
        github_token,
        github_username,
        pr_type,
        mock_llm_config,
        None,
        False,
        None,
    )

    mock_initialize_repo.assert_called_once_with(mock_output_dir, 1, 'pr', 'branch 1')
    mock_apply_patch.assert_called_once_with(
        f'{mock_output_dir}/patches/pr_1', resolver_output.git_patch
    )
    mock_make_commit.assert_called_once_with(
        f'{mock_output_dir}/patches/pr_1', resolver_output.issue, 'pr'
    )
    mock_update_existing_pull_request.assert_called_once_with(
        github_issue=resolver_output.issue,
        github_token=github_token,
        github_username=github_username,
        patch_dir=f'{mock_output_dir}/patches/pr_1',
        additional_message='[Test success 1]',
        llm_config=mock_llm_config,
    )


@patch('openhands.resolver.send_pull_request.initialize_repo')
@patch('openhands.resolver.send_pull_request.apply_patch')
@patch('openhands.resolver.send_pull_request.send_pull_request')
@patch('openhands.resolver.send_pull_request.make_commit')
def test_process_single_issue(
    mock_make_commit,
    mock_send_pull_request,
    mock_apply_patch,
    mock_initialize_repo,
    mock_output_dir,
    mock_llm_config,
):
    # Initialize test data
    github_token = 'test_token'
    github_username = 'test_user'
    pr_type = 'draft'

    resolver_output = ResolverOutput(
        issue=GithubIssue(
            owner='test-owner',
            repo='test-repo',
            number=1,
            title='Issue 1',
            body='Body 1',
        ),
        issue_type='issue',
        instruction='Test instruction 1',
        base_commit='def456',
        git_patch='Test patch 1',
        history=[],
        metrics={},
        success=True,
        comment_success=None,
        result_explanation='Test success 1',
        error=None,
    )

    # Mock return value
    mock_send_pull_request.return_value = (
        'https://github.com/test-owner/test-repo/pull/1'
    )
    mock_initialize_repo.return_value = f'{mock_output_dir}/patches/issue_1'

    # Call the function
    process_single_issue(
        mock_output_dir,
        resolver_output,
        github_token,
        github_username,
        pr_type,
        mock_llm_config,
        None,
        False,
        None,
    )

    # Assert that the mocked functions were called with correct arguments
    mock_initialize_repo.assert_called_once_with(mock_output_dir, 1, 'issue', 'def456')
    mock_apply_patch.assert_called_once_with(
        f'{mock_output_dir}/patches/issue_1', resolver_output.git_patch
    )
    mock_make_commit.assert_called_once_with(
        f'{mock_output_dir}/patches/issue_1', resolver_output.issue, 'issue'
    )
    mock_send_pull_request.assert_called_once_with(
        github_issue=resolver_output.issue,
        github_token=github_token,
        github_username=github_username,
        patch_dir=f'{mock_output_dir}/patches/issue_1',
        pr_type=pr_type,
        fork_owner=None,
        additional_message=resolver_output.result_explanation,
        target_branch=None,
        reviewer=None,
        pr_title=None,
    )


@patch('openhands.resolver.send_pull_request.initialize_repo')
@patch('openhands.resolver.send_pull_request.apply_patch')
@patch('openhands.resolver.send_pull_request.send_pull_request')
@patch('openhands.resolver.send_pull_request.make_commit')
def test_process_single_issue_unsuccessful(
    mock_make_commit,
    mock_send_pull_request,
    mock_apply_patch,
    mock_initialize_repo,
    mock_output_dir,
    mock_llm_config,
):
    # Initialize test data
    github_token = 'test_token'
    github_username = 'test_user'
    pr_type = 'draft'

    resolver_output = ResolverOutput(
        issue=GithubIssue(
            owner='test-owner',
            repo='test-repo',
            number=1,
            title='Issue 1',
            body='Body 1',
        ),
        issue_type='issue',
        instruction='Test instruction 1',
        base_commit='def456',
        git_patch='Test patch 1',
        history=[],
        metrics={},
        success=False,
        comment_success=None,
        result_explanation='',
        error='Test error',
    )

    # Call the function
    process_single_issue(
        mock_output_dir,
        resolver_output,
        github_token,
        github_username,
        pr_type,
        mock_llm_config,
        None,
        False,
        None,
    )

    # Assert that none of the mocked functions were called
    mock_initialize_repo.assert_not_called()
    mock_apply_patch.assert_not_called()
    mock_make_commit.assert_not_called()
    mock_send_pull_request.assert_not_called()


@patch('openhands.resolver.send_pull_request.load_all_resolver_outputs')
@patch('openhands.resolver.send_pull_request.process_single_issue')
def test_process_all_successful_issues(
    mock_process_single_issue, mock_load_all_resolver_outputs, mock_llm_config
):
    # Create ResolverOutput objects with properly initialized GithubIssue instances
    resolver_output_1 = ResolverOutput(
        issue=GithubIssue(
            owner='test-owner',
            repo='test-repo',
            number=1,
            title='Issue 1',
            body='Body 1',
        ),
        issue_type='issue',
        instruction='Test instruction 1',
        base_commit='def456',
        git_patch='Test patch 1',
        history=[],
        metrics={},
        success=True,
        comment_success=None,
        result_explanation='Test success 1',
        error=None,
    )

    resolver_output_2 = ResolverOutput(
        issue=GithubIssue(
            owner='test-owner',
            repo='test-repo',
            number=2,
            title='Issue 2',
            body='Body 2',
        ),
        issue_type='issue',
        instruction='Test instruction 2',
        base_commit='ghi789',
        git_patch='Test patch 2',
        history=[],
        metrics={},
        success=False,
        comment_success=None,
        result_explanation='',
        error='Test error 2',
    )

    resolver_output_3 = ResolverOutput(
        issue=GithubIssue(
            owner='test-owner',
            repo='test-repo',
            number=3,
            title='Issue 3',
            body='Body 3',
        ),
        issue_type='issue',
        instruction='Test instruction 3',
        base_commit='jkl012',
        git_patch='Test patch 3',
        history=[],
        metrics={},
        success=True,
        comment_success=None,
        result_explanation='Test success 3',
        error=None,
    )

    mock_load_all_resolver_outputs.return_value = [
        resolver_output_1,
        resolver_output_2,
        resolver_output_3,
    ]

    # Call the function
    process_all_successful_issues(
        'output_dir',
        'github_token',
        'github_username',
        'draft',
        mock_llm_config,  # llm_config
        None,  # fork_owner
    )

    # Assert that process_single_issue was called for successful issues only
    assert mock_process_single_issue.call_count == 2

    # Check that the function was called with the correct arguments for successful issues
    mock_process_single_issue.assert_has_calls(
        [
            call(
                'output_dir',
                resolver_output_1,
                'github_token',
                'github_username',
                'draft',
                mock_llm_config,
                None,
                False,
                None,
            ),
            call(
                'output_dir',
                resolver_output_3,
                'github_token',
                'github_username',
                'draft',
                mock_llm_config,
                None,
                False,
                None,
            ),
        ]
    )

    # Add more assertions as needed to verify the behavior of the function


@patch('requests.get')
@patch('subprocess.run')
def test_send_pull_request_branch_naming(
    mock_run, mock_get, mock_github_issue, mock_output_dir
):
    repo_path = os.path.join(mock_output_dir, 'repo')

    # Mock API responses
    mock_get.side_effect = [
        MagicMock(status_code=200),  # First branch exists
        MagicMock(status_code=200),  # Second branch exists
        MagicMock(status_code=404),  # Third branch doesn't exist
        MagicMock(json=lambda: {'default_branch': 'main'}),  # Get default branch
    ]

    # Mock subprocess.run calls
    mock_run.side_effect = [
        MagicMock(returncode=0),  # git checkout -b
        MagicMock(returncode=0),  # git push
    ]

    # Call the function
    result = send_pull_request(
        github_issue=mock_github_issue,
        github_token='test-token',
        github_username='test-user',
        patch_dir=repo_path,
        pr_type='branch',
    )

    # Assert API calls
    assert mock_get.call_count == 4

    # Check branch creation and push
    assert mock_run.call_count == 2
    checkout_call, push_call = mock_run.call_args_list

    assert checkout_call == call(
        ['git', '-C', repo_path, 'checkout', '-b', 'openhands-fix-issue-42-try3'],
        capture_output=True,
        text=True,
    )
    assert push_call == call(
        [
            'git',
            '-C',
            repo_path,
            'push',
            'https://test-user:test-token@github.com/test-owner/test-repo.git',
            'openhands-fix-issue-42-try3',
        ],
        capture_output=True,
        text=True,
    )

    # Check the result
    assert (
        result
        == 'https://github.com/test-owner/test-repo/compare/openhands-fix-issue-42-try3?expand=1'
    )


@patch('openhands.resolver.send_pull_request.argparse.ArgumentParser')
@patch('openhands.resolver.send_pull_request.process_all_successful_issues')
@patch('openhands.resolver.send_pull_request.process_single_issue')
@patch('openhands.resolver.send_pull_request.load_single_resolver_output')
@patch('os.path.exists')
@patch('os.getenv')
def test_main(
    mock_getenv,
    mock_path_exists,
    mock_load_single_resolver_output,
    mock_process_single_issue,
    mock_process_all_successful_issues,
    mock_parser,
):
    from openhands.resolver.send_pull_request import main

    # Setup mock parser
    mock_args = MagicMock()
    mock_args.github_token = None
    mock_args.github_username = 'mock_username'
    mock_args.output_dir = '/mock/output'
    mock_args.pr_type = 'draft'
    mock_args.issue_number = '42'
    mock_args.fork_owner = None
    mock_args.send_on_failure = False
    mock_args.llm_model = 'mock_model'
    mock_args.llm_base_url = 'mock_url'
    mock_args.llm_api_key = 'mock_key'
    mock_args.target_branch = None
    mock_args.reviewer = None
    mock_args.pr_title = None
    mock_parser.return_value.parse_args.return_value = mock_args

    # Setup environment variables
    mock_getenv.side_effect = (
        lambda key, default=None: 'mock_token' if key == 'GITHUB_TOKEN' else default
    )

    # Setup path exists
    mock_path_exists.return_value = True

    # Setup mock resolver output
    mock_resolver_output = MagicMock()
    mock_load_single_resolver_output.return_value = mock_resolver_output

    # Run main function
    main()

    llm_config = LLMConfig(
        model=mock_args.llm_model,
        base_url=mock_args.llm_base_url,
        api_key=mock_args.llm_api_key,
    )

    # Use any_call instead of assert_called_with for more flexible matching
    assert mock_process_single_issue.call_args == call(
        '/mock/output',
        mock_resolver_output,
        'mock_token',
        'mock_username',
        'draft',
        llm_config,
        None,
        False,
        mock_args.target_branch,
        mock_args.reviewer,
        mock_args.pr_title,
    )

    # Other assertions
    mock_parser.assert_called_once()
    mock_getenv.assert_any_call('GITHUB_TOKEN')
    mock_path_exists.assert_called_with('/mock/output')
    mock_load_single_resolver_output.assert_called_with('/mock/output/output.jsonl', 42)

    # Test for 'all_successful' issue number
    mock_args.issue_number = 'all_successful'
    main()
    mock_process_all_successful_issues.assert_called_with(
        '/mock/output',
        'mock_token',
        'mock_username',
        'draft',
        llm_config,
        None,
    )

    # Test for invalid issue number
    mock_args.issue_number = 'invalid'
    with pytest.raises(ValueError):
        main()


@patch('subprocess.run')
def test_make_commit_escapes_issue_title(mock_subprocess_run):
    # Setup
    repo_dir = '/path/to/repo'
    issue = GithubIssue(
        owner='test-owner',
        repo='test-repo',
        number=42,
        title='Issue with "quotes" and $pecial characters',
        body='Test body',
    )

    # Mock subprocess.run to return success for all calls
    mock_subprocess_run.return_value = MagicMock(
        returncode=0, stdout='sample output', stderr=''
    )

    # Call the function
    issue_type = 'issue'
    make_commit(repo_dir, issue, issue_type)

    # Assert that subprocess.run was called with the correct arguments
    calls = mock_subprocess_run.call_args_list
    assert len(calls) == 4  # git config check, git add, git commit

    # Check the git commit call
    git_commit_call = calls[3][0][0]
    expected_commit_message = (
        'Fix issue #42: Issue with "quotes" and $pecial characters'
    )
    assert [
        'git',
        '-C',
        '/path/to/repo',
        'commit',
        '-m',
        expected_commit_message,
    ] == git_commit_call


@patch('subprocess.run')
def test_make_commit_no_changes(mock_subprocess_run):
    # Setup
    repo_dir = '/path/to/repo'
    issue = GithubIssue(
        owner='test-owner',
        repo='test-repo',
        number=42,
        title='Issue with no changes',
        body='Test body',
    )

    # Mock subprocess.run to simulate no changes in the repo
    mock_subprocess_run.side_effect = [
        MagicMock(returncode=0),
        MagicMock(returncode=0),
        MagicMock(returncode=1, stdout=''),  # git status --porcelain (no changes)
    ]

    with pytest.raises(
        RuntimeError, match='ERROR: Openhands failed to make code changes.'
    ):
        make_commit(repo_dir, issue, 'issue')

    # Check that subprocess.run was called for checking git status and add, but not commit
    assert mock_subprocess_run.call_count == 3
    git_status_call = mock_subprocess_run.call_args_list[2][0][0]
    assert f'git -C {repo_dir} status --porcelain' in git_status_call


def test_apply_patch_rename_directory(mock_output_dir):
    # Create a sample directory structure
    old_dir = os.path.join(mock_output_dir, 'prompts', 'resolve')
    os.makedirs(old_dir)

    # Create test files
    test_files = [
        'issue-success-check.jinja',
        'pr-feedback-check.jinja',
        'pr-thread-check.jinja',
    ]
    for filename in test_files:
        file_path = os.path.join(old_dir, filename)
        with open(file_path, 'w') as f:
            f.write(f'Content of {filename}')

    # Create a patch that renames the directory
    patch_content = """diff --git a/prompts/resolve/issue-success-check.jinja b/prompts/guess_success/issue-success-check.jinja
similarity index 100%
rename from prompts/resolve/issue-success-check.jinja
rename to prompts/guess_success/issue-success-check.jinja
diff --git a/prompts/resolve/pr-feedback-check.jinja b/prompts/guess_success/pr-feedback-check.jinja
similarity index 100%
rename from prompts/resolve/pr-feedback-check.jinja
rename to prompts/guess_success/pr-feedback-check.jinja
diff --git a/prompts/resolve/pr-thread-check.jinja b/prompts/guess_success/pr-thread-check.jinja
similarity index 100%
rename from prompts/resolve/pr-thread-check.jinja
rename to prompts/guess_success/pr-thread-check.jinja"""

    # Apply the patch
    apply_patch(mock_output_dir, patch_content)

    # Check if files were moved correctly
    new_dir = os.path.join(mock_output_dir, 'prompts', 'guess_success')
    assert not os.path.exists(old_dir), 'Old directory still exists'
    assert os.path.exists(new_dir), 'New directory was not created'

    # Check if all files were moved and content preserved
    for filename in test_files:
        old_path = os.path.join(old_dir, filename)
        new_path = os.path.join(new_dir, filename)
        assert not os.path.exists(old_path), f'Old file {filename} still exists'
        assert os.path.exists(new_path), f'New file {filename} was not created'
        with open(new_path, 'r') as f:
            content = f.read()
        assert content == f'Content of {filename}', f'Content mismatch for {filename}'
