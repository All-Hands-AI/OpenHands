# Resolver Runtime Refactoring Plan

## Task Overview
Refactor the resolver component to reuse setup.py functions for runtime initialization, connection, and completion instead of reinventing the wheel.

## Repository Cloning Patterns Analysis

### Repository Cloning Patterns Across OpenHands Entry Points

#### 1. **Resolver (issue_resolver.py)** - DIFFERENT PATTERN (Legacy)
```python
# Step 1: Clone to separate location
subprocess.check_output(['git', 'clone', url, f'{output_dir}/repo'])

# Step 2: Later, copy repo to workspace
shutil.copytree(os.path.join(self.output_dir, 'repo'), self.workspace_base)

# Step 3: Create and connect runtime
runtime = create_runtime(config)
await runtime.connect()

# Step 4: Initialize runtime (git config, setup scripts)
self.initialize_runtime(runtime)
```

#### 2. **Main.py** - STANDARD PATTERN
```python
# Step 1: Create and connect runtime
runtime = create_runtime(config)
await runtime.connect()

# Step 2: Clone directly into runtime workspace + setup
repo_directory = initialize_repository_for_runtime(runtime, selected_repository)
```

#### 3. **Server/Session** - STANDARD PATTERN
```python
# Step 1: Create and connect runtime
# Step 2: Clone directly into runtime workspace
await runtime.clone_or_init_repo(tokens, repo, branch)
# Step 3: Run setup scripts
await runtime.maybe_run_setup_script()
await runtime.maybe_setup_git_hooks()
```

#### 4. **Setup.py's initialize_repository_for_runtime()** - STANDARD PATTERN
```python
# Calls runtime.clone_or_init_repo() + setup scripts
repo_directory = runtime.clone_or_init_repo(tokens, repo, branch)
runtime.maybe_run_setup_script()
runtime.maybe_setup_git_hooks()
```

### The Issue
The **resolver is the odd one out** - it uses a 2-step process (clone to temp location, then copy to workspace) due to **legacy reasons** (it was originally developed as a separate app built on OH, not a component of OH). All other entry points use the standard pattern (clone directly into runtime workspace).

## Current State Analysis

### ✅ What Resolver Already Does Right:
- [x] Uses `create_runtime()` from setup.py for runtime creation

### ❌ What Needs to be Fixed:
- [ ] **Resolver uses legacy 2-step cloning instead of standard runtime.clone_or_init_repo()**
- [ ] Resolver has custom `initialize_runtime()` method that duplicates setup.py logic
- [ ] Resolver has custom `complete_runtime()` method with no setup.py equivalent
- [ ] Resolver doesn't follow proper runtime cleanup patterns like main.py
- [ ] Runtime connection pattern is inconsistent across codebase

## Refactoring Steps

### Phase 1: Fix Repository Cloning Pattern (PRIORITY)
**Goal**: Make resolver use the same repository cloning pattern as all other OpenHands entry points.

- [ ] **Step 1.1**: Replace resolver's legacy 2-step cloning with standard pattern
  - Remove `subprocess.check_output(['git', 'clone', ...])` from `resolve_issue()`
  - Remove `shutil.copytree()` from `process_issue()`
  - Use `initialize_repository_for_runtime()` instead
  - This will clone directly into runtime workspace AND run setup scripts

- [ ] **Step 1.2**: Update resolver workflow to match standard pattern
  - Create and connect runtime first
  - Then call `initialize_repository_for_runtime()` for cloning + setup
  - Remove the manual repo copying step entirely
  - Ensure base_commit is still captured correctly

### Phase 2: Refactor Runtime Initialization and Completion
**Goal**: Remove code duplication between resolver and setup.py for runtime operations.

- [ ] **Step 2.1**: Create missing functions in setup.py
  - Create `setup_runtime_environment()` for git config and platform-specific setup
  - Create `complete_runtime_session()` for git patch generation
  - Create `cleanup_runtime()` for proper resource cleanup

- [ ] **Step 2.2**: Replace resolver's `initialize_runtime()`
  - Use setup.py's `setup_runtime_environment()` instead
  - Remove duplicate git configuration code
  - Maintain platform-specific behavior (GitLab CI)

- [ ] **Step 2.3**: Replace resolver's `complete_runtime()`
  - Use setup.py's `complete_runtime_session()` instead
  - Move git patch generation logic to setup.py
  - Ensure return values match resolver's expectations

- [ ] **Step 2.4**: Add proper runtime cleanup to resolver
  - Use setup.py's `cleanup_runtime()` function
  - Ensure resources are properly released in try/finally blocks

### Phase 3: Testing and Validation
- [ ] **Step 3.1**: Test resolver functionality with refactored code
  - Verify git operations work correctly
  - Verify setup scripts are executed
  - Verify git hooks are set up

- [ ] **Step 3.2**: Test runtime lifecycle (create → connect → clone → initialize → complete → cleanup)
  - Ensure no resource leaks
  - Verify proper error handling

- [ ] **Step 3.3**: Verify resolver output remains consistent
  - Git patches are generated correctly
  - Issue resolution works as before
  - No regression in functionality

### Phase 4: Code Quality and Documentation
- [ ] **Step 4.1**: Add proper documentation to new setup.py functions
  - Document parameters and return values
  - Add usage examples
  - Document platform-specific behavior

- [ ] **Step 4.2**: Remove obsolete code from resolver
  - Delete old `initialize_runtime()` method
  - Delete old `complete_runtime()` method
  - Clean up imports and unused code

- [ ] **Step 4.3**: Update any other components that might benefit from these functions
  - Check if other entry points could use the same patterns
  - Ensure consistency across the codebase

## Success Criteria
- [ ] **Resolver uses standard repository cloning pattern (runtime.clone_or_init_repo)**
- [ ] Resolver uses setup.py functions for all runtime operations
- [ ] No code duplication between resolver and setup.py
- [ ] Proper runtime lifecycle management (connect → initialize → complete → cleanup)
- [ ] All existing resolver functionality preserved
- [ ] Consistent patterns across all OpenHands entry points
- [ ] Proper error handling and resource cleanup

## Files to Modify
1. `/openhands/core/setup.py` - Add new runtime management functions
2. `/openhands/resolver/issue_resolver.py` - Refactor to use setup.py functions
3. Any tests related to resolver functionality

## Risk Mitigation
- Maintain backward compatibility during refactoring
- Test thoroughly before removing old code
- Keep git patch generation logic identical to avoid breaking issue resolution
- Ensure platform-specific behavior (GitLab CI) is preserved
