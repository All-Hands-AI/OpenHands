# Task List

1. 🔄 Push latest commits on fix/metrics-in-state-for-evals to GitHub
Token auth failing; will try PAT via env var update or fall back to GitHub API for PR changes only
2. ⏳ Update PR #10537 description to reflect new metrics approach

3. ✅ Install pre-commit hooks and run linters
pre-commit run succeeded on changed files; imports fixed
4. ✅ Run targeted unit tests for metrics exposure
tests/unit/test_state_metrics_exposure.py passes locally
5. 🔄 Fix integration test script to use get_metrics and commit with passing pre-commit
