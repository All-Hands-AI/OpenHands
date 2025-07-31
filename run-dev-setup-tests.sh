#!/bin/bash

# Master test runner for OpenHands development setup testing
# Tests 3 different setups across 3 different scenarios each

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results storage
declare -A setup_times
declare -A commit_times
declare -A test_results

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')] $1${NC}"
}

print_success() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] $1${NC}"
}

print_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] $1${NC}"
}

# Function to reset git and filesystem state
reset_state() {
    print_status "Resetting git and filesystem state..."

    # Reset any staged changes
    git reset HEAD . 2>/dev/null || true

    # Reset any modified files (but preserve our test scripts)
    git checkout -- . 2>/dev/null || true

    # Remove only the specific test files we create, not our scripts
    rm -f test_file_toplevel.py frontend/test_file_frontend.js

    # Remove test commits by resetting to the original commit
    # This removes any commits made during testing
    if [[ -n "$ORIGINAL_COMMIT" ]]; then
        current_commit=$(git rev-parse HEAD)
        if [[ "$current_commit" != "$ORIGINAL_COMMIT" ]]; then
            print_status "Removing test commits (resetting to $ORIGINAL_COMMIT)"
            git reset --hard "$ORIGINAL_COMMIT" 2>/dev/null || true
        fi
    fi

    print_success "State reset complete"
}

# Function to run a single test scenario
run_test_scenario() {
    local setup_name=$1
    local setup_script=$2
    local scenario=$3
    local test_file=$4
    local test_content=$5

    print_status "=== Testing $setup_name with $scenario ==="

    # Reset state before each test
    reset_state

    # Run the setup script and capture timing
    print_status "Running setup: $setup_script"
    setup_start=$(date +%s.%N)

    # Redirect setup output to log file if available
    if [[ -n "$SETUP_LOG_FILE" ]]; then
        echo "=== Setup: $setup_name - $scenario ===" >> "$SETUP_LOG_FILE"
        echo "Timestamp: $(date)" >> "$SETUP_LOG_FILE"
        echo "Command: bash $setup_script" >> "$SETUP_LOG_FILE"
        echo "--- Output ---" >> "$SETUP_LOG_FILE"

        if bash "$setup_script" >> "$SETUP_LOG_FILE" 2>&1; then
            setup_end=$(date +%s.%N)
            setup_duration=$(echo "$setup_end - $setup_start" | bc -l)
            setup_times["${setup_name}_${scenario}"]=$setup_duration
            echo "--- End Output (Duration: ${setup_duration}s) ---" >> "$SETUP_LOG_FILE"
            echo "" >> "$SETUP_LOG_FILE"
            print_success "Setup completed in ${setup_duration}s (output logged to setup log)"
        else
            setup_end=$(date +%s.%N)
            setup_duration=$(echo "$setup_end - $setup_start" | bc -l)
            setup_times["${setup_name}_${scenario}"]=$setup_duration
            echo "--- Setup Failed (Duration: ${setup_duration}s) ---" >> "$SETUP_LOG_FILE"
            echo "" >> "$SETUP_LOG_FILE"
            print_error "Setup failed in ${setup_duration}s for $setup_name (check setup log for details)"
            test_results["${setup_name}_${scenario}"]="SETUP_FAILED"
            return 1
        fi
    else
        # Fallback to original behavior if no log file specified
        if bash "$setup_script"; then
            setup_end=$(date +%s.%N)
            setup_duration=$(echo "$setup_end - $setup_start" | bc -l)
            setup_times["${setup_name}_${scenario}"]=$setup_duration
            print_success "Setup completed in ${setup_duration}s"
        else
            setup_end=$(date +%s.%N)
            setup_duration=$(echo "$setup_end - $setup_start" | bc -l)
            setup_times["${setup_name}_${scenario}"]=$setup_duration
            print_error "Setup failed in ${setup_duration}s for $setup_name"
            test_results["${setup_name}_${scenario}"]="SETUP_FAILED"
            return 1
        fi
    fi

    # Create test file if specified
    if [[ -n "$test_file" ]]; then
        print_status "Creating test file: $test_file"
        # Create directory if needed
        mkdir -p "$(dirname "$test_file")"
        echo -e "$test_content" > "$test_file"
    fi

    # Add files to git and check if there are changes to commit
    print_status "Adding files and committing..."
    git add .

    # Check if there are any changes to commit
    if git diff --cached --quiet; then
        # No changes to commit - this is expected for "no-change" scenario
        if [[ "$scenario" == "no-change" ]]; then
            print_success "No changes to commit (expected for no-change scenario)"
            test_results["${setup_name}_${scenario}"]="SUCCESS"
            commit_times["${setup_name}_${scenario}"]="0.0"

            # Log this to commit log if available
            if [[ -n "$COMMIT_LOG_FILE" ]]; then
                echo "=== Commit: $setup_name - $scenario ===" >> "$COMMIT_LOG_FILE"
                echo "Timestamp: $(date)" >> "$COMMIT_LOG_FILE"
                echo "Command: git status --porcelain (checking for changes)" >> "$COMMIT_LOG_FILE"
                echo "--- Output ---" >> "$COMMIT_LOG_FILE"
                echo "No changes to commit (expected for no-change scenario)" >> "$COMMIT_LOG_FILE"
                echo "--- End Output (Duration: 0.0s) ---" >> "$COMMIT_LOG_FILE"
                echo "" >> "$COMMIT_LOG_FILE"
            fi
        else
            # Changes were expected but none found
            print_error "No changes to commit, but changes were expected for $scenario scenario"
            test_results["${setup_name}_${scenario}"]="NO_CHANGES"
            commit_times["${setup_name}_${scenario}"]="0.0"
            return 1
        fi
    else
        # There are changes to commit
        commit_start=$(date +%s.%N)

        # Redirect commit output to log file if available
        if [[ -n "$COMMIT_LOG_FILE" ]]; then
            echo "=== Commit: $setup_name - $scenario ===" >> "$COMMIT_LOG_FILE"
            echo "Timestamp: $(date)" >> "$COMMIT_LOG_FILE"
            echo "Command: git commit -m \"Test commit for $setup_name - $scenario\"" >> "$COMMIT_LOG_FILE"
            echo "--- Output ---" >> "$COMMIT_LOG_FILE"

            if git commit -m "Test commit for $setup_name - $scenario" >> "$COMMIT_LOG_FILE" 2>&1; then
                commit_end=$(date +%s.%N)
                commit_duration=$(echo "$commit_end - $commit_start" | bc -l)
                commit_times["${setup_name}_${scenario}"]=$commit_duration
                test_results["${setup_name}_${scenario}"]="SUCCESS"
                echo "--- End Output (Duration: ${commit_duration}s) ---" >> "$COMMIT_LOG_FILE"
                echo "" >> "$COMMIT_LOG_FILE"
                print_success "Commit completed in ${commit_duration}s (output logged to commit log)"
            else
                commit_end=$(date +%s.%N)
                commit_duration=$(echo "$commit_end - $commit_start" | bc -l)
                commit_times["${setup_name}_${scenario}"]=$commit_duration
                echo "--- Commit Failed (Duration: ${commit_duration}s) ---" >> "$COMMIT_LOG_FILE"
                echo "" >> "$COMMIT_LOG_FILE"
                print_error "Commit failed in ${commit_duration}s for $setup_name - $scenario (check commit log for details)"
                test_results["${setup_name}_${scenario}"]="COMMIT_FAILED"
                return 1
            fi
        else
            # Fallback to original behavior if no log file specified
            if git commit -m "Test commit for $setup_name - $scenario"; then
                commit_end=$(date +%s.%N)
                commit_duration=$(echo "$commit_end - $commit_start" | bc -l)
                commit_times["${setup_name}_${scenario}"]=$commit_duration
                test_results["${setup_name}_${scenario}"]="SUCCESS"
                print_success "Commit completed in ${commit_duration}s"
            else
                commit_end=$(date +%s.%N)
                commit_duration=$(echo "$commit_end - $commit_start" | bc -l)
                commit_times["${setup_name}_${scenario}"]=$commit_duration
                print_error "Commit failed in ${commit_duration}s for $setup_name - $scenario"
                test_results["${setup_name}_${scenario}"]="COMMIT_FAILED"
                return 1
            fi
        fi
    fi

    print_success "=== $setup_name with $scenario completed ==="
    echo
}

