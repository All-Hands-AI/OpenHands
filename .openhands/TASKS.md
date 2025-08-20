# Task List

1. ⏳ Install pre-commit hooks and run backend pre-commit suite

2. ✅ Run full unit test suite as in CI (PYTHONPATH, xdist) and evaluate failures
Executed pytest --forked -n auto -svv ./tests/unit. After fix to config utils, only docker runtime builder tests fail locally due to missing Docker daemon. In CI with GitHub runners (setup-buildx), these should pass.
3. ✅ Run runtime CLI test (TEST_RUNTIME=cli)
Ran tests/runtime/test_bash.py; 25 passed, 10 skipped. Matches CI target.
4. ✅ Fix ConversationMemory and SecurityAnalyzer per PR #10432 requirements
ConversationMemory ensures only Thought.text is sent; coerces str to Thought and merges tool_call content. SecurityAnalyzer idempotent with processed event id set; thread-safe scheduling.
5. ✅ Fix config bug so workspace_mount_path_in_sandbox remains default unless SANDBOX_VOLUMES mounts /workspace
Adjusted load_from_env to ignore deprecated workspace_mount_path_in_sandbox from env (preserves /workspace). Unit tests for sandbox volumes now pass.
6. ⏳ Commit changes and push to feature branch used by PR #10432; update PR with summary comment
