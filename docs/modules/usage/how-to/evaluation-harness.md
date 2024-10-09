# Evaluation

This guide provides an overview of how to integrate your own evaluation benchmark into the OpenHands framework.

## Setup Environment and LLM Configuration

Please follow instructions [here](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md) to setup your local development environment.
OpenHands in development mode uses `config.toml` to keep track of most configurations.

Here's an example configuration file you can use to define and use multiple LLMs:

```toml
[llm]
# IMPORTANT: add your API key here, and set the model to the one you want to evaluate
model = "claude-3-5-sonnet-20240620"
api_key = "sk-XXX"

[llm.eval_gpt4_1106_preview_llm]
model = "gpt-4-1106-preview"
api_key = "XXX"
temperature = 0.0

[llm.eval_some_openai_compatible_model_llm]
model = "openai/MODEL_NAME"
base_url = "https://OPENAI_COMPATIBLE_URL/v1"
api_key = "XXX"
temperature = 0.0
```


## How to use OpenHands in the command line

OpenHands can be run from the command line using the following format:

```bash
poetry run python ./openhands/core/main.py \
        -i <max_iterations> \
        -t "<task_description>" \
        -c <agent_class> \
        -l <llm_config>
```

For example:

```bash
poetry run python ./openhands/core/main.py \
        -i 10 \
        -t "Write me a bash script that prints hello world." \
        -c CodeActAgent \
        -l llm
```

This command runs OpenHands with:
- A maximum of 10 iterations
- The specified task description
- Using the CodeActAgent
- With the LLM configuration defined in the `llm` section of your `config.toml` file

## How does OpenHands work

The main entry point for OpenHands is in `openhands/core/main.py`. Here's a simplified flow of how it works:

1. Parse command-line arguments and load the configuration
2. Create a runtime environment using `create_runtime()`
3. Initialize the specified agent
4. Run the controller using `run_controller()`, which:
   - Attaches the runtime to the agent
   - Executes the agent's task
   - Returns a final state when complete

The `run_controller()` function is the core of OpenHands's execution. It manages the interaction between the agent, the runtime, and the task, handling things like user input simulation and event processing.


## Easiest way to get started: Exploring Existing Benchmarks

