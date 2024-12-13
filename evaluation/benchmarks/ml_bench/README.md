# ML-Bench Evaluation with OpenHands

This project implements the evaluation of agents on the [ML-Bench](https://arxiv.org/abs/2311.09835) dataset using OpenHands. [ML-Bench](https://arxiv.org/abs/2311.09835) is a comprehensive benchmark designed to assess the effectiveness of Large Language Models (LLMs) in leveraging existing functions in open-source libraries for machine learning tasks. The benchmark consists of 10,040 samples spanning 130 tasks over 14 notable machine learning GitHub repositories.

## Task Overview

The ML-Bench task presents a scenario where, given a GitHub repository, the language model has access to all files within the repository. Upon receiving a user instruction with a set of specific parameters, the Agent is required to write code that invokes models or functions from the GitHub repository. The generated code must align with the user's instruction, particularly in terms of the specified parameters, and must be executable.

The task introduces new challenges for LLMs, such as comprehending long and language-code interleaved documents, understanding complex cross-file code structures, and effectively navigating the codebase to locate relevant information. ML-Bench serves as a critical tool for assessing the efficiency and adaptability of various methods in real-world scenarios.

For more details on the ML-Bench task and dataset, please refer to the paper: [ML-Bench: Evaluating Large Language Models for Code Generation in Repository-Level Machine Learning Tasks](https://arxiv.org/abs/2311.09835).

## Setup Environment and LLM Configuration

Please follow instruction [here](../../README.md#setup) to setup your local development environment and LLM.

## Run Inference on ML-Bench

To run the evaluation on the ML-Bench dataset, use the following command:

```bash
./evaluation/benchmarks/ml_bench/scripts/run_infer.sh [model_config] [git-version] [split] [agent] [eval_limit]
# e.g., ./evaluation/benchmarks/ml_bench/scripts/run_infer.sh eval_gpt4_1106_preview 0.6.2 full CodeActAgent 10
```

You can replace `eval_gpt4_1106_preview` with any model you set up in `config.toml`.

## Score Evaluation Output

To score the evaluation output, use the following command:

```bash
./evaluation/benchmarks/ml_bench/scripts/summarise_results.py [eval_output_dir]
# e.g., ./evaluation/benchmarks/ml_bench/scripts/summarise_results.py evaluation/evaluation_outputs/outputs/ml_bench/CodeActAgent/gpt-4-1106-preview_maxiter_10_N_v1.5
```

## Run Error Analysis on ML-Bench

To run error analysis on the ML-Bench dataset, use the following command:

```bash
./evaluation/benchmarks/ml_bench/scripts/run_analysis.sh [eval_output_dir] [model_config]
# e.g., ./evaluation/benchmarks/ml_bench/scripts/run_analysis.sh evaluation/evaluation_outputs/outputs/ml_bench/CodeActAgent/gpt-4-1106-preview_maxiter_10_N_v1.5/output.jsonl eval_gpt4_1106_preview
```

This command generates a report on the evaluation output and provides insights into the agent's performance.

## Examples

For each task in the ML-Bench dataset, OpenHands provides the agent with a set number of iterations to complete the task. The `history` field in the evaluation output shows each iteration's response and actions taken by the agent to complete the task.

Here's an example of the evaluation output for a single task instance:

```json
{
  "instance_id": 3,
  "repo": "https://github.com/dmlc/dgl",
  "instruction": "Please complete the Machine Learning task in the following repository: dgl\n\nThe task is: DGL Implementation of NGCF model\n\nI have a deep desire to embark on a journey brimming with knowledge and expertise. My objective is to train a cutting-edge NGCF Model, known for its unparalleled capabilities, on the illustrious dataset known as gowalla. To ensure swift execution, I kindly request your assistance in crafting the code, making use of the powerful GPU #3 and an embedding size of 32. Can you lend a helping hand to transform this dream into a reality?\n\nYou should create a script named `run.sh` under the specified path in the repo to run the task.\n\nYou can find the task repo at: /workspace/dgl/examples/pytorch/NGCF/NGCF\n\nYou should terminate the subprocess after running the task (e.g., call subprocess.Popen(args).wait()).When you think you have completed the task, please finish the interaction using the "finish" tool.\n",
  "metadata": {
    "agent_class": "CodeActAgent",
    "model_name": "gpt-4-1106-preview",
    "max_iterations": 10,
    "eval_output_dir": "evaluation/evaluation_outputs/outputs/ml_bench/CodeActAgent/gpt-4-1106-preview_maxiter_10_N_v1.5",
    "start_time": "2024-05-26 17:39:59",
    "git_commit": "dd8ee9044a94a213dc2e31d2085dbf2924ee80a1"
  },
  "history": [
    [
      {
        "id": 0,
        "timestamp": "2024-05-26T17:40:41.060009",
        "source": "user",
        "message": "Please complete the Machine Learning task in the following repository: dgl\n\nThe task is: DGL Implementation of NGCF model\n\nI have a deep desire to embark on a journey brimming with knowledge and expertise. My objective is to train a cutting-edge NGCF Model, known for its unparalleled capabilities, on the illustrious dataset known as gowalla. To ensure swift execution, I kindly request your assistance in crafting the code, making use of the powerful GPU #3 and an embedding size of 32. Can you lend a helping hand to transform this dream into a reality?\n\nYou should create a script named `run.sh` under the specified path in the repo to run the task.\n\nYou can find the task repo at: /workspace/dgl/examples/pytorch/NGCF/NGCF\n\nYou should terminate the subprocess after running the task (e.g., call subprocess.Popen(args).wait()).When you think you have completed the task, please finish the interaction using the "finish" tool.\n",
        "action": "message",
        "args": {
          "content": "Please complete the Machine Learning task in the following repository: dgl\n\nThe task is: DGL Implementation of NGCF model\n\nI have a deep desire to embark on a journey brimming with knowledge and expertise. My objective is to train a cutting-edge NGCF Model, known for its unparalleled capabilities, on the illustrious dataset known as gowalla. To ensure swift execution, I kindly request your assistance in crafting the code, making use of the powerful GPU #3 and an embedding size of 32. Can you lend a helping hand to transform this dream into a reality?\n\nYou should create a script named `run.sh` under the specified path in the repo to run the task.\n\nYou can find the task repo at: /workspace/dgl/examples/pytorch/NGCF/NGCF\n\nYou should terminate the subprocess after running the task (e.g., call subprocess.Popen(args).wait()).When you think you have completed the task, please finish the interaction using the "finish" tool.\n",
          "wait_for_response": false
        }
      },
      {
        "message": "No observation",
        "observation": "null",
        "content": "",
        "extras": {}
      }
    ],
    // ... more iterations
  ],
  "eval_exit_code": 124,  // ML-Bench believes the agent is successful if it continues to run until timeout
  "eval_output": "",
  "eval_script": "pip install Matplotlib==2.2.2\r\n"
                 "cd /workspace/dgl/examples/pytorch/dgmg\r\n"
                 "python main.py",
  "metrics": {
    "success": 1
  }
}
```

The `history` field contains the agent's actions and observations at each iteration, including the commands executed, file edits, and the agent's thoughts.

The `eval_exit_code` and `eval_output` fields provide information about the execution of the evaluation command and its output.

The `metrics` field contains the parsed evaluation metrics from the `eval_output`.

## Customization

You can customize the evaluation script by modifying the `evaluation/benchmarks/ml_bench/run_infer.py` file. This script handles loading the ML-Bench dataset, running the agent on each task instance, and saving the evaluation outputs.

Feel free to adjust the configuration, logging, and output formatting to suit your needs.

## Contributing

If you encounter any issues or have suggestions for improvements, please open an issue or submit a pull request on the [GitHub repository](https://github.com/gersteinlab/ML-bench).

## License

This project is licensed under the [MIT License](LICENSE).
