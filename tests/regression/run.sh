#!/bin/bash
set -e

# Function to run a single test case
run_test_case() {
    local case_dir=$1
    local case_name=$(basename "$case_dir")
    echo "Running test case: $case_name"

    # Read case configuration
    local timeout=120  # Default timeout 2 minutes
    local required=true
    if [ -f "$case_dir/case.yaml" ]; then
        if grep -q "^timeout:" "$case_dir/case.yaml"; then
            timeout=$(grep "^timeout:" "$case_dir/case.yaml" | awk '{print $2}')
        fi
        if grep -q "^required:" "$case_dir/case.yaml"; then
            required=$(grep "^required:" "$case_dir/case.yaml" | awk '{print $2}')
        fi
    fi

    # Create temp directory
    local temp_dir=$(mktemp -d)
    trap "rm -rf $temp_dir" EXIT

    # Check if git repo and commit-ish are specified
    if [ -f "$case_dir/case.yaml" ]; then
        if grep -q "^git:" "$case_dir/case.yaml"; then
            local repo=$(grep "^git:" "$case_dir/case.yaml" | awk '{print $2}')
            local commit="main"  # Default to main
            if grep -q "^commit-ish:" "$case_dir/case.yaml"; then
                commit=$(grep "^commit-ish:" "$case_dir/case.yaml" | awk '{print $2}')
            fi
            git clone "$repo" "$temp_dir" && cd "$temp_dir" && git checkout "$commit"
        fi
    fi

    # Copy prompt and test script
    cp "$case_dir/prompt.txt" "$temp_dir/"
    cp "$case_dir/test.sh" "$temp_dir/"
    chmod +x "$temp_dir/test.sh"

    # Run the agent in headless mode with timeout
    cd "$temp_dir"
    timeout "$timeout" python3 -m openhands.core.main --headless < prompt.txt

    # Run the test script
    ./test.sh
    local test_result=$?

    if [ $test_result -ne 0 ]; then
        echo "Test case $case_name failed"
        if [ "$required" = "true" ]; then
            exit 1
        fi
    else
        echo "Test case $case_name passed"
    fi
}

# Find and run all test cases
for case_dir in $(find "$(dirname "$0")/cases" -type d -mindepth 1 -maxdepth 1); do
    run_test_case "$case_dir"
done

echo "All tests completed successfully"