# Tutorial: How to add a New Evaluation Benchmark to OpenDevin

This tutorial provides a general guide on how to integrate your own evaluation benchmark into the OpenDevin framework.


## A quick walk-through of OpenDevin architecture

### Before everything begins

Please follow [this document](https://github.com/OpenDevin/OpenDevin/blob/main/Development.md) to setup local develop environment for OpenDevin.

### Configuration file

OpenDevin uses `config.toml` to keep track of most configurations.

Here's an example configuration file you can use:

```toml
[core]
max_iterations = 100
cache_dir = "/tmp/cache"

# IMPORTANT: You should set these two paths to YOUR WORKSPACE directory,
# which will be mounted into Sandbox for agent to interact with!
# The OpenDevin agent will be able to read/write files whatever they like (even rm -rf)
# in this directory, so be careful!!
workspace_base = "/path/to/your/workspace"
workspace_mount_path = "/path/to/your/workspace"
# ==========================

sandbox_container_image = "ghcr.io/opendevin/sandbox:latest"
run_as_devin = true
sandbox_type = "ssh"
use_host_network = true
ssh_hostname = "localhost"
sandbox_timeout = 120

[llm]
# IMPORTANT: add your API key here, and set the model to the one you want to evaluate
model = "gpt-4o-2024-05-13"
api_key = "sk-XXX"
```

### How do OpenDevin solves a task?

In this section, for the purpose of building an evaluation task, we omit details on the frontend and backend that mostly contains logic for user interface, and mainly focus on a function `main` (i.e., a command line interface) that allows you to complete a task end-to-end.

For example, *without any frontend/backend server*, you can run ([setup the environment first](#before-everything-begins) if you haven't) the following to get a simple task solved (with max number of 10 iterations, `CodeActAgent` as the agent, and `gpt-4o-2024-05-13` as the LLM):

```bash
poetry run python ./opendevin/core/main.py \
        -i 10 \
        -t "Write me a bash script that print hello world." \
        -c CodeActAgent \
        -m gpt-4o-2024-05-13
```

After running the script, you will observe the following:

![](./static/example_task_1.png)

You can see the agent uses bash to write a script, making it executable, and then tested it by running it to make sure it is working.

## What is "Request user input"?

At the end of the above screenshot, OpenDevin actually requests user inputs when it think it finishes the task. There are multiple motivations for this design:

1. If the agent did something wrong, the user can follow-up with language feedback to correct it.

2. If the agent did something good, the user may want to follow-up with additional problem for it to solve.

3. If the agent completes the user's task -- in a realistic setting, the user might just turn off OpenDevin application and work on something else. User could also type in "/exit" to gracefully shutdown the OpenDevin agent.

However, this will actually causes issues in evaluation, since most evaluation don't actually assume additional user input.

To fix this, we introduce the functionality of `fake_user_response_fn` in the `main` fucntion. Check the section below for more details!

## How does `main` work?

The signature of `main` (in file [[`opendevin/core/main.py`](../opendevin/core/main.py)]):

```python
async def main(
    task_str: str = '',
    exit_on_message: bool = False,
    fake_user_response_fn: Optional[Callable[[Optional[State]], str]] = None,
    sandbox: Optional[Sandbox] = None,
) -> Optional[State]:
```

- `task_str`: The task instruction to run. In the above example, it is "Write me a bash script that print hello world."
- `exit_on_message`: quit if agent asks for a message from user (optional)
- `fake_user_response_fn`: An optional function that receives the current state (could be None) and returns a fake user response.
- `sandbox`: An optional sandbox to run the agent in.

### `fake_user_response_fn`

Here's an example of `fake_user_response_fn` in the implementation for SWE-Bench in [`evaluation/swe_bench/run_infer.py`](swe_bench/run_infer.py):

```python
def codeact_user_response(state: State) -> str:
    msg = (
        'Please continue working on the task on whatever approach you think is suitable.\n'
        'If you think you have modified the code in a way that fixes the issue, please run the following command: <execute_bash> exit </execute_bash>.\n'
        'IMPORTANT: YOU SHOULD NEVER ASK FOR HUMAN HELP OR USE THE INTERNET TO SOLVE THIS TASK.\n'
    )
    if state.history:
        user_msgs = [
            action
            for action, _ in state.history
            if isinstance(action, MessageAction) and action.source == 'agent'
        ]
        if len(user_msgs) >= 2:
            # let the agent know that it can give up when it has tried 3 times
            return (
                msg
                + 'If you want to give up, run: <execute_bash> exit </execute_bash>.\n'
            )
    return msg
```

It receives a `State`, which is defined in [`opendevin/controller/state/state.py`](../opendevin/controller/state/state.py). We are mainly using `state.history` here, which is the most important field of data. You can imagine it is being a more structured version of OpenAI's chat completion [messages](https://platform.openai.com/docs/guides/text-generation/chat-completions-api).

`history: list[tuple[Action, Observation]] = field(default_factory=list)` is a list of (action, observation) tuple. All the actions are defined at [`opendevin/events/action`](../opendevin/events/action) and observations are defined at [`opendevin/events/observation`](../opendevin/events/action).

The agent can emit different actions like `CmdRunAction`  (`opendevin/events/action/commands.py`) to execute bash commands and receive `CmdOutputObservation` (`opendevin/events/observation/commands.py`), `IPythonRunCellAction` to receive `IPythonRunCellObservation`, `BrowseInteractiveAction` (`opendevin/events/action/browse.py`) to browse the web and receive `BrowserOutputObservation` (`opendevin/events/observation/browse.py`).

The action we used in this example is `MessageAction` (`opendevin/events/action/message.py`), which actually denotes a message from either `agent` or `user`. In the [CodeAct agent example](https://github.com/OpenDevin/OpenDevin/blob/7ca560471bd262f22513f3863995d0a8e6121c07/agenthub/codeact_agent/codeact_agent.py#L239-L273), an agent is considered to emit a `MessageAction` when it does not trigger a `CmdRunAction`, `IPythonRunCellAction`, and/or `BrowseInteractiveAction`.

Typically, the agent returns `MessageAction` when it is confused about the task, and want to ask human for follow-up clarification, which is a good thing in real-world task, but not necessarily in evaluation. So in this example, we provide a dummy prompt to tell the agent "Please continue working on the task on whatever approach you think is suitable[...]".

If you see something like this, you can consider adding this to your evaluation pipeline as well.

### `sandbox`

Sandbox is a fully functioning docker container where the agent can perform all sorts of tasks, e.g., using bash, calling Python, install packages, and more. You can leave `sandbox` to `None` if you don't need to do anything special to pre-configure the `Sandbox`.

In SWE-Bench, we need to copy the proper repository directory to the workspace and activate the right python virtual environment before the agent can start performing the task, so we actually defined a custom [`SWEBenchSSHBox`](https://github.com/OpenDevin/OpenDevin/blob/7ca560471bd262f22513f3863995d0a8e6121c07/evaluation/swe_bench/swe_env_box.py#L12-L118) that inherit from the default sandbox [`SSHBox`](https://github.com/OpenDevin/OpenDevin/blob/main/opendevin/runtime/docker/ssh_box.py#L188) and handles all these initial setup. If you need to configure the `sandbox` for your evaluation, check `SWEBenchSSHBox` for a reference of implementation.

## How to put together an evaluation script?

Now we have know how to start running the agent end-to-end, and how `fake_user_response_fn` and `sandbox` works. We will walk through a piece of dummy code (simplified version of SWE-Bench's [`run_infer.py`](https://github.com/OpenDevin/OpenDevin/blob/main/evaluation/swe_bench/run_infer.py)) that outline the general workflow:

- Load the dataset and prepare the evaluation configuration.
- Filter out any instances that have already been processed.
- For each instance in the dataset:
  - Set up the sandbox environment.
  - Run the agent to generate a solution.
  - Apply the solution to the instance and execute the test command.
  - Collect the results and write them to the output file.
- Perform cleanup after the evaluation is complete.

By following this workflow and implementing the key components, you can integrate your own evaluation benchmark into the OpenDevin framework.


```python
import asyncio
import json
import logging
import multiprocessing as mp
import os
import pathlib
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor

import pandas as pd
import whatthepatch
from datasets import load_dataset
from tqdm import tqdm

from evaluation.swe_bench.swe_env_box import SWEBenchSSHBox
from opendevin.controller.state.state import State
from opendevin.core.config import args, config, get_llm_config_arg
from opendevin.core.logger import get_console_handler
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.main import main
from opendevin.events.action import MessageAction
from opendevin.events.serialization.event import event_to_dict


def cleanup():
    print('Cleaning up child processes...')
    for process in mp.active_children():
        print(f'Terminating child process: {process.name}')
        process.terminate()
        process.join()


def codeact_user_response(state: State) -> str:
    msg = (
        'Please continue working on the task on whatever approach you think is suitable.\n'
        'If you think you have modified the code in a way that fixes the issue, please run the following command: <execute_bash> exit </execute_bash>.\n'
        'IMPORTANT: YOU SHOULD NEVER ASK FOR HUMAN HELP OR USE THE INTERNET TO SOLVE THIS TASK.\n'
    )
    if state.history:
        user_msgs = [
            action
            for action, _ in state.history
            if isinstance(action, MessageAction) and action.source == 'user'
        ]
        if len(user_msgs) >= 2:
            # let the agent know that it can give up when it has tried 3 times
            return (
                msg
                + 'If you want to give up, run: <execute_bash> exit </execute_bash>.\n'
            )
    return msg


def monologue_user_response(state: State) -> str:
    raise NotImplementedError('MonologueAgent should never ask for user responses.')


AGENT_CLS_TO_FAKE_USER_RESPONSE_FN = {
    'CodeActAgent': codeact_user_response,
    'MonologueAgent': monologue_user_response,
}

AGENT_CLS_TO_INST_SUFFIX = {
    'CodeActAgent': 'When you think you have fixed the issue through code changes, please run the following command: <execute_bash> exit </execute_bash>.\n'
}


def get_test_result(instance, sandbox, workspace_dir_name):
    test_result = {'result': {}, 'metadata': {}}
    # TODO: if you need to do something in the sandbox to get the correctness metric, modify this function
    return test_result


def process_instance(
    instance, agent_class, metadata, skip_workspace_mount, reset_logger: bool = True
):
    workspace_mount_path = os.path.join(config.workspace_mount_path, '_eval_workspace')
    # create process-specific workspace dir
    # if `not skip_workspace_mount` - we will create a workspace directory for EACH process
    # so that different agent don't interfere with each other.
    if not skip_workspace_mount:
        workspace_mount_path = os.path.join(workspace_mount_path, str(os.getpid()))
        pathlib.Path(workspace_mount_path).mkdir(parents=True, exist_ok=True)

    # Setup the logger properly, so you can run multi-processing to parallize the evaluation
    if reset_logger:
        # Set up logger
        log_file = os.path.join(
            eval_output_dir, 'logs', f'instance_{instance.instance_id}.log'
        )
        # Remove all existing handlers from logger
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        # add back the console handler to print ONE line
        logger.addHandler(get_console_handler())
        logger.info(
            f'Starting evaluation for instance {instance.instance_id}.\nLOG:   tail -f {log_file}'
        )
        # Remove all existing handlers from logger
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(file_handler)

    if not skip_workspace_mount:
        logger.info(f'Process-specific workspace mounted at {workspace_mount_path}')

    # NOTE: this is something special we do for SWE-Bench due to the reason described in the previous section
    # You can omit this if you don't need to setup specialized sandbox
    workspace_dir_name = f'{instance.repo}__{instance.version}'.replace('/', '__')
    sandbox = SWEBenchSSHBox.get_box_for_instance(
        instance,
        workspace_dir_name,
        skip_workspace_mount=skip_workspace_mount,
        workspace_mount_path=workspace_mount_path,
    )

    # Prepare instruction
    instruction = (
        f'Please fix the following issue for the repository in /workspace/{workspace_dir_name}.\n'
        'Environment has been set up for you to start working. You may assume all necessary tools are installed.\n\n'
        '# Problem Statement\n'
        f'{instance.problem_statement}\n\n'
    )
    if instance.hints_text:
        instruction += f'# Hints\n{instance.hints_text}\n\n'
    instruction += (
        'IMPORTANT: You should ONLY interact with the environment provided to you AND NEVER ASK FOR HUMAN HELP.\n'
        'You should NOT modify any existing test case files. If needed, you can add new test cases in a NEW file to reproduce the issue.\n'
        'You SHOULD INCLUDE PROPER INDENTATION in your edit commands.\n'
    )
    # NOTE: You can actually set slightly different instruction for different agents
    instruction += AGENT_CLS_TO_INST_SUFFIX.get(agent_class, '')

    # Here's how you can run the agent (similar to the `main` function) and get the final task state
    state: State = asyncio.run(
        main(
            instruction,
            fake_user_response_fn=AGENT_CLS_TO_FAKE_USER_RESPONSE_FN.get(agent_class),
            sandbox=sandbox,
        )
    )

    # ======= THIS IS SWE-Bench specific =======
    # Get git patch
    git_patch = sandbox.get_diff_patch()
    logger.info(f'Got git diff for instance {instance.instance_id}')
    # ==========================================

    # ======= Attempt to evaluate the agent's edits =======
    # TODO: if you need to do something in the sandbox to get the correctness metric, modify this function
    test_result = get_test_result(instance, sandbox, workspace_dir_name)

    # If you are working on simplier benchmark that only evaluates the final model output (e.g., in a MessageAction)
    # You can simply get the LAST `MessageAction` from the returned `state.history` and parse it for evaluation.

    if state is None:
        raise ValueError('State should not be None.')

    # Save the output
    output = {
        'instance_id': instance.instance_id,
        'swe_instance': instance.to_dict(),  # SWE Bench specific
        'instruction': instruction,
        'git_patch': git_patch, # SWE Bench specific
        'metadata': metadata,
        'history': [
            (event_to_dict(action), event_to_dict(obs)) for action, obs in state.history
        ],
        'error': state.error if state and state.error else None,
        'test_result': test_result,
    }

    # Close the sandbox
    sandbox.close()
    return output


if __name__ == '__main__':
    # NOTE: It is preferable to load datasets from huggingface datasets and perform post-processing
    # so we don't need to manage file uploading to OpenDevin's repo
    dataset = load_dataset('princeton-nlp/SWE-bench_Lite')
    swe_bench_tests = dataset['test'].to_pandas()

    # Check https://github.com/OpenDevin/OpenDevin/blob/main/evaluation/swe_bench/README.md#configure-opendevin-and-your-llm
    # for details of how to set `llm_config`
    if args.llm_config:
        specified_llm_config = get_llm_config_arg(args.llm_config)
        if specified_llm_config:
            config.llm = specified_llm_config
    logger.info(f'Config for evaluation: {config}')

    # TEST METADATA
    agent_class = args.agent_cls
    assert (
        agent_class in AGENT_CLS_TO_FAKE_USER_RESPONSE_FN
    ), f'Unsupported agent class: {agent_class}'
    model_name = config.llm.model.split('/')[-1]
    max_iterations = args.max_iterations
    eval_note = ''
    if args.eval_note is not None:
        eval_note += '_N_' + args.eval_note
    eval_output_dir = os.path.join(
        args.eval_output_dir,
        'swe_bench',
        agent_class,
        model_name + '_maxiter_' + str(max_iterations) + eval_note,
    )

    pathlib.Path(eval_output_dir).mkdir(parents=True, exist_ok=True)
    pathlib.Path(os.path.join(eval_output_dir, 'logs')).mkdir(
        parents=True, exist_ok=True
    )
    logger.info(f'Using evaluation output directory: {eval_output_dir}')

    metadata = {
        'agent_class': agent_class,
        'model_name': model_name,
        'max_iterations': max_iterations,
        'eval_output_dir': eval_output_dir,
        'start_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        # get the commit id of current repo for reproduciblity
        'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'])
        .decode('utf-8')
        .strip(),
    }
    logger.info(f'Metadata: {metadata}')
    with open(os.path.join(eval_output_dir, 'metadata.json'), 'w') as f:
        json.dump(metadata, f)

    # LIMIT EVALUATION
    eval_n_limit = args.eval_n_limit
    if eval_n_limit:
        swe_bench_tests = swe_bench_tests.head(eval_n_limit)
        logger.info(f'Limiting evaluation to first {eval_n_limit} instances.')

    # OUTPUT FILE
    output_file = os.path.join(eval_output_dir, 'output.jsonl')
    logger.info(f'Writing evaluation output to {output_file}')
    finished_instance_ids = set()
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            for line in f:
                data = json.loads(line)
                finished_instance_ids.add(data['instance_id'])
        logger.warning(
            f'Output file {output_file} already exists. Loaded {len(finished_instance_ids)} finished instances.'
        )
    output_fp = open(output_file, 'a')

    logger.info(
        f'Evaluation started with Agent {agent_class}, model {model_name}, max iterations {max_iterations}.'
    )

    # =============================================
    # filter out finished instances
    new_swe_bench_tests = []
    for idx, instance in swe_bench_tests.iterrows():
        if instance.instance_id in finished_instance_ids:
            logger.info(
                f'Skipping instance {instance.instance_id} as it is already finished.'
            )
            continue
        new_swe_bench_tests.append(instance)

    swe_bench_tests = pd.DataFrame(new_swe_bench_tests)
    logger.info(
        f'Finished instances: {len(finished_instance_ids)}, Remaining instances: {len(swe_bench_tests)}'
    )
    # =============================================

    pbar = tqdm(total=len(swe_bench_tests))

    # This function tracks the progress AND write the output to a JSONL file
    def update_progress(future):
        pbar.update(1)
        output = future.result()
        pbar.set_description(f'Instance {output["instance_id"]}')
        pbar.set_postfix_str(f'Test Result: {output["test_result"]["result"]}')
        logger.info(
            f'Finished evaluation for instance {output["instance_id"]}: {output["test_result"]["result"]}'
        )
        output_fp.write(json.dumps(output) + '\n')
        output_fp.flush()

    # This sets the multi-processing
    num_workers = args.eval_num_workers
    logger.info(f'Using {num_workers} workers for evaluation.')

    # This is SWE-Bench specific - CodeActAgent don't requires mounted workspace to work
    skip_workspace_mount = agent_class == 'CodeActAgent'
    logger.info(f'Skipping workspace mount: {skip_workspace_mount}')

    try:
        with ProcessPoolExecutor(num_workers) as executor:
            futures = []
            # This is how we perform multi-processing
            for row_idx, instance in swe_bench_tests.iterrows():
                future = executor.submit(
                    process_instance,
                    instance,
                    agent_class,
                    metadata,
                    skip_workspace_mount,
                    reset_logger=bool(num_workers > 1),
                )
                future.add_done_callback(update_progress)
                futures.append(future)

            # Wait for all futures to complete
            for future in futures:
                future.result()
    except KeyboardInterrupt:
        print('KeyboardInterrupt received. Cleaning up...')
        cleanup()

    output_fp.close()
    logger.info('Evaluation finished.')
```

When you fully understand the `run_infer.py`, you can be ready to actually starting the evaluation!


## Run the evaluation!

Similar to SWE-Bench's [`run_infer.sh`](https://github.com/OpenDevin/OpenDevin/blob/main/evaluation/swe_bench/scripts/run_infer.sh), you can write your script similarily:

```bash
#!/bin/bash

AGENT=CodeActAgent
# IMPORTANT: Because Agent's prompt changes fairly often in the rapidly evolving codebase of OpenDevin
# We need to track the version of Agent in the evaluation to make sure results are comparable
AGENT_VERSION=v$(python3 -c "from agenthub.codeact_agent import CodeActAgent; print(CodeActAgent.VERSION)")
MODEL_CONFIG=$1

echo "AGENT: $AGENT"
echo "AGENT_VERSION: $AGENT_VERSION"
echo "MODEL_CONFIG: $MODEL_CONFIG"

# You should add $MODEL_CONFIG in your `config.toml`

poetry run python3 evaluation/swe_bench/run_infer.py \
  --agent-cls $AGENT \
  --llm-config $MODEL_CONFIG \
  --max-iterations 50 \
  --max-chars 10000000 \
  --eval-num-workers 8 \
  --eval-note $AGENT_VERSION
```

You can start the evaluation by running:

```bash
./run_infer.sh eval_gpt4_1106_preview
```

Where `eval_gpt4_1106_preview` is the model config you defined on the `config.toml`.
