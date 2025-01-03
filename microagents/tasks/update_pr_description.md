---
name: update_pr_description
type: task
version: 1.0.0
author: openhands
agent: CodeActAgent
inputs:
  - name: PR_URL
    description: "URL of the pull request"
    type: string
    required: true
    validation:
      pattern: "^https://github.com/.+/.+/pull/[0-9]+$"
  - name: BRANCH_NAME
    description: "Branch name corresponds to the pull request"
    type: string
    required: true
---

Please check the branch "{{ BRANCH_NAME }}" and look at the diff against the main branch. This branch belongs to this PR "{{ PR_URL }}".

Once you understand the purpose of the diff, please use Github API to read the existing PR description, and update it to be more reflective of the changes we've made when necessary.
