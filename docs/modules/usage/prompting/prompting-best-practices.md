# Prompting Best Practices

When working with OpenHands AI software developer, providing clear and effective prompts is key to getting accurate
and useful responses. This guide outlines best practices for crafting effective prompts.

## Characteristics of Good Prompts

Good prompts are:

- **Concrete**: Clearly describe what functionality should be added or what error needs fixing.
- **Location-specific**: Specify the locations in the codebase that should be modified, if known.
- **Appropriately scoped**: Focus on a single feature, typically not exceeding 100 lines of code.

## Examples

### Good Prompt Examples

- Add a function `calculate_average` in `utils/math_operations.py` that takes a list of numbers as input and returns their average.
- Fix the TypeError in `frontend/src/components/UserProfile.tsx` occurring on line 42. The error suggests we're trying to access a property of undefined.
- Implement input validation for the email field in the registration form. Update `frontend/src/components/RegistrationForm.tsx` to check if the email is in a valid format before submission.

### Bad Prompt Examples

- Make the code better. (Too vague, not concrete)
- Rewrite the entire backend to use a different framework. (Not appropriately scoped)
- There's a bug somewhere in the user authentication. Can you find and fix it? (Lacks specificity and location information)

## Tips for Effective Prompting

- Be as specific as possible about the desired outcome or the problem to be solved.
- Provide context, including relevant file paths and line numbers if available.
- Break large tasks into smaller, manageable prompts.
- Include relevant error messages or logs.
- Specify the programming language or framework, if not obvious.

The more precise and informative your prompt, the better OpenHands can assist you.

See [Getting Started with OpenHands](../getting-started) for more examples of helpful prompts.
