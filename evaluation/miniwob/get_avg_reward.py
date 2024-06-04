import argparse
import json

import browsergym.miniwob  # noqa F401 register miniwob tasks as gym environments
import gymnasium as gym

parser = argparse.ArgumentParser(description='Calculate average reward.')
parser.add_argument('output_path', type=str, help='path to output.jsonl')

args = parser.parse_args()

if __name__ == '__main__':
    env_ids = [
        id for id in gym.envs.registry.keys() if id.startswith('browsergym/miniwob')
    ]
    total_num = len(env_ids)
    print('Total number of tasks: ', total_num)
    total_reward = 0
    with open(args.output_path, 'r') as f:
        for line in f:
            data = json.loads(line)
            total_reward += data['test_result']

    avg_reward = total_reward / total_num
    print('Avg Reward: ', avg_reward)
