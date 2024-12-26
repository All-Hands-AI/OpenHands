# Customizing Agent Behavior

OpenHands can be customized to work more effectively with specific repositories by providing repository-specific context and guidelines. This section explains how to optimize OpenHands for your project.

## Repository Configuration

You can customize OpenHands' behavior for your repository by creating a `.openhands` directory in your repository's root. At minimum, it should contain the file
`.openhands/microagents/repo.md`, which includes instructions that will
be given to the agent every time it works with this repository.

We suggest including the following information:
1. **Repository Overview**: A brief description of your project's purpose and architecture
2. **Directory Structure**: Key directories and their purposes
3. **Development Guidelines**: Project-specific coding standards and practices
4. **Testing Requirements**: How to run tests and what types of tests are required
5. **Setup Instructions**: Steps needed to build and run the project

### Example Repository Configuration
Example `.openhands/microagents/repo.md` file:
```
Repository: MyProject
Description: A web application for task management

Directory Structure:
- src/: Main application code
- tests/: Test files
- docs/: Documentation

Setup:
- Run `npm install` to install dependencies
- Use `npm run dev` for development
- Run `npm test` for testing

Guidelines:
- Follow ESLint configuration
- Write tests for all new features
- Use TypeScript for new code
```

### Customizing Prompts

When working with a customized repository:

1. **Reference Project Standards**: Mention specific coding standards or patterns used in your project
2. **Include Context**: Reference relevant documentation or existing implementations
3. **Specify Testing Requirements**: Include project-specific testing requirements in your prompts

Example customized prompt:
```
Add a new task completion feature to src/components/TaskList.tsx following our existing component patterns.
Include unit tests in tests/components/ and update the documentation in docs/features/.
The component should use our shared styling from src/styles/components.
```

### Best Practices for Repository Customization

1. **Keep Instructions Updated**: Regularly update your `.openhands` directory as your project evolves
2. **Be Specific**: Include specific paths, patterns, and requirements unique to your project
3. **Document Dependencies**: List all tools and dependencies required for development
4. **Include Examples**: Provide examples of good code patterns from your project
5. **Specify Conventions**: Document naming conventions, file organization, and code style preferences

By customizing OpenHands for your repository, you'll get more accurate and consistent results that align with your project's standards and requirements.

## Other Microagents
You can create other instructions in the `.openhands/microagents/` directory
that will be sent to the agent if a particular keyword is found, like `test`, `frontend`, or `migration`. See [Microagents](microagents.md) for more information.
