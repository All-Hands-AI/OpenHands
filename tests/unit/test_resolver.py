from openhands.resolver.github_issue import GithubIssue
from openhands.resolver.resolver_output import ResolverOutput


def test_resolver_output_has_partial_success():
    # Test case 1: No comment_success
    output = ResolverOutput(
        issue=GithubIssue(
            owner='test', repo='test', number=1, title='test', body='test'
        ),
        issue_type='pr',
        instruction='test',
        base_commit='test',
        git_patch='test',
        history=[],
        metrics=None,
        success=False,
        comment_success=None,
        success_explanation='test',
        error=None,
    )
    assert not output.has_partial_success

    # Test case 2: Empty comment_success list
    output = ResolverOutput(
        issue=GithubIssue(
            owner='test', repo='test', number=1, title='test', body='test'
        ),
        issue_type='pr',
        instruction='test',
        base_commit='test',
        git_patch='test',
        history=[],
        metrics=None,
        success=False,
        comment_success=[],
        success_explanation='test',
        error=None,
    )
    assert not output.has_partial_success

    # Test case 3: All comments failed
    output = ResolverOutput(
        issue=GithubIssue(
            owner='test', repo='test', number=1, title='test', body='test'
        ),
        issue_type='pr',
        instruction='test',
        base_commit='test',
        git_patch='test',
        history=[],
        metrics=None,
        success=False,
        comment_success=[False, False],
        success_explanation='test',
        error=None,
    )
    assert not output.has_partial_success

    # Test case 4: Some comments succeeded
    output = ResolverOutput(
        issue=GithubIssue(
            owner='test', repo='test', number=1, title='test', body='test'
        ),
        issue_type='pr',
        instruction='test',
        base_commit='test',
        git_patch='test',
        history=[],
        metrics=None,
        success=False,
        comment_success=[True, False],
        success_explanation='test',
        error=None,
    )
    assert output.has_partial_success

    # Test case 5: All comments succeeded
    output = ResolverOutput(
        issue=GithubIssue(
            owner='test', repo='test', number=1, title='test', body='test'
        ),
        issue_type='pr',
        instruction='test',
        base_commit='test',
        git_patch='test',
        history=[],
        metrics=None,
        success=False,
        comment_success=[True, True],
        success_explanation='test',
        error=None,
    )
    assert output.has_partial_success
