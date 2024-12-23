# Prompting Best Practices

When working with OpenHands AI software developer, it's crucial to provide clear and effective prompts. This guide outlines best practices for creating prompts that will yield the most accurate and useful responses.

## Table of Contents

- [Characteristics of Good Prompts](#characteristics-of-good-prompts)
- [Customizing Prompts for your Project](#customizing-prompts-for-your-project)

## Characteristics of Good Prompts

Good prompts are:

1. **Concrete**: They explain exactly what functionality should be added or what error needs to be fixed.
2. **Location-specific**: If known, they explain the locations in the code base that should be modified.
3. **Appropriately scoped**: They should be the size of a single feature, typically not exceeding 100 lines of code.

## Examples

### Good Prompt Examples

1. "Add a function `calculate_average` in `utils/math_operations.py` that takes a list of numbers as input and returns their average."

2. "Fix the TypeError in `frontend/src/components/UserProfile.tsx` occurring on line 42. The error suggests we're trying to access a property of undefined."

3. "Implement input validation for the email field in the registration form. Update `frontend/src/components/RegistrationForm.tsx` to check if the email is in a valid format before submission."

### Bad Prompt Examples

1. "Make the code better." (Too vague, not concrete)

2. "Rewrite the entire backend to use a different framework." (Not appropriately scoped)

3. "There's a bug somewhere in the user authentication. Can you find and fix it?" (Lacks specificity and location information)

## Tips for Effective Prompting

1. Be as specific as possible about the desired outcome or the problem to be solved.
2. Provide context, including relevant file paths and line numbers if available.
3. Break down large tasks into smaller, manageable prompts.
4. Include any relevant error messages or logs.
5. Specify the programming language or framework if it's not obvious from the context.

Remember, the more precise and informative your prompt is, the better the AI can assist you in developing or modifying the OpenHands software.

See [Getting Started with OpenHands](./getting-started) for more examples of helpful prompts.

## Customizing Prompts for your Project

OpenHands can be customized to work more effectively with specific repositories by providing repository-specific context and guidelines. This section explains how to optimize OpenHands for your project.

### Repository Configuration

You can customize OpenHands' behavior for your repository by creating a `.openhands_instructions` file in your repository's root directory. This file should contain:

1. **Repository Overview**: A brief description of your project's purpose and architecture
2. **Directory Structure**: Key directories and their purposes
3. **Development Guidelines**: Project-specific coding standards and practices
4. **Testing Requirements**: How to run tests and what types of tests are required
5. **Setup Instructions**: Steps needed to build and run the project

Example `.openhands_instructions` file:
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

1. **Keep Instructions Updated**: Regularly update your `.openhands_instructions` file as your project evolves
2. **Be Specific**: Include specific paths, patterns, and requirements unique to your project
3. **Document Dependencies**: List all tools and dependencies required for development
4. **Include Examples**: Provide examples of good code patterns from your project
5. **Specify Conventions**: Document naming conventions, file organization, and code style preferences

By customizing OpenHands for your repository, you'll get more accurate and consistent results that align with your project's standards and requirements.
