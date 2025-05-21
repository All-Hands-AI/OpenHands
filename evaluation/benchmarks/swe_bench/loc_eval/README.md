# **SWE-Bench Evaluation with Localization Evaluation**

This folder implements localization evaluation at both file and function levels to complementing the assessment of agent inference on [SWE-Bench](https://www.swebench.com/).

## **1. Environment Setup**
- Python env: [Install python environment](../../../README.md#development-environment)
- LLM config: [Configure LLM config](../../../README.md#configure-openhands-and-your-llm)

## **2. Inference & Evaluation**
- Run inference on SWE-Bench instances:
    - You may refer to instructions at [README.md](../README.md) for running inference on SWE-Bench
    - General settings:
        - Format:
            ```bash
            ./evaluation/benchmarks/swe_bench/scripts/run_infer.sh [model_config] [git-version] [agent] [eval_limit] [max_iter] [num_workers] [dataset] [dataset_split] [N_RUNS] [MODE] [loc-eval-save]
            ```
            - `model_config`: the config group name for your LLM settings, as defined in your `config.toml`.
            - `git-version`: the git commit hash of the OpenHands version you would like to evaluate.
            - `agent`: the name of the agent for benchmarks, defaulting to `CodeActAgent`.
            - `eval_limit`: limits the evaluation to the first `eval_limit` instances. By default, the script evaluates the entire SWE-bench_Lite test set (300 issues). 
                - Note: in order to use `eval_limit`, you must also set `agent`.
            - `max_iter`: the maximum number of iterations for the agent to run. By default, it is set to 100.
            - `num_workers`: the number of parallel workers to run the evaluation. By default, it is set to 1.
            - `dataset`: SWE-Bench dataset name. Please use huggingface format to specifies which dataset to evaluate on.
            - `dataset_split`: SWE-Bench dataset split.
            - `loc-eval-save`: directory to save outputs for localization

        - Example:
            ```bash
            # Example
            ./evaluation/benchmarks/swe_bench/loc_eval/scripts/run_infer.sh llm.claude-3-5-haiku HEAD CodeActAgent 20 50 1 princeton-nlp/SWE-bench_Verified test 1 swe ./evaluation/benchmarks/swe_bench/loc_eval/saves
            ```
- Run evaluation on SWE-Bench instances:
    - You may refer to instructions at [README.md](../README.md) for running evaluation on SWE-Bench
    - Format:
        ```bash
        ./evaluation/benchmarks/swe_bench/scripts/eval_infer.sh [output_jsonl] [instance_id] [dataset_name] [split]
        ```
        - `output_jsonl`: inference output JSONL file
        - `instance_id`: SWE-Bench instance id
        - `dataset_name`: SWE-Bench dataset name
        - `split`: SWE-Bench dataset split to use

    - Example: 
        ```bash
        # Example
        ./evaluation/benchmarks/swe_bench/scripts/eval_infer.sh evaluation/evaluation_outputs/outputs/princeton-nlp__SWE-bench_Lite/CodeActAgent/claude-3-5-haiku_maxiter_50_N_v1.0/output.jsonl
        ```

## **3. Localization Evaluation**
- Localization evaluation computes two-level localization accuracy, while also considers task success as an additional metric for overall evaluation:
    - **File localization accuracy:** the accuracy of accurately localize the target file
    - **Function localization accuracy:** the accuracy of accurately localize the target function
    - **Task success** (will be auto-skipped if missing): the success rate of whether tasks are successfully resolved
    - **Inference cost:** the expenditure of agent running inference on SWE-Bench instances
- Run localization evaluation
    - Format:
        ```bash
        ./evaluation/benchmarks/swe_bench/loc_eval/scripts/run_eval_loc.sh [infer-dir] [eval-dir] [output-dir] [split] [dataset] [max-infer-turn]
        ```
        - `infer-dir`: inference directory containing inference outputs
        - `eval-dir`: evaluation directory containing evaluation outputs
        - `output-dir`: localization evaluation output dir
        - `split`: SWE-Bench dataset split to use
        - `dataset`: SWE-Bench dataset name
        - `max-infer-turn`: the maximum number of iterations the agent took to run inference

    - Example: 
        ```bash
        # Example
        ./evaluation/benchmarks/swe_bench/loc_eval/scripts/run_eval_loc.sh \
            --infer-dir ./inference_outputs \
            --eval-dir ./inference_eval_outputs \
            --output-dir ./evaluation/benchmarks/swe_bench/loc_eval/saves \
            --split test \
            --dataset princeton-nlp/SWE-bench_Verified \
            --max-infer-turn 20
        ```