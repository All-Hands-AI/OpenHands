# OpenHands Development Setup Testing Framework

This testing framework compares different development setup approaches for OpenHands by measuring setup times and commit performance across various scenarios.

## Overview

The framework tests 3 different development setups:

1. **dev-proper**: Full build setup using `make build`
2. **dev-min**: Minimal setup using `make install-pre-commit-hooks`
3. **openhands-agent**: Agent setup using `.openhands/setup.sh`

Each setup is tested across 3 scenarios:
- **no-change**: Clean commit with no file changes
- **toplevel-change**: Commit with a Python file change in the root directory
- **frontend-change**: Commit with a JavaScript file change in the frontend directory

## Files

### Test Scripts
- `test-dev-proper.sh`: Runs full build setup (`make build`)
- `test-dev-min.sh`: Runs minimal setup (`make install-pre-commit-hooks`)
- `test-openhands-agent.sh`: Runs OpenHands agent setup (`.openhands/setup.sh`)

### Main Runner
- `run-dev-setup-tests.sh`: Master script that orchestrates all tests
- `run-timed-tests.sh`: Wrapper script that adds timestamps to all output

## Usage

### Quick Start
```bash
# Run all tests with timing
./run-timed-tests.sh
```

### Manual Execution
```bash
# Run tests without external timing wrapper
./run-dev-setup-tests.sh
```

## What Gets Measured

1. **Setup Time**: How long each development setup takes to complete
2. **Commit Time**: How long the git commit process takes (including pre-commit hooks)
3. **Success Rate**: Whether each setup and commit completed successfully

## Test Process

For each combination of setup and scenario:

1. **Reset State**: Clean git state and remove test files
2. **Run Setup**: Execute the specific development setup script
3. **Create Test File**: Add a test file if the scenario requires it
4. **Git Operations**: Add files and commit with timing measurement
5. **Record Results**: Store timing and success/failure data

## Expected Outcomes

- **dev-proper**: Longest setup time, potentially faster commits due to complete environment
- **dev-min**: Medium setup time, standard commit performance
- **openhands-agent**: Fastest setup, may have different pre-commit behavior

## Output

The framework generates a detailed report showing:
- Setup times for each configuration
- Commit times for each scenario
- Success/failure status for all tests
- Formatted table for easy comparison

## Requirements

- `bc` command for floating-point arithmetic (auto-installed if missing)
- `script` command for timing wrapper (usually pre-installed on Linux)
- Git repository with proper remote configuration
- All OpenHands dependencies for the tested setups

## Notes

- All tests run on a dedicated git branch (`dev-setup-testing`)
- State is reset between each test to ensure clean conditions
- Test files are automatically cleaned up after each scenario
- The framework handles setup failures gracefully and continues with remaining tests

## Troubleshooting

If tests fail:
1. Check that all required dependencies are installed
2. Ensure you're in the OpenHands root directory
3. Verify git repository is properly configured
4. Check that the current branch allows commits

## Cleanup

After testing, you can return to your original branch:
```bash
git checkout main  # or your original branch
git branch -D dev-setup-testing  # optional: delete test branch
