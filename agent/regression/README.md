# Regression Tests

These files demonstrate how OpenDevin currently handles certain scenarios.

To add a new regression case:
```bash
mkdir -p ./agent/regression/cases/$name/workspace
echo "write a hello world script" >> ./agent/regression/cases/$name/task.txt
TEST_CASE=$name ./agent/regression/run.sh
```
