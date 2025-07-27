#!/bin/bash

echo "Running OpenHands pre-commit hook..."
echo "This hook runs selective linting based on changed files."

# Store the exit code to return at the end
# This allows us to be additive to existing pre-commit hooks
EXIT_CODE=0

# Check what files have changed
changed_files=$(git diff --cached --name-only)
frontend_changes=$(echo "$changed_files" | grep "^frontend/")
backend_changes=$(echo "$changed_files" | grep -E "^(openhands/|evaluation/|tests/)")
vscode_extension_changes=$(echo "$changed_files" | grep "^openhands/integrations/vscode/")

# Run linting only for the parts that have changed
if [ -n "$frontend_changes" ]; then
    echo "Frontend changes detected. Running frontend linting..."
    make lint-frontend
    if [ $? -ne 0 ]; then
        echo "Frontend linting failed. Please fix the issues before committing."
        EXIT_CODE=1
    else
        echo "Frontend linting checks passed!"
    fi
fi

if [ -n "$backend_changes" ]; then
    echo "Backend changes detected. Running backend linting..."
    make lint-backend
    if [ $? -ne 0 ]; then
        echo "Backend linting failed. Please fix the issues before committing."
        EXIT_CODE=1
    else
        echo "Backend linting checks passed!"
    fi
fi

# Check for VSCode extension changes
if [ -n "$vscode_extension_changes" ]; then
    echo "VSCode extension changes detected. Running VSCode extension linting..."
    if [ -d "openhands/integrations/vscode" ]; then
        cd openhands/integrations/vscode || exit 1
        echo "Running npm lint:fix..."
        npm run lint:fix
        if [ $? -ne 0 ]; then
            echo "VSCode extension linting failed. Please fix the issues before committing."
            EXIT_CODE=1
        else
            echo "VSCode extension linting passed!"
        fi

        echo "Running npm typecheck..."
        npm run typecheck
        if [ $? -ne 0 ]; then
            echo "VSCode extension type checking failed. Please fix the issues before committing."
            EXIT_CODE=1
        else
            echo "VSCode extension type checking passed!"
        fi

        echo "Running npm compile..."
        npm run compile
        if [ $? -ne 0 ]; then
            echo "VSCode extension compilation failed. Please fix the issues before committing."
            EXIT_CODE=1
        else
            echo "VSCode extension compilation passed!"
        fi

        cd ../../..
    else
        echo "VSCode extension directory not found. Skipping VSCode extension checks."
    fi
fi

# If no specific changes detected that match our patterns, run basic checks
if [ -z "$frontend_changes" ] && [ -z "$backend_changes" ] && [ -z "$vscode_extension_changes" ]; then
    echo "No specific code changes detected. Running basic checks..."
    # Run only basic pre-commit hooks for non-code files
    if [ -n "$changed_files" ]; then
        poetry run pre-commit run --files $(echo "$changed_files" | tr '\n' ' ') --hook-stage commit --config ./dev_config/python/.pre-commit-config.yaml
        if [ $? -ne 0 ]; then
            echo "Basic checks failed. Please fix the issues before committing."
            EXIT_CODE=1
        else
            echo "Basic checks passed!"
        fi
    else
        echo "No files changed. Skipping basic checks."
    fi
fi

# Run additional frontend checks if frontend files have changed
if [ -n "$frontend_changes" ]; then
    echo "Running additional frontend checks..."

    # Check if frontend directory exists
    if [ -d "frontend" ]; then
        # Change to frontend directory
        cd frontend || exit 1

        # Run build
        echo "Running npm build..."
        npm run build
        if [ $? -ne 0 ]; then
            echo "Frontend build failed. Please fix the issues before committing."
            EXIT_CODE=1
        fi

        # Run tests
        echo "Running npm test..."
        npm test
        if [ $? -ne 0 ]; then
            echo "Frontend tests failed. Please fix the failing tests before committing."
            EXIT_CODE=1
        fi

        # Return to the original directory
        cd ..

        if [ $EXIT_CODE -eq 0 ]; then
            echo "Frontend checks passed!"
        fi
    else
        echo "Frontend directory not found. Skipping frontend checks."
    fi
else
    echo "No frontend changes detected. Skipping additional frontend checks."
fi

# Run any existing pre-commit hooks that might have been installed by the user
# This makes our hook additive rather than replacing existing hooks
if [ -f ".git/hooks/pre-commit.local" ]; then
    echo "Running existing pre-commit hooks..."
    bash .git/hooks/pre-commit.local
    if [ $? -ne 0 ]; then
        echo "Existing pre-commit hooks failed."
        EXIT_CODE=1
    fi
fi

if [ $EXIT_CODE -eq 0 ]; then
    echo "All pre-commit checks passed!"
else
    echo "Some pre-commit checks failed. Please fix the issues before committing."
fi

exit $EXIT_CODE
