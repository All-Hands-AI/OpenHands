# Task
Your task is to write a sqlite database. In general, your formula for doing so is the following:

- You use your "run" ability to check if sqlite is installed, and install it if not
- You use your "run" ability to create a sqlite database
- You use your "run" ability to create a table in the database
- You use your "run" ability to insert data from a csv file into the table

Based on this formula, please follow this instruction:

{{ state.plan.main_goal }}

## Available Actions
{{ instructions.actions.run }}
{{ instructions.actions.browse }}
{{ instructions.actions.think }}
{{ instructions.actions.finish }}

## History
{{ instructions.history_truncated }}
{{ to_json(state.history[-10:]) }}

## Format
{{ instructions.format.action }}
