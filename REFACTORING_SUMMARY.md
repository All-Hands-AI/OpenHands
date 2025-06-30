# Refactoring Summary: Repository Provider Detection

## Problem
The `_is_gitlab_repo` function in `openhands/runtime/base.py` was error-prone because it:
1. Made network calls to determine the provider type
2. Could fail due to authentication issues or network problems
3. Was called multiple times for the same repository
4. Had inconsistent error handling

## Solution
Replaced the error-prone function with a robust `RepositoryInfo` class that includes provider information obtained during the initial repository verification.

## Changes Made

### 1. Created `RepositoryInfo` class in `openhands/runtime/base.py`
- Encapsulates repository string and provider information
- Provides convenient methods: `is_gitlab()`, `provider`, `full_name`, `directory_name`
- Handles cases where provider information is not available (backward compatibility)

### 2. Updated `clone_or_init_repo` method
- Now returns `RepositoryInfo` instead of just a string
- Uses new `_get_authenticated_git_url_and_repo_info` method
- Eliminates redundant provider detection calls

### 3. Refactored `_get_authenticated_git_url` method
- Renamed to `_get_authenticated_git_url_and_repo_info`
- Returns both the authenticated URL and Repository object
- Avoids duplicate provider verification calls

### 4. Updated `get_microagents_from_org_or_user` method
- Now accepts `RepositoryInfo` instead of string
- Uses `repository_info.is_gitlab()` instead of `_is_gitlab_repository()`
- More reliable provider detection

### 5. Updated `get_microagents_from_selected_repo` method
- Now accepts `RepositoryInfo` instead of string
- Passes repository info to org/user microagent loading

### 6. Removed `_is_gitlab_repository` method
- Completely eliminated the error-prone function
- No more network calls for provider detection during microagent loading

### 7. Updated all callers
- `openhands/server/session/agent_session.py`: Updated to use `RepositoryInfo`
- `openhands/core/setup.py`: Updated to use `RepositoryInfo`
- `openhands/cli/main.py`: Already compatible (passes None)

### 8. Updated tests
- `tests/unit/test_runtime_gitlab_microagents.py`: Updated to test `RepositoryInfo` class
- Replaced tests for removed `_is_gitlab_repository` method
- Added comprehensive tests for the new `RepositoryInfo` functionality

## Benefits

1. **Reliability**: Provider information is determined once during repository verification
2. **Performance**: Eliminates redundant network calls
3. **Error Handling**: Consistent error handling through the Repository object
4. **Maintainability**: Clear separation of concerns with dedicated `RepositoryInfo` class
5. **Backward Compatibility**: Works with existing code that doesn't have provider info

## Backward Compatibility

The refactoring maintains backward compatibility:
- `RepositoryInfo` can be created with just a repository string
- When provider info is not available, `is_gitlab()` returns `False` (safe default)
- Existing callers that pass `None` continue to work

## Testing

All changes have been tested with:
- Unit tests for `RepositoryInfo` class functionality
- Integration tests for GitLab vs GitHub provider detection
- Backward compatibility tests for cases without provider info
- Pre-commit hooks for code quality and formatting
