from unittest.mock import MagicMock, patch

from openhands.core.config import LLMConfig
from openhands.resolver.github_issue import ReviewThread
from openhands.resolver.issue_definitions import IssueHandler, PRHandler


def test_get_converted_issues_initializes_review_comments():
    # Mock the necessary dependencies
    with patch('requests.get') as mock_get:
        # Mock the response for issues
        mock_issues_response = MagicMock()
        mock_issues_response.json.return_value = [
            {'number': 1, 'title': 'Test Issue', 'body': 'Test Body'}
        ]
        # Mock the response for comments
        mock_comments_response = MagicMock()
        mock_comments_response.json.return_value = []

        # Set up the mock to return different responses for different calls
        # First call is for issues, second call is for comments
        mock_get.side_effect = [
            mock_issues_response,
            mock_comments_response,
            mock_comments_response,
        ]  # Need two comment responses because we make two API calls

        # Create an instance of IssueHandler
        llm_config = LLMConfig(model='test', api_key='test')
        handler = IssueHandler('test-owner', 'test-repo', 'test-token', llm_config)

        # Get converted issues
        issues = handler.get_converted_issues(issue_numbers=[1])

        # Verify that we got exactly one issue
        assert len(issues) == 1

        # Verify that review_comments is initialized as None
        assert issues[0].review_comments is None

        # Verify other fields are set correctly
        assert issues[0].number == 1
        assert issues[0].title == 'Test Issue'
        assert issues[0].body == 'Test Body'
        assert issues[0].owner == 'test-owner'
        assert issues[0].repo == 'test-repo'


def test_pr_handler_get_converted_issues_with_comments():
    # Mock the necessary dependencies
    with patch('requests.get') as mock_get:
        # Mock the response for PRs
        mock_prs_response = MagicMock()
        mock_prs_response.json.return_value = [
            {
                'number': 1,
                'title': 'Test PR',
                'body': 'Test Body fixes #1',
                'head': {'ref': 'test-branch'},
            }
        ]

        # Mock the response for PR comments
        mock_comments_response = MagicMock()
        mock_comments_response.json.return_value = [
            {'body': 'First comment'},
            {'body': 'Second comment'},
        ]

        # Mock the response for PR metadata (GraphQL)
        mock_graphql_response = MagicMock()
        mock_graphql_response.json.return_value = {
            'data': {
                'repository': {
                    'pullRequest': {
                        'closingIssuesReferences': {'edges': []},
                        'reviews': {'nodes': []},
                        'reviewThreads': {'edges': []},
                    }
                }
            }
        }

        # Set up the mock to return different responses
        # We need to return empty responses for subsequent pages
        mock_empty_response = MagicMock()
        mock_empty_response.json.return_value = []

        # Mock the response for fetching the external issue referenced in PR body
        mock_external_issue_response = MagicMock()
        mock_external_issue_response.json.return_value = {
            'body': 'This is additional context from an externally referenced issue.'
        }

        mock_get.side_effect = [
            mock_prs_response,  # First call for PRs
            mock_empty_response,  # Second call for PRs (empty page)
            mock_comments_response,  # Third call for PR comments
            mock_empty_response,  # Fourth call for PR comments (empty page)
            mock_external_issue_response,  # Mock response for the external issue reference #1
        ]

        # Mock the post request for GraphQL
        with patch('requests.post') as mock_post:
            mock_post.return_value = mock_graphql_response

            # Create an instance of PRHandler
            llm_config = LLMConfig(model='test', api_key='test')
            handler = PRHandler('test-owner', 'test-repo', 'test-token', llm_config)

            # Get converted issues
            prs = handler.get_converted_issues(issue_numbers=[1])

            # Verify that we got exactly one PR
            assert len(prs) == 1

            # Verify that thread_comments are set correctly
            assert prs[0].thread_comments == ['First comment', 'Second comment']

            # Verify other fields are set correctly
            assert prs[0].number == 1
            assert prs[0].title == 'Test PR'
            assert prs[0].body == 'Test Body fixes #1'
            assert prs[0].owner == 'test-owner'
            assert prs[0].repo == 'test-repo'
            assert prs[0].head_branch == 'test-branch'
            assert prs[0].closing_issues == [
                'This is additional context from an externally referenced issue.'
            ]


