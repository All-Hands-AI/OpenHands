# Repository Customization

You can customize how OpenHands interacts with your repository by creating a
`.openhands` directory at the root level.

## Microagents

Microagents allow you to extend OpenHands prompts with information specific to your project and define how OpenHands
should function. See [Microagents Overview](../prompting/microagents-overview) for more information.


## Setup Script
You can add a `.openhands/setup.sh` file, which will run every time OpenHands begins working with your repository.
This is an ideal location for installing dependencies, setting environment variables, and performing other setup tasks.

For example:
```bash
#!/bin/bash
export MY_ENV_VAR="my value"
sudo apt-get update
sudo apt-get install -y lsof
cd frontend && npm install ; cd ..
```

## Pre-commit Script
You can add a `.openhands/pre-commit.sh` file to create a custom git pre-commit hook that runs before each commit.
This can be used to enforce code quality standards, run tests, or perform other checks before allowing commits.

For example:
```bash
#!/bin/bash
# Run linting checks
cd frontend && npm run lint
if [ $? -ne 0 ]; then
  echo "Frontend linting failed. Please fix the issues before committing."
  exit 1
fi

# Run tests
cd backend && pytest tests/unit
if [ $? -ne 0 ]; then
  echo "Backend tests failed. Please fix the issues before committing."
  exit 1
fi

exit 0
```
