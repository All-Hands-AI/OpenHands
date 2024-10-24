# CLI Mode

OpenHands can be run in an interactive CLI mode, which allows users to start an interactive session via the command line.

This mode is different from the [headless mode](headless-mode), which is non-interactive and better for scripting.

## With Python

To start an interactive OpenHands session via the command line, follow these steps:

1. Ensure you have followed the [Development setup instructions](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md).

2. Run the following command:

```bash
poetry run python -m openhands.core.cli
```

This command will start an interactive session where you can input tasks and receive responses from OpenHands.

You'll need to be sure to set your model, API key, and other settings via environment variables
[or the `config.toml` file](https://github.com/All-Hands-AI/OpenHands/blob/main/config.template.toml).


## With Docker

To run OpenHands in CLI mode with Docker, set your LLM options, then run
the Docker command from the README, followed by the command
`python -m openhands.core.cli`.

```bash
export LLM_MODEL="anthropic/claude-3-5-sonnet-20240620"
export LLM_API_KEY="sk_test_12345"

docker run # ...
    -e LLM_API_KEY=$LLM_API_KEY \
    -e LLM_MODEL=$LLM_MODEL \
    # ...
    python -m openhands.core.cli
```

This command will start an interactive session in Docker where you can input tasks and receive responses from OpenHands.

## Examples of CLI Commands and Expected Outputs

Here are some examples of CLI commands and their expected outputs:

### Example 1: Simple Task

```bash
How can I help? >> Write a Python script that prints "Hello, World!"
```

Expected Output:

```bash
🤖 Sure! Here is a Python script that prints "Hello, World!":

❯ print("Hello, World!")
```

### Example 2: Bash Command

```bash
How can I help? >> Create a directory named "test_dir"
```

Expected Output:

```bash
🤖 Creating a directory named "test_dir":

❯ mkdir test_dir
```

### Example 3: Error Handling

```bash
How can I help? >> Delete a non-existent file
```

Expected Output:

```bash
🤖 An error occurred. Please try again.
```
