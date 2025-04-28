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
