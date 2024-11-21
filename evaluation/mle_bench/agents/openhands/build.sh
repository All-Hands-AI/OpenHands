#!/bin/bash

cd /home/agent

# The final configuration for the agent happens here, otherwise the standard entrypoint hangs while
# all the build artifacts are being recursively chmod'ed.

/opt/conda/bin/conda run -n agent --no-capture-output make build
# sudo -u nonroot /opt/conda/bin/conda run -n agent --no-capture-output playwright install
