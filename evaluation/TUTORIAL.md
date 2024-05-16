# Adding a New Evaluation Benchmark to OpenDevin

This tutorial provides a general guide on how to integrate your own evaluation benchmark into the OpenDevin framework.

## Key Components

To integrate a new evaluation benchmark, you need to implement the following key components:

1. **Dataset Loading**: Load your dataset and convert it into a format that can be processed by the evaluation script. This often involves converting datasets to pandas DataFrames.

2. **Configuration**: Set up the configuration for your evaluation, including the model to be evaluated, the number of iterations, and any other relevant parameters.

3. **Metadata Preparation**: Prepare metadata for the evaluation run, which includes information such as the agent class, model name, and the commit ID of the repository.

4. **Instance Processing**: Implement a function to process each instance of the evaluation. This function should handle the logic for running the agent, applying patches, reverting changes, and executing test commands.

5. **Sandbox Environment**: Set up a sandbox environment where the evaluation will be run. This ensures that the evaluation is performed in a controlled and isolated setting.

6. **Result Collection**: Collect and store the results of the evaluation. This typically involves writing the results to a file in a structured format like JSON.

7. **Parallel Execution**: Utilize parallel processing to run the evaluation on multiple instances simultaneously. This can significantly speed up the evaluation process.

8. **Progress Monitoring**: Implement a progress bar or another form of logging to monitor the evaluation process.

9. **Cleanup**: Define a cleanup procedure to terminate any child processes and perform necessary cleanup after the evaluation run.

## Workflow

The general workflow for running an evaluation benchmark is as follows:

- Load the dataset and prepare the evaluation configuration.
- Filter out any instances that have already been processed.
- For each instance in the dataset:
  - Set up the sandbox environment.
  - Run the agent to generate a solution.
  - Apply the solution to the instance and execute the test command.
  - Collect the results and write them to the output file.
- Monitor the progress of the evaluation and handle any exceptions.
- Perform cleanup after the evaluation is complete.

By following this workflow and implementing the key components, you can integrate your own evaluation benchmark into the OpenDevin framework.


## Example Code Snippets

Below are example code snippets for each key component mentioned above:

### 1. Dataset Loading
```python
from datasets import load_dataset
import pandas as pd

# Load your dataset
dataset = load_dataset('your_dataset_name')
# Convert to pandas DataFrame
df = dataset['test'].to_pandas()
```

### 2. Configuration
```python
from opendevin.core.config import config

# Set up evaluation configuration
config.llm.model = 'your_model_name'
config.eval.max_iterations = 100
```

### 3. Metadata Preparation
```python
import time
import subprocess

# Prepare metadata
metadata = {
    'agent_class': 'YourAgentClass',
    'model_name': config.llm.model.split('/')[-1],
    'max_iterations': config.eval.max_iterations,
    'start_time': time.strftime('%Y-%m-%d %H:%M:%S'),
    'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf-8').strip(),
}
```

### 4. Instance Processing
```python
def process_instance(instance, agent_class, metadata):
    # Set up sandbox, run agent, apply patch, revert changes, execute test command
    # Collect results and return them
    pass
```

### 5. Sandbox Environment Using SSHBox
The `SSHBox` class provides a way to interact with a Docker container via SSH, which can be used to create a sandbox environment for running evaluations. Here is an example of how to use `SSHBox`:

```python
from opendevin.runtime.docker.ssh_box import SSHBox

# Initialize the SSHBox with necessary configurations
sandbox = SSHBox(image_name="your_docker_image",
                 ssh_key_path="path_to_ssh_key",
                 volume_mappings={"host_path": "container_path"})

# Start the sandbox environment
sandbox.start()

# Execute commands within the sandbox
exit_code, output = sandbox.execute("your_command_here")

# Stop the sandbox environment when done
sandbox.stop()
```

By using `SSHBox`, you can ensure that each evaluation instance runs in a clean, controlled environment, which is essential for consistent and reliable evaluation results.

### 5. Sandbox Environment
```python
from evaluation.swe_bench.swe_env_box import SWEBenchSSHBox

# Set up a sandbox environment
sandbox = SWEBenchSSHBox()
```

### 6. Result Collection
```python
# Collect and store results
results = {
    'instance_id': instance_id,
    'result': test_result,
    'metadata': metadata,
}

# Write results to a file
with open(output_file, 'a') as f:
    json.dump(results, f)
    f.write('\n')
```

### 7. Parallel Execution
```python
from concurrent.futures import ProcessPoolExecutor

# Use ProcessPoolExecutor for parallel execution
with ProcessPoolExecutor(max_workers) as executor:
    futures = [executor.submit(process_instance, instance, agent_class, metadata) for instance in instances]
```

### 8. Progress Monitoring
```python
from tqdm import tqdm

# Set up a progress bar
pbar = tqdm(total=len(instances))
```

### 9. Cleanup
```python
import multiprocessing as mp

# Cleanup function to terminate child processes
def cleanup():
    for process in mp.active_children():
        process.terminate()
        process.join()
```

By including these example code snippets in your implementation, you can create a new evaluation benchmark that fits within the OpenDevin framework.


### Detailed Instance Processing
When processing an instance, the following steps are typically involved:

- **Set Up Sandbox**: Create an isolated environment where the evaluation will be run. This is crucial for ensuring that the evaluation does not interfere with the host system or other evaluations.

- **Run Agent**: Execute the agent that will attempt to solve the instance. This could involve generating code, making predictions, or performing any task that the agent is designed to do.

- **Apply Patch**: If the evaluation involves code changes, apply a patch to the codebase within the sandbox. This simulates the effect of the agent's proposed solution.

- **Revert Changes**: Before applying new changes, revert any previous changes to the codebase to ensure that each test is run from a clean state.

- **Execute Test Command**: Run a command to test whether the agent's solution is correct. This could be a build process, a set of unit tests, or any other verification process.

