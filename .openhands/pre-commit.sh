#!/bin/bash

echo "Running OpenHands pre-commit hook..."

# Check if frontend directory has changed
frontend_changes=$(git diff --cached --name-only | grep "^frontend/")
if [ -n "$frontend_changes" ]; then
    echo "Frontend changes detected. Running frontend checks..."

    # Check if frontend directory exists
    if [ -d "frontend" ]; then
        # Change to frontend directory
        cd frontend || exit 1

        # Run lint:fix
        echo "Running npm lint:fix..."
        npm run lint:fix
        if [ $? -ne 0 ]; then
            echo "Frontend linting failed. Please fix the issues before committing."
            exit 1
        fi

        # Run build
        echo "Running npm build..."
        npm run build
        if [ $? -ne 0 ]; then
            echo "Frontend build failed. Please fix the issues before committing."
            exit 1
        fi

        # Run tests
        echo "Running npm test..."
        npm test
        if [ $? -ne 0 ]; then
            echo "Frontend tests failed. Please fix the failing tests before committing."
            exit 1
        fi

        # Return to the original directory
        cd ..

        echo "Frontend checks passed!"
    else
        echo "Frontend directory not found. Skipping frontend checks."
    fi
else
    echo "No frontend changes detected. Skipping frontend checks."
fi

echo "Pre-commit checks passed!"
exit 0
