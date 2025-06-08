---
inputs:
- description: Branch for the agent to work on
  name: BRANCH_NAME
- description: The test command you want the agent to work on. For example, `pytest
    tests/unit/test_bash_parsing.py`
  name: TEST_COMMAND_TO_RUN
name: update_test
triggers:
- /update_test
---

Can you check out branch "{{ BRANCH_NAME }}", and run {{ TEST_COMMAND_TO_RUN }}.

The current implementation of the code is correct BUT the test functions {{ FUNCTION_TO_FIX }} in file {{ FILE_FOR_FUNCTION }} are failing.

Please update the test file so that they pass with the current version of the implementation.