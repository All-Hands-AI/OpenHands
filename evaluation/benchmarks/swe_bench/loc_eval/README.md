# **Localization Evaluation for SWE-Bench**

This folder implements localization evaluation at both file and function levels to complementing the assessment of agent inference on [SWE-Bench](https://www.swebench.com/).

## **1. Environment Setup**
- Python env: [Install python environment](../../../README.md#development-environment)
- LLM config: [Configure LLM config](../../../README.md#configure-openhands-and-your-llm)

## **2. Inference & Evaluation**
- Inference and evaluation follow the original `run_infer.sh` and `run_eval.sh` implementation
    - You may refer to instructions at [README.md](../README.md) for running inference and evaluation on SWE-Bench

## **3. Localization Evaluation**
- Localization evaluation computes two-level localization accuracy, while also considers task success as an additional metric for overall evaluation:
    - **File Localization Accuracy:** Accuracy of correctly localizing the target file
    - **Function Localization Accuracy:** Accuracy of correctly localizing the target function
    - **Resolve Rate** (will be auto-skipped if missing): Success rate of whether tasks are successfully resolved
    - **File Localization Efficiency:** Average number of iterations taken to successfully localize the target file
    - **Function Localization Efficiency:** Average number of iterations taken to successfully localize the target file
    - **Task success efficiency:** Average number of iterations taken to resolve the task
    - **Resource efficiency:** the API expenditure of the agent running inference on SWE-Bench instances

- Run localization evaluation
    - Format:
        ```bash
        ./evaluation/benchmarks/swe_bench/scripts/eval_localization.sh [infer-dir] [split] [dataset] [max-infer-turn] [align-with-max]
        ```
        - `infer-dir`: inference directory containing inference outputs
        - `split`: SWE-Bench dataset split to use
        - `dataset`: SWE-Bench dataset name
        - `max-infer-turn`: the maximum number of iterations the agent took to run inference
        - `align-with-max`: whether to align failure indices (e.g., incorrect localization, unresolved tasks) with `max_iter`

    - Example:
        ```bash
        # Example
        ./evaluation/benchmarks/swe_bench/scripts/eval_localization.sh \
            --infer-dir ./evaluation/evaluation_outputs/outputs/princeton-nlp__SWE-bench_Verified-test/CodeActAgent/gpt_4o_100_N \
            --split test \
            --dataset princeton-nlp/SWE-bench_Verified \
            --max-infer-turn 100 \
            --align-with-max true
        ```

- Localization evaluation results will be automatically saved to `[infer-dir]/loc_eval`
