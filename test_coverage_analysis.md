# VSCode Extension Test Coverage Analysis

## Current Coverage: 65% (44 lines missing)

## NEW BEHAVIORS TO TEST:

### ✅ Already Implemented:
1. Extension already installed detection → create flag and exit

### ❌ Missing Critical Tests:

#### A. Extension Detection Edge Cases:
1. `--list-extensions` returns non-zero exit code → should continue with installation
2. `--list-extensions` throws exception → should continue with installation  
3. Extension ID found in middle of list (not first line) → should detect correctly
4. Empty stdout from `--list-extensions` → should continue with installation
5. Extension ID partially matches (e.g., "other.openhands-vscode") → should not match

#### B. Success Flag Creation:
1. `_mark_installation_successful()` OSError → should log but continue
2. Flag creation succeeds → should log debug message

#### C. Retry Logic Validation:
1. Installation fails → should NOT create flag (allow retry)
2. Installation succeeds → should create flag (prevent retry)
3. Flag exists → should skip all operations

#### D. New Error Messages:
1. All methods fail → should show retry message
2. Different editors → should show correct editor name in messages

#### E. Helper Function Coverage:
1. `_is_extension_installed()` with various subprocess outcomes
2. `_mark_installation_successful()` with various file system states

## TESTS NEEDING UPDATES:

### Subprocess Call Count Changes:
- All tests now need to account for initial `--list-extensions` call
- Tests expecting 0 subprocess calls now expect 1
- Tests expecting 1 subprocess call now expect 2

### Flag File Name Changes:
- Old: `.vscode_extension_install_attempted`
- New: `.vscode_extension_installed`

### Error Message Changes:
- Old: "Could not create VS Code extension attempt flag file"
- New: "Could not create VS Code extension success flag file"

### Windsurf Command Detection:
- Some tests expect `windsurf` but code uses `surf` (need to check implementation)

## PRIORITY ORDER:
1. Fix existing failing tests (update for new behavior)
2. Add critical edge case tests for new functions
3. Add comprehensive retry logic tests
4. Add error handling tests