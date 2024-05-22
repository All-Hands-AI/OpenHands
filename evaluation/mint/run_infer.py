import asyncio
import json
import logging
import multiprocessing as mp
import os
import pathlib
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor

from datasets import load_dataset
from tqdm import tqdm

from evaluation.swe_bench.swe_env_box import DockerSSHBox
from opendevin.controller.state.state import State
from opendevin.core.config import config, get_llm_config_arg, get_parser
from opendevin.core.logger import get_console_handler
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.main import main
from opendevin.events.action import MessageAction


def cleanup():
    print('Cleaning up child processes...')
    for process in mp.active_children():
        print(f'Terminating child process: {process.name}')
        process.terminate()
        process.join()


def codeact_user_response(state: State):
    msg = (
        'Please continue working on the task on whatever approach you think is suitable.\n'
        'If you think you have modified the code in a way that fixes the issue, please run the following command: <execute_bash> exit </execute_bash>.\n'
        'IMPORTANT: YOU SHOULD NEVER ASK FOR HUMAN HELP OR USE THE INTERNET TO SOLVE THIS TASK.\n'
    )
    if state.history:
        user_msgs = [
            action
            for action, obs in state.history
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
    'CodeActAgent': 'When you think you have solved the question, please first send your answer to user through message, remember to wrap it inside <solution> tag, and then exit using the following command: <execute_bash> exit </execute_bash>.\n'
}


