---
name: add_openhands_repo_instruction
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
- /add_openhands_repo_instruction
---

I need to add repository-specific instructions to the OpenHands repository. Please provide the following information:

1. Repository name: ${repo_name}
2. Repository directory: ${repo_directory}
3. Repository structure: ${repo_structure}
4. Common commands (build, lint, test, pre-commit, etc.): ${common_commands}
5. Code style preferences: ${code_style_preferences}
6. Workflows and best practices: ${workflows_and_best_practices}

If the user didn't provide any of these variables, ask the user to provide them first before the agent can proceed with the task.

I'll use this information to create or update the `.openhands/microagents/repo.md` file in the repository with the provided details. This will help future agents understand the repository better and provide more accurate assistance.

The repository instructions should be organized in a clear and structured way, with sections for each type of information. I'll make sure to format the instructions properly and include all the relevant details.

Once I have all the necessary information, I'll create or update the repository instructions file and provide a summary of the changes made.