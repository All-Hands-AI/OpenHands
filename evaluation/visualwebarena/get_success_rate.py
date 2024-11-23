import argparse
import json

import browsergym.visualwebarena  # noqa F401 register visualwebarena tasks as gym environments
import gymnasium as gym

parser = argparse.ArgumentParser(description='Calculate average reward.')
parser.add_argument('output_path', type=str, help='path to output.jsonl')

args = parser.parse_args()

if __name__ == '__main__':
    env_ids = [
        id
        for id in gym.envs.registry.keys()
        if id.startswith('browsergym/visualwebarena')
    ]
    total_num = len(env_ids)
    print('Total number of tasks: ', total_num)
    total_reward = 0
    total_cost = 0
    actual_num = 0
    with open(args.output_path, 'r') as f:
        for line in f:
            data = json.loads(line)
            actual_num += 1
            total_cost += data['metrics']['accumulated_cost']
            reward = data['test_result']['reward']
            if reward >= 0:
                total_reward += data['test_result']['reward']
            else:
                actual_num -= 1
    avg_reward = total_reward / total_num
    print('Total reward: ', total_reward)
    print('Success Rate: ', avg_reward)

    avg_cost = total_cost / actual_num
    print('Avg Cost: ', avg_cost)
    print('Total Cost: ', total_cost)
    print('Actual number of tasks finished: ', actual_num)
