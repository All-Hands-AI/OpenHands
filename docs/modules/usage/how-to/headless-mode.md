# Headless Mode

You can run OpenHands with a single command, without starting the web application.
This makes it easy to write scripts and automate tasks with OpenHands.

This is different from [CLI Mode](cli-mode), which is interactive, and better for active development.

## With Python

To run OpenHands in headless mode with Python,
[follow the Development setup instructions](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md),
and then run:

```bash
poetry run python -m openhands.core.main -t "write a bash script that prints hi"
```

You'll need to be sure to set your model, API key, and other settings via environment variables
[or the `config.toml` file](https://github.com/All-Hands-AI/OpenHands/blob/main/config.template.toml).

## With Docker

1. Set `WORKSPACE_BASE` to the directory you want OpenHands to edit:

```bash
WORKSPACE_BASE=$(pwd)/workspace
```

2. Set `LLM_MODEL` to the model you want to use:

```bash
LLM_MODEL="claude-3-5-sonnet-20240620"
```

3. Set `LLM_API_KEY` to an API key, e.g., for OpenAI or Anthropic:

```bash
LLM_API_KEY="abcde"
```

4. Run the following Docker command:

```bash
poetry run python -m openhands.core.main -t "write a bash script that prints hi"
```
