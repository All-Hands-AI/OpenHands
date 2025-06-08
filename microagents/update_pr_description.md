---
inputs:
- description: URL of the pull request
  name: PR_URL
  type: string
  validation:
    pattern: ^https://github.com/.+/.+/pull/[0-9]+$
- description: Branch name corresponds to the pull request
  name: BRANCH_NAME
  type: string
name: update_pr_description
triggers:
- /update_pr_description
---

Please check the branch "{{ BRANCH_NAME }}" and look at the diff against the main branch. This branch belongs to this PR "{{ PR_URL }}".

Once you understand the purpose of the diff, please use Github API to read the existing PR description, and update it to be more reflective of the changes we've made when necessary.