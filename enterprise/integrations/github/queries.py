PR_QUERY_BY_NODE_ID = """
query($nodeId: ID!, $pr_number: Int!, $commits_after: String, $comments_after: String, $reviews_after: String) {
    node(id: $nodeId) {
        ... on Repository {
            name
            owner {
                login
            }
            languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
                nodes {
                    name
                }
            }
            pullRequest(number: $pr_number) {
                number
                title
                body
                author {
                    login
                }
                merged
                mergedAt
                mergedBy {
                    login
                }
                state
                mergeCommit {
                    oid
                }
                comments(first: 50, after: $comments_after) {
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                    nodes {
                        author {
                            login
                        }
                        body
                        createdAt
                    }
                }
                commits(first: 50, after: $commits_after) {
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                    nodes {
                        commit {
                            oid
                            message
                            committedDate
                            author {
                                name
                                email
                                user {
                                    login
                                }
                            }
                            additions
                            deletions
                            changedFiles
                        }
                    }
                }
                reviews(first: 50, after: $reviews_after) {
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                    nodes {
                        author {
                            login
                        }
                        body
                        state
                        createdAt
                        comments(first: 50) {
                            pageInfo {
                                hasNextPage
                                endCursor
                            }
                            nodes {
                                author {
                                    login
                                }
                                body
                                createdAt
                            }
                        }
                    }
                }
            }
        }
    }
    rateLimit {
        remaining
        limit
        resetAt
    }
}
"""
