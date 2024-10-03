# Prompting Best Practices

When working with OpenHands AI software developer, it's crucial to provide clear and effective prompts. This guide outlines best practices for creating prompts that will yield the most accurate and useful responses.

## Characteristics of Good Prompts

Good prompts are:

1. **Concrete**: They explain exactly what functionality should be added or what error needs to be fixed.
2. **Location-specific**: If known, they explain the locations in the code base that should be modified.
3. **Appropriately scoped**: They should be the size of a single feature, typically not exceeding 100 lines of code.

## Examples of Good Prompts

1. "Add a function `calculate_average` in the file `/workspace/openhands/utils/math_operations.py` that takes a list of numbers as input and returns their average."

2. "Fix the TypeError in the `process_user_input` function in `/workspace/frontend/src/components/UserInput.tsx`. The error occurs when passing a string instead of a number to the `processData` function."

3. "Implement input validation for the email field in the user registration form. Update the file `/workspace/frontend/src/components/RegistrationForm.tsx` to include this validation before form submission."

## Examples of Bad Prompts

1. "Make the code better." (Too vague and not concrete)

2. "Rewrite the entire backend to use a different framework." (Not appropriately scoped)

3. "Fix all the bugs in the project." (Not concrete, not location-specific, and not appropriately scoped)

## Tips for Writing Effective Prompts

1. Be as specific as possible about the desired outcome or the problem to be solved.
2. Provide context, including relevant file paths and function names.
3. Break down large tasks into smaller, manageable prompts.
4. Include any relevant error messages or logs if you're asking for a bug fix.
5. Specify the programming language and any relevant libraries or frameworks being used.

Remember, the more precise and detailed your prompt is, the better the chances of getting an accurate and helpful response from the OpenHands AI software developer.
