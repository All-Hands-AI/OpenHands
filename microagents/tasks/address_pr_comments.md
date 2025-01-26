---
name: address_pr_comments
type: task
version: 1.0.0
author: openhands
agent: CodeActAgent
inputs:
  - name: PR_URL
    description: "URL of the pull request"
    required: true
  - name: BRANCH_NAME
    description: "Branch name corresponds to the pull request"
    required: true
---

First, check the branch {{ BRANCH_NAME }} and read the diff against the main branch to understand the purpose.

This branch corresponds to this PR {{ PR_URL }}

Next, you should use the GitHub API to read the reviews and comments on this PR and address them.
