# Task List

1. ✅ Install pre-commit hooks and run backend pre-commit

2. ✅ Fetch PR #10391 details, diff, and inline comments addressed to @openhands; verify requested changes are applied
Verified PR body and labels. Previously applied changes matched reviewer requests. No additional inline comment content to process.
3. ✅ Implement minimal fix to ensure Tavily is used and Fetch/browser not used
Added logic in openhands/mcp/utils.py to skip adding 'fetch' stdio MCP tool when search_api_key is configured
4. ⏳ Run frontend lint/build if needed

5. ✅ Commit and push changes to e2e-tavily-web-search-test

6. 🔄 Wait 120 seconds and check GitHub Actions workflow status (prioritize E2E)

7. ⏳ If any job fails, download logs/artifacts, identify cause and fix; iterate until all green
