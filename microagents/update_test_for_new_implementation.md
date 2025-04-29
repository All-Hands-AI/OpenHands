---
name: update_test_for_new_implementation
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
- /update_test
---

I'll help you update tests to match a new implementation. Please provide the following information:

1. Test file path: ${test_file_path}
2. Implementation file path: ${implementation_file_path}
3. Description of implementation changes: ${implementation_changes}
4. Repository name: ${repo_name}

If the user didn't provide any of these variables, ask the user to provide them first before the agent can proceed with the task.

I'll follow these steps to update the tests:

1. Examine the implementation file to understand the changes made
2. Review the existing test file to see what needs to be updated
3. Update the tests to match the new implementation while maintaining test coverage
4. Run the tests to ensure they pass with the new implementation
5. Explain the changes made to the tests and how they align with the implementation changes

My approach will be:
- Understand both the old and new implementation to identify what's changed
- Update test cases to reflect the new behavior while maintaining coverage
- Add new tests for any new functionality
- Remove or modify tests that no longer apply
- Ensure all tests pass with the new implementation
- Document the changes made to the tests

I'll keep you updated throughout the process and let you know when the tests are successfully updated.