def test_get_issue_comments_with_specific_comment_id():
    # Mock the necessary dependencies
    with patch('requests.get') as mock_get:
        # Mock the response for comments
        mock_comments_response = MagicMock()
        mock_comments_response.json.return_value = [
            {'id': 123, 'body': 'First comment'},
            {'id': 456, 'body': 'Second comment'},
        ]

        mock_get.return_value = mock_comments_response

        # Create an instance of IssueHandler
        llm_config = LLMConfig(model='test', api_key='test')
        handler = IssueHandler('test-owner', 'test-repo', 'test-token', llm_config)

        # Get comments with a specific comment_id
        specific_comment = handler._get_issue_comments(issue_number=1, comment_id=123)

        # Verify only the specific comment is returned
        assert specific_comment == ['First comment']


def test_pr_handler_get_converted_issues_with_specific_thread_comment():
    # Define the specific comment_id to filter
    specific_comment_id = 123

    # Mock GraphQL response for review threads
    with patch('requests.get') as mock_get:
        # Mock the response for PRs
        mock_prs_response = MagicMock()
        mock_prs_response.json.return_value = [
            {
                'number': 1,
                'title': 'Test PR',
                'body': 'Test Body',
                'head': {'ref': 'test-branch'},
            }
        ]

        # Mock the response for PR comments
        mock_comments_response = MagicMock()
        mock_comments_response.json.return_value = [
            {'body': 'First comment', 'id': 123},
            {'body': 'Second comment', 'id': 124},
        ]

        # Mock the response for PR metadata (GraphQL)
        mock_graphql_response = MagicMock()
        mock_graphql_response.json.return_value = {
            'data': {
                'repository': {
                    'pullRequest': {
                        'closingIssuesReferences': {'edges': []},
                        'reviews': {'nodes': []},
                        'reviewThreads': {
                            'edges': [
                                {
                                    'node': {
                                        'id': 'review-thread-1',
                                        'isResolved': False,
                                        'comments': {
                                            'nodes': [
                                                {
                                                    'fullDatabaseId': 121,
                                                    'body': 'Specific review comment',
                                                    'path': 'file1.txt',
                                                },
                                                {
                                                    'fullDatabaseId': 456,
                                                    'body': 'Another review comment',
                                                    'path': 'file2.txt',
                                                },
                                            ]
                                        },
                                    }
                                }
                            ]
                        },
                    }
                }
            }
        }

        # Set up the mock to return different responses
        # We need to return empty responses for subsequent pages
        mock_empty_response = MagicMock()
        mock_empty_response.json.return_value = []

        mock_get.side_effect = [
            mock_prs_response,  # First call for PRs
            mock_empty_response,  # Second call for PRs (empty page)
            mock_comments_response,  # Third call for PR comments
            mock_empty_response,  # Fourth call for PR comments (empty page)
        ]

        # Mock the post request for GraphQL
        with patch('requests.post') as mock_post:
            mock_post.return_value = mock_graphql_response

            # Create an instance of PRHandler
            llm_config = LLMConfig(model='test', api_key='test')
            handler = PRHandler('test-owner', 'test-repo', 'test-token', llm_config)

            # Get converted issues
            prs = handler.get_converted_issues(
                issue_numbers=[1], comment_id=specific_comment_id
            )

            # Verify that we got exactly one PR
            assert len(prs) == 1

            # Verify that thread_comments are set correctly
            assert prs[0].thread_comments == ['First comment']
            assert prs[0].review_comments == []
            assert prs[0].review_threads == []

            # Verify other fields are set correctly
            assert prs[0].number == 1
            assert prs[0].title == 'Test PR'
            assert prs[0].body == 'Test Body'
            assert prs[0].owner == 'test-owner'
            assert prs[0].repo == 'test-repo'
            assert prs[0].head_branch == 'test-branch'


