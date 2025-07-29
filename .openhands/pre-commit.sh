#!/bin/bash

echo "Running OpenHands pre-commit hook..."
echo "@happyherp: I wonder if this actually is called from anywhere...."
EXIT_CODE=1

# Store the exit code to return at the end
# This allows us to be additive to existing pre-commit hooks
if [ $EXIT_CODE -eq 0 ]; then
    echo "All pre-commit checks passed!"
else
    echo "Some pre-commit checks failed. Please fix the issues before committing."
fi
echo "FAIL ON PURPOSE. THIS IS A TEST"
exit $EXIT_CODE
