---
name: get_test_to_pass
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
- /fix_test
---

I'll help you fix failing tests in your codebase. Please provide the following information:

1. Test file path: ${test_file_path}
2. Implementation file path (if known): ${implementation_file_path}
3. Error message or failure details: ${error_message}
4. Repository name: ${repo_name}

If the user didn't provide any of these variables, ask the user to provide them first before the agent can proceed with the task.

I'll follow these steps to fix the failing test:

1. Examine the test file to understand what's being tested
2. Look at the implementation file to understand the current code
3. Analyze the error message to identify the specific issue
4. Make the necessary changes to fix the test
5. Run the test to verify that it passes
6. Explain the changes made and why they fix the issue

My approach will be:
- First understand the test requirements and expected behavior
- Identify the root cause of the failure
- Make minimal changes to fix the issue while maintaining the intended functionality
- Ensure the fix doesn't break other tests or functionality
- Document the changes and explain the reasoning

I'll keep you updated throughout the process and let you know when the test is passing.