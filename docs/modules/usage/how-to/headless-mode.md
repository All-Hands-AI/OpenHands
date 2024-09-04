# Running in Headless Mode

You can run OpenHands via a CLI, without starting the web application. This makes it easy to automate tasks with OpenHands.

## Difference Between CLI Mode and Headless Mode

- **CLI Mode**: Interactive mode where users can input tasks and receive responses in real-time. It is suitable for users who prefer or require a command-line interface.
- **Headless Mode**: Non-interactive mode where tasks are executed without user interaction. It is suitable for automation and scripting purposes.

For more information on CLI mode, refer to the [CLI Mode documentation](./cli-mode.md).

As with other modes, the environment is configurable via environment variables or by saving values into [config.toml](https://github.com/All-Hands-AI/OpenHands/blob/main/config.template.toml)

## With Python

To run OpenHands in headless mode with Python,
[follow the Development setup instructions](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md),
and then run:

### Headless with Python

```bash
poetry run python -m openhands.core.main -t "write a bash script that prints hi"
```
