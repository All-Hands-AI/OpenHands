#!/bin/bash

# Get the Python executable
PYTHON_EXE=$(which python)

# Run the team CLI
$PYTHON_EXE -m openhands.cli.team "$@"
