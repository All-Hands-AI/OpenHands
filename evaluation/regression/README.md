# Regression Tests

These files demonstrate how OpenDevin currently handles certain scenarios.

To add a new regression case:
```bash
name="hello-script"

# The start directory contains the initial state of the project the agent will work on
# Add any files you'd like here.
mkdir -p ./agent/regression/cases/$name/start

# task.txt contains the task to be accomplished
echo "write a hello world script" >> ./agent/regression/cases/$name/task.txt

# Single out your test case using the TEST_CASE environment variable
TEST_CASE=$name ./agent/regression/run.sh
```
