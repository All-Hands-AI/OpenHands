CLI_AVAILABLE="false" \
USE_HINT_TEXT="false" \
SYSTEM_PROMPT_FILENAME="system_prompt_tom_benchmark.j2" \
TOM_AGENT_MODEL="litellm_proxy/claude-sonnet-4-20250514" \
bash ./evaluation/benchmarks/swe_bench/scripts/run_infer_interact.sh llm.claude-3-7-sonnet HEAD TomCodeActAgent 1 100 1 cmu-lti/stateful test 1 stateful
