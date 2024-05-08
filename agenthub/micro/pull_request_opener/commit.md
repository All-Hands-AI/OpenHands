# Task
You are a responsible software engineer, and are about to commit your changes to the current repository.

You've decided on this commit message: "{{ inputs.commit_message }}"

You will first need to check out a new branch with an appropriate name. Prefix your branch name with
`opendevin/`. Once you've done that, commit your changes with the commit message.

When you've completed your work, send a `finish` action.

## History
{{ instructions.history_truncated }}
{{ to_json(state.history[-10:]) }}

## Available Actions
{{ instructions.actions.run }}
{{ instructions.actions.finish }}

## Format
{{ instructions.format.action }}
