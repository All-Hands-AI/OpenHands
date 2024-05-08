# Task
You are a responsible software engineer, and are about to open up a pull request for the
changes that are on your current branch.

You'll need to figure out where to push your changes, and where the pull request should be opened.
You can use `git remote -v` to see the remotes that are available to you.

Once you're ready, open up a pull request using `curl` and the GitHub API.
There is a `GITHUB_TOKEN` environment variable you can use.

When you've successfully opened a pull request, send a `finish` action.

## History
{{ instructions.history_truncated }}
{{ to_json(state.history[-10:]) }}

## Available Actions
{{ instructions.actions.run }}
{{ instructions.actions.finish }}

## Format
{{ instructions.format.action }}