def test_pr_handler_get_converted_issues_with_specific_review_thread_comment():
    # Define the specific comment_id to filter
    specific_comment_id = 123

    # Mock GraphQL response for review threads
    with patch('requests.get') as mock_get:
        # Mock the response for PRs
        mock_prs_response = MagicMock()
        mock_prs_response.json.return_value = [
            {
                'number': 1,
                'title': 'Test PR',
                'body': 'Test Body',
                'head': {'ref': 'test-branch'},
            }
        ]

        # Mock the response for PR comments
        mock_comments_response = MagicMock()
        mock_comments_response.json.return_value = [
            {'body': 'First comment', 'id': 120},
            {'body': 'Second comment', 'id': 124},
        ]

        # Mock the response for PR metadata (GraphQL)
        mock_graphql_response = MagicMock()
        mock_graphql_response.json.return_value = {
            'data': {
                'repository': {
                    'pullRequest': {
                        'closingIssuesReferences': {'edges': []},
                        'reviews': {'nodes': []},
                        'reviewThreads': {
                            'edges': [
                                {
                                    'node': {
                                        'id': 'review-thread-1',
                                        'isResolved': False,
                                        'comments': {
                                            'nodes': [
                                                {
                                                    'fullDatabaseId': specific_comment_id,
                                                    'body': 'Specific review comment',
                                                    'path': 'file1.txt',
                                                },
                                                {
                                                    'fullDatabaseId': 456,
                                                    'body': 'Another review comment',
                                                    'path': 'file1.txt',
                                                },
                                            ]
                                        },
                                    }
                                }
                            ]
                        },
                    }
                }
            }
        }

        # Set up the mock to return different responses
        # We need to return empty responses for subsequent pages
        mock_empty_response = MagicMock()
        mock_empty_response.json.return_value = []

        mock_get.side_effect = [
            mock_prs_response,  # First call for PRs
            mock_empty_response,  # Second call for PRs (empty page)
            mock_comments_response,  # Third call for PR comments
            mock_empty_response,  # Fourth call for PR comments (empty page)
        ]

        # Mock the post request for GraphQL
        with patch('requests.post') as mock_post:
            mock_post.return_value = mock_graphql_response

            # Create an instance of PRHandler
            llm_config = LLMConfig(model='test', api_key='test')
            handler = PRHandler('test-owner', 'test-repo', 'test-token', llm_config)

            # Get converted issues
            prs = handler.get_converted_issues(
                issue_numbers=[1], comment_id=specific_comment_id
            )

            # Verify that we got exactly one PR
            assert len(prs) == 1

            # Verify that thread_comments are set correctly
            assert prs[0].thread_comments is None
            assert prs[0].review_comments == []
            assert len(prs[0].review_threads) == 1
            assert isinstance(prs[0].review_threads[0], ReviewThread)
            assert (
                prs[0].review_threads[0].comment
                == 'Specific review comment\n---\nlatest feedback:\nAnother review comment\n'
            )
            assert prs[0].review_threads[0].files == ['file1.txt']

            # Verify other fields are set correctly
            assert prs[0].number == 1
            assert prs[0].title == 'Test PR'
            assert prs[0].body == 'Test Body'
            assert prs[0].owner == 'test-owner'
            assert prs[0].repo == 'test-repo'
            assert prs[0].head_branch == 'test-branch'


def test_pr_handler_get_converted_issues_with_specific_comment_and_issue_refs():
    # Define the specific comment_id to filter
    specific_comment_id = 123

    # Mock GraphQL response for review threads
    with patch('requests.get') as mock_get:
        # Mock the response for PRs
        mock_prs_response = MagicMock()
        mock_prs_response.json.return_value = [
            {
                'number': 1,
                'title': 'Test PR fixes #3',
                'body': 'Test Body',
                'head': {'ref': 'test-branch'},
            }
        ]

        # Mock the response for PR comments
        mock_comments_response = MagicMock()
        mock_comments_response.json.return_value = [
            {'body': 'First comment', 'id': 120},
            {'body': 'Second comment', 'id': 124},
        ]

        # Mock the response for PR metadata (GraphQL)
        mock_graphql_response = MagicMock()
        mock_graphql_response.json.return_value = {
            'data': {
                'repository': {
                    'pullRequest': {
                        'closingIssuesReferences': {'edges': []},
                        'reviews': {'nodes': []},
                        'reviewThreads': {
                            'edges': [
                                {
                                    'node': {
                                        'id': 'review-thread-1',
                                        'isResolved': False,
                                        'comments': {
                                            'nodes': [
                                                {
                                                    'fullDatabaseId': specific_comment_id,
                                                    'body': 'Specific review comment that references #6',
                                                    'path': 'file1.txt',
                                                },
                                                {
                                                    'fullDatabaseId': 456,
                                                    'body': 'Another review comment referencing #7',
                                                    'path': 'file2.txt',
                                                },
                                            ]
                                        },
                                    }
                                }
                            ]
                        },
                    }
                }
            }
        }

        # Set up the mock to return different responses
        # We need to return empty responses for subsequent pages
        mock_empty_response = MagicMock()
        mock_empty_response.json.return_value = []

        # Mock the response for fetching the external issue referenced in PR body
        mock_external_issue_response_in_body = MagicMock()
        mock_external_issue_response_in_body.json.return_value = {
            'body': 'External context #1.'
        }

        # Mock the response for fetching the external issue referenced in review thread
        mock_external_issue_response_review_thread = MagicMock()
        mock_external_issue_response_review_thread.json.return_value = {
            'body': 'External context #2.'
        }

        mock_get.side_effect = [
            mock_prs_response,  # First call for PRs
            mock_empty_response,  # Second call for PRs (empty page)
            mock_comments_response,  # Third call for PR comments
            mock_empty_response,  # Fourth call for PR comments (empty page)
            mock_external_issue_response_in_body,
            mock_external_issue_response_review_thread,
        ]

        # Mock the post request for GraphQL
        with patch('requests.post') as mock_post:
            mock_post.return_value = mock_graphql_response

            # Create an instance of PRHandler
            llm_config = LLMConfig(model='test', api_key='test')
            handler = PRHandler('test-owner', 'test-repo', 'test-token', llm_config)

            # Get converted issues
            prs = handler.get_converted_issues(
                issue_numbers=[1], comment_id=specific_comment_id
            )

            # Verify that we got exactly one PR
            assert len(prs) == 1

            # Verify that thread_comments are set correctly
            assert prs[0].thread_comments is None
            assert prs[0].review_comments == []
            assert len(prs[0].review_threads) == 1
            assert isinstance(prs[0].review_threads[0], ReviewThread)
            assert (
                prs[0].review_threads[0].comment
                == 'Specific review comment that references #6\n---\nlatest feedback:\nAnother review comment referencing #7\n'
            )
            assert prs[0].closing_issues == [
                'External context #1.',
                'External context #2.',
            ]  # Only includes references inside comment ID and body PR

            # Verify other fields are set correctly
            assert prs[0].number == 1
            assert prs[0].title == 'Test PR fixes #3'
            assert prs[0].body == 'Test Body'
            assert prs[0].owner == 'test-owner'
            assert prs[0].repo == 'test-repo'
            assert prs[0].head_branch == 'test-branch'