def process_instance(
    instance,
    agent_class,
    metadata,
    skip_workspace_mount,
    eval_output_dir,
    reset_logger: bool = True,
):
    print('Processing instance:', instance)

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
            eval_output_dir, 'logs', f'instance_{instance['id']}.log'
        )
        # Remove all existing handlers from logger
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        # add back the console handler to print ONE line
        logger.addHandler(get_console_handler())
        logger.info(
            f'Starting evaluation for instance {instance['id']}.\nHint: run "tail -f {log_file}" to see live logs in a seperate shell'
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

    sandbox = DockerSSHBox()

    # Prepare instruction
    instruction = (
        """You are a helpful assistant assigned with the task of problem-solving.
To solve the task, you can only interact with the interactive Python (Jupyter Notebook) environment using <execute_ipython> tag. Other tools cannot be used.
At each turn, you should first provide your step-by-step thinking for solving the task. Your thought process should be enclosed using "<thought>" tag, for example: <thought> I need to print "Hello World!" </thought>.
After that, you have two options:
1) Interact with a Python programming environment and receive the corresponding output.
2) Directly provide a solution by sending your answer to user through message that adheres to the required format for the given task. Your solution should be enclosed using "<solution>" tag, for example: The answer is <solution> A </solution>.

---

Task:
Evaluate $\\int\\int_C (x+y)^2 dx,dy$, where C is the circle defined by $x^2 + y^2 = M$, and M is the birth year of Li Bai.
Output format requirement: Round to three decimal places, using half up rounding rule.

Assistant:
<thought> To solve this problem, let's start by determining Li Bai's birth year. </thought>
<execute> print(wikipedia_search('Li Bai')) </execute>

Observation:
Page: Li Bai
Summary: Li Bai (Chinese: 李白; pinyin: Lǐ Bái, 701–762), also pronounced as Li Bo, courtesy name Taibai (Chinese: 太白), was a Chinese poet, acclaimed from his own time to the present as a brilliant and romantic figure who took traditional poetic forms to new heights.

Assistant:
<thought>
From the wiki_search result, we can see that Li Bai was born in 701, thus M = 701.
To evaluate the double integral of $(x+y)^2$ over the region $C$, where $C$ is the circle defined by $x^2 + y^2 = 701$, we should use polar coordinates.
In polar coordinates, $x = r\\cos(\theta)$ and $y = r\\sin(\theta)$, and the differential area element $dx,dy$ becomes $r,dr,d\theta$.
$\\int\\int_C (x+y)^2 dx,dy = \\int_0^{2\\pi}\\int_0^{\\sqrt{701}} (r\\cos(\theta) + r\\sin(\theta))^2r,dr,d\theta$
Let's use the SymPy package to calculate this.
</thought>
<execute>
from sympy import symbols, integrate, cos, sin, pi

r, theta = symbols('r theta')

# the integrand
integrand = (r*cos(theta) + r*sin(theta))**2 * r

# perform the double integration
double_integral = integrate(integrate(integrand, (r, 0, 701 ** 0.5)), (theta, 0, 2*pi))
print(double_integral)
</execute>

Observation:
Out[2]: 245700.5*pi

Assistant:
<thought> Let's round this result to three decimal places using half up rounding rule. </thought>
<execute>
import math
print(round(245700.5*math.pi, 3))
</execute>

Observation:
771890.886

Assistant:
The answer is <solution> 771890.886 </solution>.

---"""
        f'You have {5} chances to interact with the environment or propose a solution. You can only propose a solution {2} times.'
        '# Problem statement: \n'
        f"{instance['prompt']}\n\n"
    )
    instruction += 'IMPORTANT: You should ONLY interact with the environment provided to you or provide the solution inside <solution> tag AND NEVER ASK FOR HUMAN HELP.\n'
    # NOTE: You can actually set slightly different instruction for different agents
    instruction += AGENT_CLS_TO_INST_SUFFIX.get(agent_class, '')
    logger.info('Instruction:', instruction)

    # Here's how you can run the agent (similar to the `main` function) and get the final task state
    state: State = asyncio.run(
        main(
            instruction,
            fake_user_response_fn=AGENT_CLS_TO_FAKE_USER_RESPONSE_FN.get(agent_class),
            sandbox=sandbox,
        )
    )

    if state is None:
        raise ValueError('State should not be None.')

    final_message = ''
    for act in reversed(state.history):
        if isinstance(act, MessageAction):
            final_message = act.content
            break
    logger.info(
        f'Final message: {final_message} | Ground truth: {instance["reference"]}'
    )

    # FIXME: uncomment this
    # test_result = {'result': final_message}

    # FIXME: uncomment this
    # Save the output
    # output = {
    #     'id': instance['id'],
    #     'instance': instance,
    #     'instruction': instance['prompt'],
    #     'metadata': metadata,
    #     # 'history': [
    #     #     (event_to_dict(action), event_to_dict(obs)) for action, obs in state.history
    #     # ],
    #     'error': state.error if state and state.error else None,
    #     'test_result': test_result,
    # }

    """
    # ======= Attempt to evaluate the agent's edits =======
    # TODO: if you need to do something in the sandbox to get the correctness metric, modify this function
    test_result = get_test_result(instance, sandbox, workspace_dir_name)

    # If you are working on some simpler benchmark that only evaluates the final model output (e.g., in a MessageAction)
    # You can simply get the LAST `MessageAction` from the returned `state.history` and parse it for evaluation.

    if state is None:
        raise ValueError('State should not be None.')

    # Save the output
    output = {
        'instance_id': instance.instance_id,
        'swe_instance': instance.to_dict(),  # SWE Bench specific
        'instruction': instruction,
        'git_patch': git_patch,  # SWE Bench specific
        'metadata': metadata,
        'history': [
            (event_to_dict(action), event_to_dict(obs)) for action, obs in state.history
        ],
        'error': state.error if state and state.error else None,
        'test_result': test_result,
    }
    """

    # Close the sandbox
    sandbox.close()
    # TODO:
    # return output

    return {}


if __name__ == '__main__':
    parser = get_parser()

    parser.add_argument(
        '--subset',
        default='math',
        choices=['math', 'gsm8k'],
        type=str,
        help='subset of the dataset to be used',
    )

    args, _ = parser.parse_known_args()

    # NOTE: It is preferable to load datasets from huggingface datasets and perform post-processing
    # so we don't need to manage file uploading to OpenDevin's repo
    mint_dataset = load_dataset(
        'ryanhoangt/xingyaoww-mint-bench', name=args.subset, split='test'
    )
    logger.info(f'Evaluating MINT - {args.subset} subset')

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
        'mint',
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
        mint_dataset = mint_dataset.select(range(1, 1 + eval_n_limit))
        logger.info(f'Limiting evaluation to first {eval_n_limit} instances.')

    # OUTPUT FILE
    output_file = os.path.join(eval_output_dir, 'output.jsonl')
    logger.info(f'Writing evaluation output to {output_file}')
    finished_instance_ids = set()
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            for line in f:
                data = json.loads(line)
                finished_instance_ids.add(data['id'])
        logger.warning(
            f'Output file {output_file} already exists. Loaded {len(finished_instance_ids)} finished instances.'
        )
    output_fp = open(output_file, 'a')

    logger.info(
        f'Evaluation started with Agent {agent_class}, model {model_name}, max iterations {max_iterations}.'
    )

    # =============================================
    # filter out finished instances
    new_mint_tests = []
    for instance in mint_dataset:
        if instance['id'] in finished_instance_ids:
            logger.info(f'Skipping instance {instance.id} as it is already finished.')
            continue
        new_mint_tests.append(instance)

    mint_dataset = new_mint_tests
    logger.info(
        f'Finished instances: {len(finished_instance_ids)}, Remaining instances: {len(mint_dataset)}'
    )
    # =============================================

    pbar = tqdm(total=len(mint_dataset))

    # This function tracks the progress AND write the output to a JSONL file
    def update_progress(future):
        pbar.update(1)
        output = future.result()
        logger.info('Output: ', output)
        # pbar.set_description(f'Instance {output["instance_id"]}')
        # pbar.set_postfix_str(f'Test Result: {output["test_result"]["result"]}')
        # logger.info(
        #     f'Finished evaluation for instance {output["instance_id"]}: {output["test_result"]["result"]}'
        # )
        output_fp.write(json.dumps(output) + '\n')
        output_fp.flush()

    # This sets the multi-processing
    num_workers = args.eval_num_workers
    logger.info(f'Using {num_workers} workers for evaluation.')

    # This is SWE-Bench specific - CodeActAgent doesn't require mounted workspace to work
    skip_workspace_mount = agent_class == 'CodeActAgent'
    logger.info(f'Skipping workspace mount: {skip_workspace_mount}')

    try:
        with ProcessPoolExecutor(num_workers) as executor:
            futures = []
            # This is how we perform multi-processing
            for instance in mint_dataset:
                future = executor.submit(
                    process_instance,
                    instance,
                    agent_class,
                    metadata,
                    skip_workspace_mount,
                    eval_output_dir,
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
