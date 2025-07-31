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

    if bash "$setup_script"; then
        setup_end=$(date +%s.%N)
        setup_duration=$(echo "$setup_end - $setup_start" | bc -l)
        setup_times["${setup_name}_${scenario}"]=$setup_duration
        print_success "Setup completed in ${setup_duration}s"
    else
        print_error "Setup failed for $setup_name"
        test_results["${setup_name}_${scenario}"]="SETUP_FAILED"
        return 1
    fi

    # Create test file if specified
    if [[ -n "$test_file" ]]; then
        print_status "Creating test file: $test_file"
        # Create directory if needed
        mkdir -p "$(dirname "$test_file")"
        echo -e "$test_content" > "$test_file"
    fi

    # Add files to git and commit with timing
    print_status "Adding files and committing..."
    git add .

    commit_start=$(date +%s.%N)

    if git commit -m "Test commit for $setup_name - $scenario"; then
        commit_end=$(date +%s.%N)
        commit_duration=$(echo "$commit_end - $commit_start" | bc -l)
        commit_times["${setup_name}_${scenario}"]=$commit_duration
        test_results["${setup_name}_${scenario}"]="SUCCESS"
        print_success "Commit completed in ${commit_duration}s"
    else
        print_error "Commit failed for $setup_name - $scenario"
        test_results["${setup_name}_${scenario}"]="COMMIT_FAILED"
        return 1
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

    for setup in "dev-proper" "dev-min" "openhands-agent"; do
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
    print_status "Starting OpenHands Development Setup Testing"
    print_status "Current branch: $(git branch --show-current)"
    print_status "Current commit: $(git rev-parse --short HEAD)"
    echo

    # Make scripts executable
    chmod +x test-dev-proper.sh test-dev-min.sh test-openhands-agent.sh

    # Test scenarios
    declare -A scenarios=(
        ["no-change"]=""
        ["toplevel-change"]="test_file_toplevel.py|# Test file for toplevel changes\nprint('Hello from toplevel test')"
        ["frontend-change"]="frontend/test_file_frontend.js|// Test file for frontend changes\nconsole.log('Hello from frontend test');"
    )

    # Run all combinations of setups and scenarios
    for setup in "dev-proper" "dev-min" "openhands-agent"; do
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
