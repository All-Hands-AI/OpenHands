import os
import subprocess
import tempfile

from openhands.integrations.service_types import ProviderType
from openhands.resolver.interfaces.issue import Issue
from openhands.resolver.send_pull_request import make_commit


def test_commit_message_with_quotes():
    # Create a temporary directory and initialize git repo
    with tempfile.TemporaryDirectory() as temp_dir:
        subprocess.run(['git', 'init', temp_dir], check=True)

        # Create a test file and add it to git
        test_file = os.path.join(temp_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test content')

        subprocess.run(['git', '-C', temp_dir, 'add', 'test.txt'], check=True)

        # Create a test issue with problematic title
        issue = Issue(
            owner='test-owner',
            repo='test-repo',
            number=123,
            title="Issue with 'quotes' and \"double quotes\" and <class 'ValueError'>",
            body='Test body',
            labels=[],
            assignees=[],
            state='open',
            created_at='2024-01-01T00:00:00Z',
            updated_at='2024-01-01T00:00:00Z',
            closed_at=None,
            head_branch=None,
            thread_ids=None,
        )

        # Make the commit
        make_commit(temp_dir, issue, 'issue')

        # Get the commit message
        result = subprocess.run(
            ['git', '-C', temp_dir, 'log', '-1', '--pretty=%B'],
            capture_output=True,
            text=True,
            check=True,
        )
        commit_msg = result.stdout.strip()

        # The commit message should contain the quotes without excessive escaping
        expected = "Fix issue #123: Issue with 'quotes' and \"double quotes\" and <class 'ValueError'>"
        assert commit_msg == expected, f'Expected: {expected}\nGot: {commit_msg}'


def test_pr_title_with_quotes(monkeypatch):
    # Mock requests.post to avoid actual API calls
    class MockResponse:
        def __init__(self, status_code=201):
            self.status_code = status_code
            self.text = ''

        def json(self):
            return {'html_url': 'https://github.com/test/test/pull/1'}

        def raise_for_status(self):
            pass

    def mock_post(*args, **kwargs):
        # Verify that the PR title is not over-escaped
        data = kwargs.get('json', {})
        title = data.get('title', '')
        expected = "Fix issue #123: Issue with 'quotes' and \"double quotes\" and <class 'ValueError'>"
        assert title == expected, (
            f'PR title was incorrectly escaped.\nExpected: {expected}\nGot: {title}'
        )
        return MockResponse()

    class MockGetResponse:
        def __init__(self, status_code=200):
            self.status_code = status_code
            self.text = ''

        def json(self):
            return {'default_branch': 'main'}

        def raise_for_status(self):
            pass

    monkeypatch.setattr('httpx.post', mock_post)
    monkeypatch.setattr('httpx.get', lambda *args, **kwargs: MockGetResponse())
    monkeypatch.setattr(
        'openhands.resolver.interfaces.github.GithubIssueHandler.branch_exists',
        lambda *args, **kwargs: False,
    )

    # Mock subprocess.run to avoid actual git commands
    original_run = subprocess.run

    def mock_run(*args, **kwargs):
        print(f'Running command: {args[0] if args else kwargs.get("args", [])}')
        if isinstance(args[0], list) and args[0][0] == 'git':
            if 'push' in args[0]:
                return subprocess.CompletedProcess(
                    args[0], returncode=0, stdout='', stderr=''
                )
            return original_run(*args, **kwargs)
        return original_run(*args, **kwargs)

    monkeypatch.setattr('subprocess.run', mock_run)

    # Create a temporary directory and initialize git repo
    with tempfile.TemporaryDirectory() as temp_dir:
        print('Initializing git repo...')
        subprocess.run(['git', 'init', temp_dir], check=True)

        # Add these lines to configure git
        subprocess.run(
            ['git', '-C', temp_dir, 'config', 'user.name', 'Test User'], check=True
        )
        subprocess.run(
            ['git', '-C', temp_dir, 'config', 'user.email', 'test@example.com'],
            check=True,
        )

        # Create a test file and add it to git
        test_file = os.path.join(temp_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test content')

        print('Adding and committing test file...')
        subprocess.run(['git', '-C', temp_dir, 'add', 'test.txt'], check=True)
        subprocess.run(
            ['git', '-C', temp_dir, 'commit', '-m', 'Initial commit'], check=True
        )

        # Create a test issue with problematic title
        print('Creating test issue...')
        issue = Issue(
            owner='test-owner',
            repo='test-repo',
            number=123,
            title="Issue with 'quotes' and \"double quotes\" and <class 'ValueError'>",
            body='Test body',
            labels=[],
            assignees=[],
            state='open',
            created_at='2024-01-01T00:00:00Z',
            updated_at='2024-01-01T00:00:00Z',
            closed_at=None,
            head_branch=None,
            thread_ids=None,
        )

        # Try to send a PR - this will fail if the title is incorrectly escaped
        print('Sending PR...')
        from openhands.resolver.send_pull_request import send_pull_request

        send_pull_request(
            issue=issue,
            token='dummy-token',
            username='test-user',
            platform=ProviderType.GITHUB,
            patch_dir=temp_dir,
            pr_type='ready',
        )
