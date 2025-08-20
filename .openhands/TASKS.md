# Task List

1. 🔄 Align git config and co-author policy
Will reset git config to enyst/engel.nyst@gmail.com; ensure co-author lines use OpenHands-GPT-5.
2. 🔄 Revert ConversationMemory hotfix; enforce Thought everywhere post-deserialization
Removed permissive handling of str Thought in ConversationMemory.
3. 🔄 Normalize Thought in all response_to_actions implementations
Updated combine_thought to always coerce to Thought. Need to ensure readonly_agent and loc_agent use the same helper (they already call combine_thought).
4. 🔄 Verify serialization/deserialization boundaries
action_from_dict already normalizes str/dict Thought; event_to_dict normalizes output. Verify tests.
5. ⏳ Run full pre-commit as repo.md
Run poetry pre-commit and address migration-mode hook per repo.md.
6. ⏳ Run targeted tests
Memory and function_calling tests; avoid docker.
