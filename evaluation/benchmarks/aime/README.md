# AIME (American Invitational Mathematics Examination) Benchmark

## Overview

This benchmark evaluates the performance of AI agents on solving problems from the American Invitational Mathematics Examination (AIME). The AIME is a challenging high school mathematics competition in the United States, known for its difficult problems that require advanced problem-solving skills.

## Dataset

The dataset used for this benchmark is the [AIME 1983-2024 dataset](https://huggingface.co/datasets/gneubig/aime-1983-2024) available on Hugging Face. It contains AIME problems from 1983 to 2024, covering a wide range of advanced mathematical topics.

## Evaluation Process

The evaluation script (`run_infer.py`) performs the following steps:

1. Loads the AIME dataset from Hugging Face.
2. For each problem:
   - Presents the question to the AI agent.
   - Allows the agent to use Python and numerical libraries (e.g., numpy, sympy) to solve the problem.
   - Compares the agent's final answer with the correct answer.
3. Calculates the overall performance metrics.

## Running the Evaluation

To run the evaluation, use the following command:

```bash
python run_infer.py --llm_config <your_llm_config> --agent_cls CodeActAgent --max_iterations 50 --eval_n_limit 10 --eval_num_workers 1 --data-split train
```

You can adjust the parameters as needed:
- `--llm_config`: Specify the LLM configuration to use.
- `--agent_cls`: The agent class to evaluate (currently supports CodeActAgent).
- `--max_iterations`: Maximum number of iterations for each problem.
- `--eval_n_limit`: Number of problems to evaluate (use a smaller number for testing).
- `--eval_num_workers`: Number of worker processes for parallel evaluation.
- `--data-split`: The dataset split to use (e.g., 'train', 'test').

### Remote Runtime Support

This evaluation script supports running with a remote runtime. To use the remote runtime, set the following environment variables:

- `RUNTIME`: Set this to 'remote' to use the remote runtime (default is 'eventstream').
- `ALLHANDS_API_KEY`: Your API key for accessing the remote runtime.
- `SANDBOX_REMOTE_RUNTIME_API_URL`: The URL of the remote runtime API.

Example:

```bash
export RUNTIME=remote
export ALLHANDS_API_KEY=your_api_key_here
export SANDBOX_REMOTE_RUNTIME_API_URL=https://your-remote-runtime-url.com

python run_infer.py --llm_config <your_llm_config> --agent_cls CodeActAgent --max_iterations 50 --eval_n_limit 10 --eval_num_workers 1 --data-split train
```

Using the remote runtime can provide additional resources and potentially improve performance for complex mathematical computations.

## Output

The evaluation script generates an output file (`output.jsonl`) containing detailed results for each problem, including:
- The problem statement
- The agent's solution process
- The final answer provided by the agent
- Whether the answer was correct

## Metrics

The main metric for this benchmark is the accuracy of the agent's answers. An answer is considered correct if it exactly matches the integer answer provided in the dataset.

## Importance

The AIME benchmark is significant for several reasons:
1. It tests advanced mathematical problem-solving skills.
2. Problems often require creative thinking and novel approaches.
3. It covers a wide range of mathematical topics, including algebra, geometry, number theory, and combinatorics.
4. Success on this benchmark would indicate strong capabilities in mathematical reasoning and computation.

## Limitations

- The benchmark focuses on final answers and may not fully capture the quality of the problem-solving process.
- It requires the agent to format answers in a specific way, which may not always reflect real-world use cases.
- The problems are specific to the AIME format and may not generalize to all types of mathematical problem-solving.

## Future Work

- Implement a more detailed scoring system that considers partial credit for correct approaches.
- Expand the evaluation to include other mathematics competitions or problem sets.
- Develop methods to evaluate the quality and efficiency of the problem-solving process, not just the final answer.
