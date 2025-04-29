---
name: address_pr_comments
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
- /address_pr_comments
---

I'll help you address comments on a pull request. Please provide the following information:

1. Pull request URL: ${pr_url}
2. Repository name: ${repo_name}
3. Branch name: ${branch_name}
4. Specific comments to address (optional): ${specific_comments}

If the user didn't provide any of these variables, ask the user to provide them first before the agent can proceed with the task.

I'll follow these steps to address the PR comments:

1. Examine the pull request to understand the context and the changes made
2. Review all comments on the PR, focusing on the ones specified (if any)
3. Make the necessary changes to address each comment
4. Commit and push the changes to the same branch
5. Respond to each comment on GitHub explaining how it was addressed

For each comment, I'll:
- Understand the feedback and what changes are needed
- Make the required code changes
- Test the changes to ensure they work as expected
- Commit with a clear message referencing the comment
- Reply to the comment explaining what was done

I'll keep you updated throughout the process and let you know when all comments have been addressed.