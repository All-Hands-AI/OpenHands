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

pr_review_thread_comments_graphql_query = """
    query GetPRReviewThreadComments($owner: String!, $name: String!, $number: Int!) {
        repository(owner: $owner, name: $name) {
            pullRequest(number: $number) {
                reviewThreads(first: 100) {
                    nodes {
                        id
                        comments(first: 100) {
                            nodes {
                                id
                                databaseId
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
            }
        }
    }
"""
