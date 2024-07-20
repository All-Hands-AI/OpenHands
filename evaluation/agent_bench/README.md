# AgentBench Evaluation

This folder contains evaluation harness for evaluating agents on
the [AgentBench: Evaluating LLMs as Agents](https://arxiv.org/abs/2308.03688).

## Configure OpenDevin and your LLM

Create a `config.toml` file if it does not exist at the root of the workspace. Please check [README.md](../../README.md)
for how to set this up.

Here is an example `config.toml` file:

```toml
[core]
max_iterations = 100
cache_dir = "/path/to/cache"

workspace_base = "/path/to/workspace"
workspace_mount_path = "/path/to/workspace"

ssh_hostname = "localhost"

# AgentBench specific
run_as_devin = true

[sandbox]
use_host_network = false
enable_auto_lint = true
box_type = "ssh"
timeout = 120

[llm.eval_gpt35_turbo]
model = "gpt-3.5-turbo"
api_key = "sk-123"
temperature = 0.0

[llm.eval_gpt4o]
model = "gpt-4o"
api_key = "sk-123"
temperature = 0.0
```

## Start the evaluation

```bash
./evaluation/agent_bench/scripts/run_infer.sh [model_config] [git-version] [agent] [eval_limit]
```

Following is the basic command to start the evaluation. Here we are only evaluating the `osbench` for now.

You can update the arguments in the script `evaluation/agent_bench/scripts/run_infer.sh`, such as `--max-iterations`, `--eval-num-workers` and so on.

- `--agent-cls`, the agent to use. For example, `CodeActAgent`.
- `--llm-config`: the LLM configuration to use. For example, `eval_gpt4_1106_preview`.
- `--max-iterations`: the number of iterations to run the evaluation. For example, `30`.
- `--eval-num-workers`: the number of workers to use for evaluation. For example, `5`.
- `--eval-n-limit`: the number of examples to evaluate. For example, `100`.

```bash
./evaluation/agent_bench/scripts/run_infer.sh eval_gpt35_turbo 0.6.2 CodeActAgent 1
```
