# Task List

1. 🔄 Locate and confirm the hardcoded condenser max_size in server initialization and record exact file/line

2. ⏳ Backend: add validation for condenser_max_size >= 10 in Settings model

3. ⏳ Frontend: Add numeric input for condenser max size in Advanced LLM Settings UI, disabled when default condenser disabled

4. ⏳ Frontend: Add i18n keys and declaration for condenser max size

5. 🔄 Frontend: Ensure hooks/types/defaults include condenser_max_size for GET/POST
User indicates mostly done; verify and adjust PostApiSettings and use-save-settings mapping
6. 🔄 Mocks: Update handlers to include condenser_max_size in GET/POST persistence

7. ⏳ Run linters/builds and fix errors (backend pre-commit, frontend lint/build)

8. ⏳ Commit changes and open PR with proper description
