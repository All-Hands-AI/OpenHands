#!/bin/bash

cd /home/agent
/opt/conda/bin/conda run -n agent --no-capture-output make build
sudo -u nonroot /opt/conda/bin/conda run -n agent --no-capture-output playwright install
