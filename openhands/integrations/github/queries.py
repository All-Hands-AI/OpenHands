suggested_task_pr_graphql_query = """
    query GetUserPRs($login: String!) {
        user(login: $login) {
        pullRequests(first: 50, states: [OPEN], orderBy: {field: UPDATED_AT, direction: DESC}) {
            nodes {
            number
            title
            repository {
                nameWithOwner
            }
            mergeable
            commits(last: 1) {
                nodes {
                commit {
                    statusCheckRollup {
                        state
                    }
                }
                }
            }
            reviews(first: 50, states: [CHANGES_REQUESTED, COMMENTED]) {
                nodes {
                state
                }
            }
            }
        }
        }
    }
"""


suggested_task_issue_graphql_query = """
    query GetUserIssues($login: String!) {
        user(login: $login) {
        issues(first: 50, states: [OPEN], filterBy: {assignee: $login}, orderBy: {field: UPDATED_AT, direction: DESC}) {
            nodes {
            number
            title
            repository {
                nameWithOwner
                }
            }
        }
        }
    }
"""

get_thread_from_comment_graphql_query = """
    query GetThreadFromComment($commentId: ID!) {
        node(id: $commentId) {
            ... on PullRequestReviewComment {
                id
                body
                author {
                    login
                }
                createdAt
                updatedAt
                replyTo {
                    id
                    body
                    author {
                        login
                    }
                    createdAt
                    updatedAt
                }
            }
        }
    }
"""
