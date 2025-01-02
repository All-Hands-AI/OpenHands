# Prompting Best Practices

When working with OpenHands AI software developer, it's crucial to provide clear and effective prompts. This guide outlines best practices for creating prompts that will yield the most accurate and useful responses.

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

See [Getting Started with OpenHands](../getting-started) for more examples of helpful prompts.
