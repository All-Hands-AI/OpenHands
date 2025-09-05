#!/usr/bin/env python3
"""
WebArena evaluation script for OpenHands outputs using official WebArena evaluation harness.
This script evaluates the results from run_infer.py using the official WebArena evaluation code.

This script requires:
1. Official WebArena repository cloned to /workspace/project/webarena
2. WebArena environment variables properly configured
3. Authentication files set up for WebArena sites
4. Docker containers running for WebArena sites
"""

import argparse
import json
import os
import sys
from typing import Any

# Set up environment variables for WebArena
WEBARENA_BASE_URL = os.environ.get('WEBARENA_BASE_URL', '')
if WEBARENA_BASE_URL:
    os.environ['REDDIT'] = f'{WEBARENA_BASE_URL}:9999'
    os.environ['SHOPPING'] = f'{WEBARENA_BASE_URL}:7770'
    os.environ['SHOPPING_ADMIN'] = f'{WEBARENA_BASE_URL}:7780'
    os.environ['GITLAB'] = f'{WEBARENA_BASE_URL}:8023'
    os.environ['WIKIPEDIA'] = f'{WEBARENA_BASE_URL}:8888'
    os.environ['MAP'] = f'{WEBARENA_BASE_URL}:3000'
    os.environ['HOMEPAGE'] = f'{WEBARENA_BASE_URL}:4399'

# Add the webarena path to sys.path to import its modules
WEBARENA_PATH = '/workspace/project/webarena'
sys.path.insert(0, WEBARENA_PATH)

try:
    from browser_env import ScriptBrowserEnv, create_stop_action
    from browser_env.actions import Action
    from browser_env.utils import StateInfo
    from evaluation_harness import evaluator_router

    print('✅ WebArena evaluation harness imported successfully')
except ImportError as e:
    print(f'❌ Failed to import WebArena evaluation harness: {e}')
    print('Make sure the WebArena repository is cloned to /workspace/project/webarena')
    print('and all dependencies are installed.')
    sys.exit(1)


def load_config_file(config_path: str) -> dict[str, Any]:
    """Load WebArena config file."""
    with open(config_path, 'r') as f:
        return json.load(f)


def convert_openhands_action_to_webarena(action_data: dict[str, Any]) -> Action:
    """Convert OpenHands action format to WebArena action format."""
    action_type = action_data.get('action', '')
    args = action_data.get('args', {})

    if action_type == 'browse':
        url = args.get('url', '')
        if url:
            return Action(action_type='goto', coordinate=[0, 0], text=url)

    elif action_type == 'click':
        coordinate = args.get('coordinate', [0, 0])
        return Action(action_type='click', coordinate=coordinate)

    elif action_type == 'type':
        text = args.get('text', '')
        return Action(action_type='type', text=text, coordinate=[0, 0])

    elif action_type == 'key':
        key = args.get('key', '')
        return Action(action_type='key', text=key, coordinate=[0, 0])

    elif action_type == 'scroll':
        coordinate = args.get('coordinate', [0, 0])
        direction = args.get('direction', 'down')
        return Action(action_type='scroll', coordinate=coordinate, text=direction)

    elif action_type == 'finish':
        return create_stop_action('')

    # Default fallback for unknown actions
    return Action(action_type='none', coordinate=[0, 0])


def convert_openhands_trajectory_to_webarena_format(
    openhands_output: dict[str, Any],
) -> list[Any]:
    """
    Convert OpenHands trajectory format to WebArena trajectory format.

    OpenHands format: history contains pairs of [action, observation]
    WebArena format: trajectory is a list alternating between StateInfo and Action
    """
    trajectory = []

    # Add initial state
    initial_state = StateInfo(
        observation={'text': 'Initial state'}, info={'observation_metadata': {}}
    )
    trajectory.append(initial_state)

    # Process the history
    history = openhands_output.get('history', [])
    for history_pair in history:
        if len(history_pair) >= 2:
            action_data = history_pair[0]
            observation_data = history_pair[1]

            # Convert action
            webarena_action = convert_openhands_action_to_webarena(action_data)
            trajectory.append(webarena_action)

            # Add state info from observation
            state_info = StateInfo(
                observation={'text': observation_data.get('content', '')},
                info={'observation_metadata': observation_data.get('extras', {})},
            )
            trajectory.append(state_info)

    return trajectory


