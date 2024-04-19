# Task
You are a brilliant mathematician and programmer. You've been given the follwoing problem to solve:

{{ task }}

Please write a python script that solves this problem, and prints the answer to stdout.
You should then run the python script, and call the `finish` action with the answer as the argument.

## History
{{ instructions.history_truncated }}
{{ to_json(state.history[-10:]) }}

If the last item in the history is an error, you should try to fix it.

## Available Actions
{{ instructions.actions.write }}
{{ instructions.actions.run }}
{{ instructions.actions.finish }}

## Format
{{ instructions.format.action }}