We encourage you to review the various evaluation benchmarks available in the [`evaluation/` directory](https://github.com/All-Hands-AI/OpenHands/blob/main/evaluation) of our repository.

To integrate your own benchmark, we suggest starting with the one that most closely resembles your needs. This approach can significantly streamline your integration process, allowing you to build upon existing structures and adapt them to your specific requirements.

## How to create an evaluation workflow


To create an evaluation workflow for your benchmark, follow these steps:

1. Import relevant OpenHands utilities:
   ```python
    import openhands.agenthub
    from evaluation.utils.shared import (
        EvalMetadata,
        EvalOutput,
        make_metadata,
        prepare_dataset,
        reset_logger_for_multiprocessing,
        run_evaluation,
    )
    from openhands.controller.state.state import State
    from openhands.core.config import (
        AppConfig,
        SandboxConfig,
        get_llm_config_arg,
        parse_arguments,
    )
    from openhands.core.logger import openhands_logger as logger
    from openhands.core.main import create_runtime, run_controller
    from openhands.events.action import CmdRunAction
    from openhands.events.observation import CmdOutputObservation, ErrorObservation
    from openhands.runtime.runtime import Runtime
   ```

2. Create a configuration:
   ```python
   def get_config(instance: pd.Series, metadata: EvalMetadata) -> AppConfig:
       config = AppConfig(
           default_agent=metadata.agent_class,
           runtime='eventstream',
           max_iterations=metadata.max_iterations,
           sandbox=SandboxConfig(
               base_container_image='your_container_image',
               enable_auto_lint=True,
               timeout=300,
           ),
       )
       config.set_llm_config(metadata.llm_config)
       return config
   ```

3. Initialize the runtime and set up the evaluation environment:
   ```python
   def initialize_runtime(runtime: Runtime, instance: pd.Series):
       # Set up your evaluation environment here
       # For example, setting environment variables, preparing files, etc.
       pass
   ```

4. Create a function to process each instance:
   ```python
   def process_instance(instance: pd.Series, metadata: EvalMetadata) -> EvalOutput:
       config = get_config(instance, metadata)
       runtime = create_runtime(config)
       initialize_runtime(runtime, instance)

       instruction = get_instruction(instance, metadata)

       state = run_controller(
           config=config,
           task_str=instruction,
           runtime=runtime,
           fake_user_response_fn=your_user_response_function,
       )

       # Evaluate the agent's actions
       evaluation_result = await evaluate_agent_actions(runtime, instance)

       return EvalOutput(
           instance_id=instance.instance_id,
           instruction=instruction,
           test_result=evaluation_result,
           metadata=metadata,
           history=state.history.compatibility_for_eval_history_pairs(),
           metrics=state.metrics.get() if state.metrics else None,
           error=state.last_error if state and state.last_error else None,
       )
   ```

5. Run the evaluation:
   ```python
   metadata = make_metadata(llm_config, dataset_name, agent_class, max_iterations, eval_note, eval_output_dir)
   output_file = os.path.join(metadata.eval_output_dir, 'output.jsonl')
   instances = prepare_dataset(your_dataset, output_file, eval_n_limit)

   await run_evaluation(
       instances,
       metadata,
       output_file,
       num_workers,
       process_instance
   )
   ```

This workflow sets up the configuration, initializes the runtime environment, processes each instance by running the agent and evaluating its actions, and then collects the results into an `EvalOutput` object. The `run_evaluation` function handles parallelization and progress tracking.

Remember to customize the `get_instruction`, `your_user_response_function`, and `evaluate_agent_actions` functions according to your specific benchmark requirements.

By following this structure, you can create a robust evaluation workflow for your benchmark within the OpenHands framework.


## Understanding the `user_response_fn`

The `user_response_fn` is a crucial component in OpenHands's evaluation workflow. It simulates user interaction with the agent, allowing for automated responses during the evaluation process. This function is particularly useful when you want to provide consistent, predefined responses to the agent's queries or actions.


### Workflow and Interaction

The correct workflow for handling actions and the `user_response_fn` is as follows:

1. Agent receives a task and starts processing
2. Agent emits an Action
3. If the Action is executable (e.g., CmdRunAction, IPythonRunCellAction):
   - The Runtime processes the Action
   - Runtime returns an Observation
4. If the Action is not executable (typically a MessageAction):
   - The `user_response_fn` is called
   - It returns a simulated user response
5. The agent receives either the Observation or the simulated response
6. Steps 2-5 repeat until the task is completed or max iterations are reached

Here's a more accurate visual representation:

```
                 [Agent]
                    |
                    v
               [Emit Action]
                    |
                    v
            [Is Action Executable?]
           /                       \
         Yes                        No
          |                          |
          v                          v
     [Runtime]               [user_response_fn]
          |                          |
          v                          v
  [Return Observation]    [Simulated Response]
           \                        /
            \                      /
             v                    v
           [Agent receives feedback]
                    |
                    v
         [Continue or Complete Task]
```

In this workflow:

- Executable actions (like running commands or executing code) are handled directly by the Runtime
- Non-executable actions (typically when the agent wants to communicate or ask for clarification) are handled by the `user_response_fn`
- The agent then processes the feedback, whether it's an Observation from the Runtime or a simulated response from the `user_response_fn`

This approach allows for automated handling of both concrete actions and simulated user interactions, making it suitable for evaluation scenarios where you want to test the agent's ability to complete tasks with minimal human intervention.

### Example Implementation

Here's an example of a `user_response_fn` used in the SWE-Bench evaluation:

```python
def codeact_user_response(state: State | None) -> str:
    msg = (
        'Please continue working on the task on whatever approach you think is suitable.\n'
        'If you think you have solved the task, please first send your answer to user through message and then <execute_bash> exit </execute_bash>.\n'
        'IMPORTANT: YOU SHOULD NEVER ASK FOR HUMAN HELP.\n'
    )

    if state and state.history:
        # check if the agent has tried to talk to the user 3 times, if so, let the agent know it can give up
        user_msgs = [
            event
            for event in state.history.get_events()
            if isinstance(event, MessageAction) and event.source == 'user'
        ]
        if len(user_msgs) >= 2:
            # let the agent know that it can give up when it has tried 3 times
            return (
                msg
                + 'If you want to give up, run: <execute_bash> exit </execute_bash>.\n'
            )
    return msg
```

This function does the following:

1. Provides a standard message encouraging the agent to continue working
2. Checks how many times the agent has attempted to communicate with the user
3. If the agent has made multiple attempts, it provides an option to give up

By using this function, you can ensure consistent behavior across multiple evaluation runs and prevent the agent from getting stuck waiting for human input.
