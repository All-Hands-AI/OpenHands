---
inputs:
- description: Branch for the agent to work on
  name: BRANCH_NAME
- description: The test command you want the agent to work on. For example, `pytest
    tests/unit/test_bash_parsing.py`
  name: TEST_COMMAND_TO_RUN
- description: The name of function to fix
  name: FUNCTION_TO_FIX
- description: The path of the file that contains the function
  name: FILE_FOR_FUNCTION
triggers:
- /fix_test
---

Can you check out branch "{{ BRANCH_NAME }}", and run {{ TEST_COMMAND_TO_RUN }}.

Help me fix these tests to pass by fixing the {{ FUNCTION_TO_FIX }} function in file {{ FILE_FOR_FUNCTION }}.

PLEASE DO NOT modify the tests by yourself -- Let me know if you think some of the tests are incorrect.