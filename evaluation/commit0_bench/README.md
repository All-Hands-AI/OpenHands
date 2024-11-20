# Commit0 Evaluation with OpenHands

Step 1: `git clone https://github.com/commit-0/commit0.git evaluation/commit0_bench/commit0`

Step 2: adding `commit0 = { path = "evaluation/commit0_bench/commit0" }` to pyproject.toml

Step 3: Comment Line 134 in pyproject.toml (`# swebench = { git = "https://github.com/All-Hands-AI/SWE-bench.git" }`) due to package conflict

Step 4: Run `make build` to setup the environment

Step 5: Run `./evaluation/commit0_bench/scripts/run_infer.sh lite llm.eval_sonnet HEAD CodeActAgent 20 100 1` to run the evaluation
