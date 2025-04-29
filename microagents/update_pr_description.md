---
name: update_pr_description
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
- /update_pr_description
---

I'll help you update a pull request description with comprehensive information. Please provide the following details:

1. Pull request URL: ${pr_url}
2. Repository name: ${repo_name}
3. Branch name: ${branch_name}
4. Summary of changes: ${summary_of_changes}
5. Testing performed: ${testing_performed}
6. Related issues (if any): ${related_issues}

If the user didn't provide any of these variables, ask the user to provide them first before the agent can proceed with the task.

I'll create a well-structured PR description that includes:

1. **Overview**: A clear summary of what the PR accomplishes
2. **Changes**: A detailed list of the changes made
3. **Testing**: Description of tests performed and results
4. **Related Issues**: Links to any related issues or tickets
5. **Screenshots/Videos**: If applicable, visual evidence of the changes
6. **Additional Notes**: Any other relevant information

I'll use the GitHub API to update the PR description with this information. The description will be formatted in Markdown for readability.

I'll also check if there are any PR templates in the repository and ensure the updated description follows the template structure if one exists.