# Function to generate final report
generate_report() {
    print_status "=== FINAL TEST REPORT ==="
    echo

    printf "%-20s %-20s %-15s %-15s %-10s\n" "SETUP" "SCENARIO" "SETUP_TIME(s)" "COMMIT_TIME(s)" "STATUS"
    printf "%-20s %-20s %-15s %-15s %-10s\n" "----" "--------" "-----------" "------------" "------"

    for setup in "dev-proper" "dev-max" "openhands-agent"; do
        for scenario in "no-change" "toplevel-change" "frontend-change"; do
            key="${setup}_${scenario}"
            setup_time=${setup_times[$key]:-"N/A"}
            commit_time=${commit_times[$key]:-"N/A"}
            status=${test_results[$key]:-"NOT_RUN"}

            printf "%-20s %-20s %-15s %-15s %-10s\n" "$setup" "$scenario" "$setup_time" "$commit_time" "$status"
        done
    done

    echo
    print_success "=== REPORT COMPLETE ==="
}

# Main execution
main() {
    # Store the original commit to reset to after each test
    ORIGINAL_COMMIT=$(git rev-parse HEAD)
    export ORIGINAL_COMMIT

    print_status "Starting OpenHands Development Setup Testing"
    print_status "Current branch: $(git branch --show-current)"
    print_status "Current commit: $(git rev-parse --short HEAD)"
    echo

    # Make scripts executable
    chmod +x test-dev-proper.sh test-dev-max.sh test-openhands-agent.sh

    # Test scenarios
    declare -A scenarios=(
        ["no-change"]=""
        ["toplevel-change"]="test_file_toplevel.py|# Test file for toplevel changes\nprint('Hello from toplevel test')"
        ["frontend-change"]="frontend/test_file_frontend.js|// Test file for frontend changes\nconsole.log('Hello from frontend test');"
    )

    # Run all combinations of setups and scenarios
    for setup in "dev-proper" "dev-max" "openhands-agent"; do
        setup_script="test-${setup}.sh"

        for scenario_key in "no-change" "toplevel-change" "frontend-change"; do
            scenario_data=${scenarios[$scenario_key]}

            if [[ "$scenario_data" == "" ]]; then
                # No file change scenario
                run_test_scenario "$setup" "$setup_script" "$scenario_key" "" ""
            else
                # File change scenario
                IFS='|' read -r test_file test_content <<< "$scenario_data"
                run_test_scenario "$setup" "$setup_script" "$scenario_key" "$test_file" "$test_content"
            fi
        done
    done

    # Final cleanup
    reset_state

    # Generate and display report
    generate_report

    print_success "All tests completed!"
}

# Check if bc is available for floating point arithmetic
if ! command -v bc &> /dev/null; then
    print_error "bc command not found. Installing bc for timing calculations..."
    # Try to install bc if not available
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y bc
    elif command -v yum &> /dev/null; then
        sudo yum install -y bc
    elif command -v brew &> /dev/null; then
        brew install bc
    else
        print_error "Could not install bc. Please install it manually."
        exit 1
    fi
fi

# Run the main function
main "$@"
