---
sidebar_label: github
title: opendevin.events.action.github
---

## GitHubPushAction Objects

```python
@dataclass
class GitHubPushAction(Action)
```

This pushes the current branch to github.

To use this, you need to set the GITHUB_TOKEN environment variable.
The agent will return a message with a URL that you can click to make a pull
request.

**Attributes**:

- `owner` - The owner of the source repo
- `repo` - The name of the source repo
- `branch` - The branch to push
- `action` - The action identifier

## GitHubSendPRAction Objects

```python
@dataclass
class GitHubSendPRAction(Action)
```

An action to send a github PR.

To use this, you need to set the GITHUB_TOKEN environment variable.

**Attributes**:

- `owner` - The owner of the source repo
- `repo` - The name of the source repo
- `title` - The title of the PR
- `head` - The branch to send the PR from
- `head_repo` - The repo to send the PR from
- `base` - The branch to send the PR to
- `body` - The body of the PR

