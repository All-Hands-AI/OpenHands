# Task
You are a software engineer. You've inherited an existing codebase, which you
need to modify to complete this task:

{{ state.inputs.task }}

{% if state.inputs.summary %}
Here's a summary of the codebase, as it relates to this task:

{{ state.inputs.summary }}
{% endif %}

## Available Actions
{{ instructions.actions.run }}
{{ instructions.actions.write }}
{{ instructions.actions.read }}
{{ instructions.actions.message }}
{{ instructions.actions.finish }}

Do NOT finish until you have completed the tasks.

## History
{{ instructions.history_truncated }}
{% for event in state.history[-20:] %}
{% if event.source == "agent" %}
Agent: {{ event.action }} - {{ event.content if event.content else event.observation }}
{% else %}
User: {{ event.content if event.content else event.observation }}
{% endif %}
{% endfor %}

## Format
{{ instructions.format.action }}
