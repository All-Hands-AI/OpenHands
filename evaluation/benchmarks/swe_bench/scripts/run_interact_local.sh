CLI_AVAILABLE="false" \
USE_HINT_TEXT="false" \
SYSTEM_PROMPT_FILENAME="system_prompt_tom_benchmark.j2" \
bash ./evaluation/benchmarks/swe_bench/scripts/run_infer_interact.sh llm.claude-sonnet-4-20250514 HEAD TomCodeActAgent 1 100 1 test 2
