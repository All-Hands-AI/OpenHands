get_review_thread_comments_query = """
    query($id: ID!, $first: Int!) {
        node(id: $id) {
        ... on Discussion {
            notes(first: $first) {
            nodes {
                id
                body
                system
                author { username }
                createdAt
                updatedAt
            }
            }
        }
        }
    }
"""