def evaluate_with_official_webarena_harness(
    instance_data: dict[str, Any], config_file_path: str
) -> dict[str, Any]:
    """
    Evaluate a single WebArena instance using the official evaluation harness.

    This function:
    1. Converts OpenHands trajectory to WebArena format
    2. Sets up a browser environment
    3. Replays the trajectory to reach the final state
    4. Runs the official WebArena evaluator
    """

    instance_id = instance_data.get('instance_id', 'unknown')
    print(f'\n🔍 Evaluating instance: {instance_id}')

    try:
        # Load config to understand the task
        config_data = load_config_file(config_file_path)
        intent = config_data.get('intent', '')
        start_url = config_data.get('start_url', '')

        print(f'   Task: {intent}')
        print(f'   Start URL: {start_url}')

        # Convert OpenHands trajectory to WebArena format
        trajectory = convert_openhands_trajectory_to_webarena_format(instance_data)
        print(f'   Converted trajectory with {len(trajectory)} steps')

        # Get the evaluator for this config
        evaluator = evaluator_router(config_file_path)
        print(f'   Using evaluator: {type(evaluator).__name__}')

        # Create browser environment for evaluation
        env = ScriptBrowserEnv(
            headless=True,
            slow_mo=0,
            observation_type='accessibility_tree',
            current_viewport_only=True,
            viewport_size={'width': 1280, 'height': 720},
        )

        try:
            # Initialize the environment with the task
            obs, info = env.reset(options={'config_file': config_file_path})

            # Replay the trajectory to reach the final state
            # This is necessary because the evaluator needs the actual browser state
            current_obs = obs
            for i, step in enumerate(trajectory):
                if isinstance(step, Action):
                    try:
                        current_obs, reward, done, info = env.step(step)
                        if done:
                            break
                    except Exception as e:
                        print(f'   Warning: Error replaying step {i}: {e}')
                        continue

            # Run the official evaluation
            score = evaluator(
                trajectory=trajectory,
                config_file=config_file_path,
                page=env.page,
                client=env.page.context.new_cdp_session(env.page),
            )

            result = {
                'instance_id': instance_id,
                'score': score,
                'success': score == 1.0,
                'trajectory_length': len(trajectory),
                'evaluator': type(evaluator).__name__,
                'evaluation_type': 'official_webarena_harness',
                'intent': intent,
            }

            print(
                f'   Result: {"✅ PASS" if score == 1.0 else "❌ FAIL"} (score: {score})'
            )
            return result

        finally:
            env.close()

    except Exception as e:
        print(f'   ❌ Error evaluating {instance_id}: {e}')
        return {
            'instance_id': instance_id,
            'score': 0.0,
            'success': False,
            'error': str(e),
            'evaluator': 'error',
            'evaluation_type': 'error',
        }