def test_pr_handler_get_converted_issues_with_duplicate_issue_refs():
    # Mock the necessary dependencies
    with patch('requests.get') as mock_get:
        # Mock the response for PRs
        mock_prs_response = MagicMock()
        mock_prs_response.json.return_value = [
            {
                'number': 1,
                'title': 'Test PR',
                'body': 'Test Body fixes #1',
                'head': {'ref': 'test-branch'},
            }
        ]

        # Mock the response for PR comments
        mock_comments_response = MagicMock()
        mock_comments_response.json.return_value = [
            {'body': 'First comment addressing #1'},
            {'body': 'Second comment addressing #2'},
        ]

        # Mock the response for PR metadata (GraphQL)
        mock_graphql_response = MagicMock()
        mock_graphql_response.json.return_value = {
            'data': {
                'repository': {
                    'pullRequest': {
                        'closingIssuesReferences': {'edges': []},
                        'reviews': {'nodes': []},
                        'reviewThreads': {'edges': []},
                    }
                }
            }
        }

        # Set up the mock to return different responses
        # We need to return empty responses for subsequent pages
        mock_empty_response = MagicMock()
        mock_empty_response.json.return_value = []

        # Mock the response for fetching the external issue referenced in PR body
        mock_external_issue_response_in_body = MagicMock()
        mock_external_issue_response_in_body.json.return_value = {
            'body': 'External context #1.'
        }

        # Mock the response for fetching the external issue referenced in review thread
        mock_external_issue_response_in_comment = MagicMock()
        mock_external_issue_response_in_comment.json.return_value = {
            'body': 'External context #2.'
        }

        mock_get.side_effect = [
            mock_prs_response,  # First call for PRs
            mock_empty_response,  # Second call for PRs (empty page)
            mock_comments_response,  # Third call for PR comments
            mock_empty_response,  # Fourth call for PR comments (empty page)
            mock_external_issue_response_in_body,  # Mock response for the external issue reference #1
            mock_external_issue_response_in_comment,
        ]

        # Mock the post request for GraphQL
        with patch('requests.post') as mock_post:
            mock_post.return_value = mock_graphql_response

            # Create an instance of PRHandler
            llm_config = LLMConfig(model='test', api_key='test')
            handler = PRHandler('test-owner', 'test-repo', 'test-token', llm_config)

            # Get converted issues
            prs = handler.get_converted_issues(issue_numbers=[1])

            # Verify that we got exactly one PR
            assert len(prs) == 1

            # Verify that thread_comments are set correctly
            assert prs[0].thread_comments == [
                'First comment addressing #1',
                'Second comment addressing #2',
            ]

            # Verify other fields are set correctly
            assert prs[0].number == 1
            assert prs[0].title == 'Test PR'
            assert prs[0].body == 'Test Body fixes #1'
            assert prs[0].owner == 'test-owner'
            assert prs[0].repo == 'test-repo'
            assert prs[0].head_branch == 'test-branch'
            assert prs[0].closing_issues == [
                'External context #1.',
                'External context #2.',
            ]
