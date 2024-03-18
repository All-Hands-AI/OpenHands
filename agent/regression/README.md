# Regression Tests

These files demonstrate how OpenDevin currently handles certain scenarios.

To add a new regression case:
```bash
# The start directory contains the initial state of the project the agent will work on
mkdir -p ./agent/regression/cases/$name/start

# The workspace will begin as a copy of the start directory, and is where the agent will do its work
mkdir -p ./agent/regression/cases/$name/workspace

# task.txt contains the task to be accomplished
echo "write a hello world script" >> ./agent/regression/cases/$name/task.txt

# Single out your test case using the TEST_CASE environment variable
TEST_CASE=$name ./agent/regression/run.sh
```
