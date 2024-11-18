#!/bin/bash

# Print commands and their arguments as they are executed
set -x

{
  # log into /home/logs
  LOGS_DIR=/home/logs
  mkdir -p $LOGS_DIR

  # chmod the /home directory such that nonroot users can work on everything within it. We do this at container start
  # time so that anything added later in agent-specific Dockerfiles will also receive the correct permissions.
  # (this command does `chmod a+rw /home` but with the exception of /home/data, which is a read-only volume)
  find /home -path /home/data -prune -o -exec chmod a+rw {} \;
  ls -l /home

  # Launch grading server, stays alive throughout container lifetime to service agent requests.
  /opt/conda/bin/python /private/grading_server.py
} 2>&1 | tee $LOGS_DIR/entrypoint.log
