# Running in CLI Mode

OpenHands can be run in an interactive CLI mode, which allows users to start an interactive session via the command line. This mode is different from the headless mode, which is non-interactive.

## Starting an Interactive Session

To start an interactive OpenHands session via the command line, follow these steps:

1. Ensure you have followed the [Development setup instructions](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md).

2. Run the following command:

```bash
poetry run python -m openhands.core.cli
```

This command will start an interactive session where you can input tasks and receive responses from OpenHands.

## Difference Between CLI Mode and Headless Mode

- **CLI Mode**: Interactive mode where users can input tasks and receive responses in real-time. It is suitable for users who prefer or require a command-line interface.
- **Headless Mode**: Non-interactive mode where tasks are executed without user interaction. It is suitable for automation and scripting purposes.

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
