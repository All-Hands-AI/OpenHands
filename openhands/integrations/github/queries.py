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


# Search branches in a repository by partial name using GitHub GraphQL.
# This leverages the `refs` connection with:
# - refPrefix: "refs/heads/" to restrict to branches
# - query: partial branch name provided by the user
# - first: pagination size (clamped by caller to GitHub limits)
search_branches_graphql_query = """
    query SearchBranches($owner: String!, $name: String!, $query: String!, $perPage: Int!) {
        repository(owner: $owner, name: $name) {
            refs(
                refPrefix: "refs/heads/",
                query: $query,
                first: $perPage,
                orderBy: { field: ALPHABETICAL, direction: ASC }
            ) {
                nodes {
                    name
                    branchProtectionRule { id }
                    target {
                        __typename
                        ... on Commit {
                            oid
                            committedDate
                        }
                    }
                }
            }
        }
    }
"""
