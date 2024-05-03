import asyncio
import json
import os
import pathlib
import time

from datasets import load_dataset
from tqdm import tqdm

from evaluation.swe_bench.swe_env_box import SWEBenchSSHBox
from opendevin.controller.state.state import State
from opendevin.core.config import args
from opendevin.core.logger import get_file_handler
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.main import main
from opendevin.events.observation import UserMessageObservation


def codeact_user_response(state: State) -> str:
    if state.history:
        user_msg_obs = [
            obs for _, obs in state.history if isinstance(obs, UserMessageObservation)
        ]
        if len(user_msg_obs) >= 3:
            # let the agent know that it can give up when it has tried 3 times
            return 'Please continue working on the task on whatever approach you think is suitable. If you think you have modified the code in a way that fixes the issue OR you want to give up, please run the following command: <execute_bash> exit </execute_bash>.\n'
    return (
        'Please continue working on the task on whatever approach you think is suitable. '
        'If you think you have modified the code in a way that fixes the issue, please run the following command: <execute_bash> exit </execute_bash>.\n'
        'IMPORTANT: YOU SHOULD NEVER ASK FOR HUMAN HELP OR USE THE INTERNET TO SOLVE THIS TASK. '
    )


AGENT_CLS_TO_FAKE_USER_RESPONSE_FN = {'CodeActAgent': codeact_user_response}

AGENT_CLS_TO_INST_SUFFIX = {
    'CodeActAgent': 'When you think you have fixed the issue through code changes, please run the following command: <execute_bash> exit </execute_bash>.\n'
}

if __name__ == '__main__':
    # Load the dataset
    dataset = load_dataset('princeton-nlp/SWE-bench_Lite')
    swe_bench_lite_test = dataset['test'].to_pandas()

    # TEST METADATA
    agent_class = args.agent_cls
    assert (
        agent_class in AGENT_CLS_TO_FAKE_USER_RESPONSE_FN
    ), f'Unsupported agent class: {agent_class}'
    model_name = args.model_name
    max_iterations = args.max_iterations
    eval_output_dir = os.path.join(
        args.eval_output_dir,
        'swe_bench',
        agent_class,
        model_name + '_maxiter_' + str(max_iterations),
    )

    # logger save to eval_output_dir/infer.log
    logger.addHandler(get_file_handler(eval_output_dir))
    pathlib.Path(eval_output_dir).mkdir(parents=True, exist_ok=True)
    logger.info(f'Using evaluation output directory: {eval_output_dir}')

    metadata = {
        'agent_class': agent_class,
        'model_name': model_name,
        'max_iterations': max_iterations,
        'eval_output_dir': eval_output_dir,
        'start_time': time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    with open(os.path.join(eval_output_dir, 'metadata.json'), 'w') as f:
        json.dump(metadata, f)

    # LIMIT EVALUATION
    eval_n_limit = args.eval_n_limit
    if eval_n_limit:
        swe_bench_lite_test = swe_bench_lite_test.head(eval_n_limit)
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

    pbar = tqdm(swe_bench_lite_test.iterrows(), total=len(swe_bench_lite_test))

    for row_idx, instance in swe_bench_lite_test.iterrows():
        if instance.instance_id in finished_instance_ids:
            logger.info(
                f'Skipping instance {instance.instance_id} as it is already finished.'
            )
            pbar.update()
            continue

        workspace_dir_name = f'{instance.repo}__{instance.version}'.replace('/', '__')
        pbar.set_description(f'Instance {instance.instance_id} | {workspace_dir_name}')
        sandbox = SWEBenchSSHBox.get_box_for_instance(instance, workspace_dir_name)

        # Prepare controller kwargs
        controller_kwargs = {
            'fake_user_response_fn': AGENT_CLS_TO_FAKE_USER_RESPONSE_FN.get(
                agent_class
            ),
            'sandbox': sandbox,
        }

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
            'IMPORTANT: YOU SHOULD NEVER ASK FOR HUMAN HELP OR USE THE INTERNET TO SOLVE THIS TASK. \n'
            'You should ONLY interact with the environment provided to you.\n'
        )
        instruction += AGENT_CLS_TO_INST_SUFFIX.get(agent_class, '')

        # Run the agent
        state: State = asyncio.run(
            main(instruction, controller_kwargs=controller_kwargs)
        )

        # Get git patch
        git_patch = sandbox.get_diff_patch()
        logger.info(f'Got git diff for instance {instance.instance_id}')

        # Save the output
        output = {
            'instance_id': instance.instance_id,
            'swe_instance': instance.to_dict(),
            'instruction': instruction,
            'git_patch': git_patch,
            'metadata': metadata,
            'history': [
                (action.to_dict(), obs.to_dict()) for action, obs in state.history
            ],
        }
        output_fp.write(json.dumps(output) + '\n')
        output_fp.flush()

    output_fp.close()
    logger.info('Evaluation finished.')
