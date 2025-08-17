# Task List

1. ✅ Install pre-commit hooks for repository

2. ✅ Search codebase for occurrences of 'convo' (case-insensitive) and list files/contexts

3. 🔄 Categorize occurrences and determine safe renames; plan aliases if needed
Comments and log strings updated; function/constant/param/locals renamed. Avoid docs/assets and sample json. Added renames for CONVO_URL->CONVERSATION_URL and get_convo_link->get_conversation_link. Renamed setup_init_convo_settings and attach_convo_id param.
4. 🔄 Apply targeted renames across backend/tests and update call sites
Updated mcp.py create_* call sites, log strings; conversation_service.py param/local names; listen_socket.py and manage_conversations.py imports/usages; updated tests to use new names and constants.
5. 🔄 Run backend linting/formatting (pre-commit) and fix issues
pre-commit ruff-format modified one file; rerun after staging. Mypy passed.
6. ⏳ Run frontend lint/build

7. ⏳ Commit changes with required co-author line and summary
