---
name: get_test_to_pass
version: 1.0.0
author: openhands
agent: CodeActAgent
triggers:
- /fix_test
inputs:
  - name: BRANCH_NAME
    description: "Branch for the agent to work on"
  - name: TEST_COMMAND_TO_RUN
    description: "The test command you want the agent to work on. For example, `pytest tests/unit/test_bash_parsing.py`"
  - name: FUNCTION_TO_FIX
    description: "The name of function to fix"
  - name: FILE_FOR_FUNCTION
    description: "The path of the file that contains the function"
---

Can you check out branch "{{ BRANCH_NAME }}", and run {{ TEST_COMMAND_TO_RUN }}.

{%- if FUNCTION_TO_FIX and FILE_FOR_FUNCTION %}
Help me fix these tests to pass by fixing the {{ FUNCTION_TO_FIX }} function in file {{ FILE_FOR_FUNCTION }}.
{%- endif %}

PLEASE DO NOT modify the tests by yourselves -- Let me know if you think some of the tests are incorrect.
