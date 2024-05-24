# ML-Bench Evaluation with OpenDevin

This project implements the evaluation of agents on the ML-Bench dataset using OpenDevin. ML-Bench is a comprehensive benchmark designed to assess the effectiveness of Large Language Models (LLMs) in leveraging existing functions in open-source libraries for machine learning tasks. The benchmark consists of 10,040 samples spanning 130 tasks over 14 notable machine learning GitHub repositories.

## Task Overview

The ML-Bench task presents a scenario where, given a GitHub repository, the language model has access to all files within the repository. Upon receiving a user instruction with a set of specific parameters, the Agent is required to write code that invokes models or functions from the GitHub repository. The generated code must align with the user's instruction, particularly in terms of the specified parameters, and must be executable.

The task introduces new challenges for LLMs, such as comprehending long and language-code interleaved documents, understanding complex cross-file code structures, and effectively navigating the codebase to locate relevant information. ML-Bench serves as a critical tool for assessing the efficiency and adaptability of various methods in real-world scenarios.

For more details on the ML-Bench task and dataset, please refer to the paper: [ML-Bench: Evaluating Large Language Models for Code Generation in Repository-Level Machine Learning Tasks](https://arxiv.org/abs/2311.09835).

## Setup Environment

Please follow the [OpenDevin setup guide](https://github.com/OpenDevin/OpenDevin/blob/main/docs/setup.md) to set up the local development environment for OpenDevin.

## Configure OpenDevin and your LLM

Create a `config.toml` file if it does not exist at the root of the workspace.

Add the following configurations:

```toml
[core]
max_iterations = 100
cache_dir = "/tmp/cache"
ssh_hostname = "localhost"
enable_auto_lint = true

# TODO: Change these to the model you want to evaluate
[eval_gpt4_1106_preview]
model = "gpt-4-1106-preview"
api_key = "XXX"
temperature = 0.0

[eval_some_openai_compatible_model]
model = "openai/MODEL_NAME"
base_url = "https://OPENAI_COMPATIBLE_URL/v1"
api_key = "XXX"
temperature = 0.0
```

## Run Inference on ML-Bench

To run the evaluation on the ML-Bench dataset, use the following command:

```bash
./evaluation/ml_bench/scripts/run_infer.sh eval_gpt4_1106_preview
```

You can replace `eval_gpt4_1106_preview` with any model you set up in `config.toml`.

## Examples

For each task in the ML-Bench dataset, OpenDevin provides the agent with a set number of iterations to complete the task. The `history` field in the evaluation output shows each iteration's response and actions taken by the agent to complete the task.

Here's an example of the evaluation output for a single task instance:

```json
{
    "instance_id": 1,
    "repo": "https://github.com/example/repo",
    "instruction": "Please complete the ML task specified in the README: https://github.com/example/repo/README.md\nThe task is: Implement a GNN model using DGL\n\nI am eager to utilize the Citeseer dataset as the training data to empower the ARMA Model with the learning rate set to a commendably small value of 0.Additionally, I'd like to incorporate 5 stacks into this model. Your assistance in formulating the necessary code to accomplish this task would be of tremendous help.\n\nReference:\nThe following commands learn a neural network and predict on the test set. Train an ARMA model which follows the original hyperparameters on different datasets.\n\n# Cora:\npython citation.py --gpu 0\n\n# Citeseer:\npython citation.py --gpu 0 --dataset Citeseer --num-stacks 3\n\n# Pubmed:\npython citation.py --gpu 0 --dataset Pubmed --dropout 0.25 --num-stacks 1\n\nYou should only modify files under the specified path in the repo.\nFollow the task arguments when running the training script:\n{\n  \"dataset\": \"Citeseer\",\n  \"lr\": \"0\",\n  \"num-stacks\": \"5\"\n}\n\nYou should terminate the subprocess after running the task (e.g., call subprocess.Popen(args).wait()).\nWhen you think you have completed the task, please run the following command: <execute_bash> exit </execute_bash>.\n",
    "metadata": {
        "agent_class": "CodeActAgent",
        "model_name": "gpt-4",
        "data_split": "test",
        "num_workers": 4
    },
    "history": [
        // ... agent's actions and observations ...
    ],
    "eval_exit_code": 0,
    "eval_output": "Accuracy: 0.85\nF1 Score: 0.92\n",
    "metrics": {
        "Accuracy": 0.85,
        "F1 Score": 0.92
    }
}
```

The `history` field contains the agent's actions and observations at each iteration, including the commands executed, file edits, and the agent's thoughts.

The `eval_exit_code` and `eval_output` fields provide information about the execution of the evaluation command and its output.

The `metrics` field contains the parsed evaluation metrics from the `eval_output`.

## Customization

You can customize the evaluation script by modifying the `evaluation/ml_bench/run_infer.py` file. This script handles loading the ML-Bench dataset, running the agent on each task instance, and saving the evaluation outputs.

Feel free to adjust the configuration, logging, and output formatting to suit your needs.

## Contributing

If you encounter any issues or have suggestions for improvements, please open an issue or submit a pull request on the [GitHub repository](https://github.com/yourusername/ML-Bench).

## License

This project is licensed under the [MIT License](LICENSE).