def main():
    parser = argparse.ArgumentParser(
        description='Evaluate WebArena results using ONLY the official WebArena evaluation harness'
    )
    parser.add_argument(
        'output_file', type=str, help='Path to OpenHands output.jsonl file'
    )
    parser.add_argument(
        '--results_file',
        type=str,
        default='webarena_official_eval_results.json',
        help='Path to save evaluation results',
    )
    parser.add_argument(
        '--config_dir',
        type=str,
        default='/workspace/project/webarena/config_files/examples',
        help='Directory containing WebArena config files',
    )

    args = parser.parse_args()

    print('🚀 Starting WebArena Evaluation with Official WebArena Harness ONLY')
    print(f'📁 Output file: {args.output_file}')
    print(f'📁 Config directory: {args.config_dir}')

    # Verify WebArena environment is properly set up
    if not WEBARENA_BASE_URL:
        print('❌ WEBARENA_BASE_URL environment variable not set')
        print('Please set WEBARENA_BASE_URL to your WebArena server URL')
        sys.exit(1)

    print(f'🌐 WebArena base URL: {WEBARENA_BASE_URL}')

    # Load OpenHands results
    results = []
    with open(args.output_file, 'r') as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))

    print(f'📊 Found {len(results)} instances to evaluate')

    # Evaluate each instance using ONLY official WebArena evaluation harness
    evaluation_results = []
    total_score = 0.0

    for result in results:
        instance_id = result.get('instance_id', 'unknown')

        # Find corresponding config file
        config_file = None
        # Accept either plain numeric id ("8") or legacy prefixed id ("webarena.8")
        task_num = instance_id.split('.')[-1]
        config_file = f'{args.config_dir}/{task_num}.json'

        if config_file and os.path.exists(config_file):
            eval_result = evaluate_with_official_webarena_harness(result, config_file)
            evaluation_results.append(eval_result)
            total_score += eval_result.get('score', 0.0)
        else:
            print(f'\n🔍 Evaluating instance: {instance_id}')
            print(f'   ⚠️  Config file not found: {config_file}')
            evaluation_results.append(
                {
                    'instance_id': instance_id,
                    'score': 0.0,
                    'success': False,
                    'error': f'Config file not found: {config_file}',
                    'evaluation_type': 'config_error',
                }
            )

    # Calculate final metrics
    total_instances = len(evaluation_results)
    success_count = sum(1 for r in evaluation_results if r.get('success', False))
    success_rate = success_count / total_instances if total_instances > 0 else 0.0
    average_score = total_score / total_instances if total_instances > 0 else 0.0

    # Save results
    final_results = {
        'evaluation_method': 'official_webarena_harness_only',
        'webarena_base_url': WEBARENA_BASE_URL,
        'total_instances': total_instances,
        'success_count': success_count,
        'success_rate': success_rate,
        'average_score': average_score,
        'individual_results': evaluation_results,
    }

    with open(args.results_file, 'w') as f:
        json.dump(final_results, f, indent=2)

    # Print summary
    print('\n' + '=' * 70)
    print('🎯 WEBARENA EVALUATION RESULTS (Official Harness ONLY)')
    print('=' * 70)
    print(f'📊 Total instances: {total_instances}')
    print(f'✅ Successful: {success_count}')
    print(f'❌ Failed: {total_instances - success_count}')
    print(f'📈 Success rate: {success_rate:.2%}')
    print(f'📊 Average score: {average_score:.4f}')
    print(f'💾 Results saved to: {args.results_file}')
    print('=' * 70)

    # Print individual results
    print('\n📋 Individual Results:')
    for result in evaluation_results:
        status = '✅ PASS' if result.get('success', False) else '❌ FAIL'
        score = result.get('score', 0.0)
        instance_id = result.get('instance_id', 'unknown')
        evaluator = result.get('evaluator', 'unknown')
        error = result.get('error', '')
        if error:
            print(f'   {instance_id}: {status} (score: {score:.2f}) - Error: {error}')
        else:
            print(
                f'   {instance_id}: {status} (score: {score:.2f}) - Evaluator: {evaluator}'
            )

    # Print requirements if there were errors
    error_count = sum(1 for r in evaluation_results if r.get('error'))
    if error_count > 0:
        print('\n' + '⚠️' * 20)
        print('EVALUATION ERRORS DETECTED')
        print('⚠️' * 20)
        print('This evaluation requires:')
        print('1. WebArena Docker containers running and accessible')
        print('2. Authentication files (.auth/) properly set up')
        print('3. All WebArena dependencies installed')
        print('4. Proper network access to WebArena sites')
        print('\nPlease resolve these issues for accurate evaluation.')
        print('⚠️' * 20)


if __name__ == '__main__':
    main()
