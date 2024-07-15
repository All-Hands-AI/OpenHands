import argparse
import json
import multiprocessing
import os
import random
import time
from datetime import datetime

from my_frontend import OpenDevinSession

questions = [
    'Using google, what is the difference between the ages of the current partners of Pete Buttigieg and Taylor Swift?',
    'Using google, what is the sum of Lebron James’s career high basketball game point, Brazil’s Soccer World Cup wins, and Ma Long’s official ping-pong rating according to the ITTF?',
    'Using google, what’s the difference in flight time in minutes between LA to San Francisco and LA to San Jose?',
    'Using Google, what is the total number of Grammy awards won by Adele, the number of Oscars won by Leonardo DiCaprio, and the number of Nobel Prizes won by Marie Curie?',
    'Using Google, what is the average salary of a software engineer in Silicon Valley, a lawyer in New York City, and a doctor in Los Angeles?',
    'I have a budget of $3000 per month. Can you give me 3 good options for apartment rental in Hudson yards, nyc using google?',
    'Find me a laptop under $1,000 that has at least 16GB RAM and a dedicated GPU.',
    'I live at 4463 Oak Grove Dr, La Cañada Flintridge, CA 91011, can you find some Mediterranean restaurant within a 10 mile radius that has a rating above 4.0 stars with more than 500 user ratings?',
    'I want to invest $10,000 in stocks. Can you recommend three stable companies to invest in based on current market trends?',
    'I have $500 to spend on a weekend getaway. Can you suggest three destinations near San Francisco with accommodation and activities within this budget?',
    'Can you go on amazon and help me put a gaming computer of any kind into my shopping cart?',
    'Help me find a table at fogo de chão in San Jose for 2 people using google.',
    'Using google, can you purchase a One-way flight from Los Angeles to Tokyo this Sunday?',
    'Help me reserve a hotel room in New York City for three nights starting next Friday using Google.',
    'Using Google, can you purchase tickets to the next NBA game in Los Angeles?',
]


def run_question(args, qid, start_datetime):
    random.seed(qid)
    question = questions[qid]
    session = OpenDevinSession(
        agent=args.agent, port=args.port, model=args.model, api_key=args.api_key
    )

    for agent_state in session.initialize(as_generator=True):
        print(qid, agent_state)

    action_messages = []
    max_steps = 20
    for message in session.run(question):
        if len(session.action_messages) > len(action_messages):
            diff = len(session.action_messages) - len(action_messages)
            new_action_messages = session.action_messages[-diff:]
            new_action_message = ';'.join(new_action_messages)
            action_messages += new_action_messages
            print(qid, new_action_message)
        if len(action_messages) >= max_steps:
            break

    os.makedirs('my_evaluator_logs', exist_ok=True)

    output_path = f'my_evaluator_logs/{start_datetime}_{args.job_name}_{qid}_steps.json'
    print('Saving log to', output_path)
    json.dump(session.raw_messages, open(output_path, 'w'))

    # session._close()

    time2sleep = 15 + random.random() * 15
    print(f'Sleeping for {time2sleep:.2f} seconds')
    time.sleep(time2sleep)


def main():
    # Create the parser
    parser = argparse.ArgumentParser(
        description="Run evaluations at scale as if you're using the frontend"
    )

    # Add arguments
    parser.add_argument('job_name', type=str)
    parser.add_argument('--agent', type=str, default='WorldModelAgent')
    parser.add_argument('--port', type=int, default=5000)
    parser.add_argument(
        '--model', type=str, default='meta-llama/Meta-Llama-3-70B-Instruct'
    )
    parser.add_argument('--api_key', type=str, default='test')

    # Parse the arguments
    args = parser.parse_args()

    start_datetime = datetime.now().strftime('%Y-%m-%d-%H:%M:%S')

    args_list = [(args, qid, start_datetime) for qid in range(len(questions))]
    with multiprocessing.Pool(processes=3) as pool:
        pool.starmap(run_question, args_list)

    # run_question(args, 2, start_datetime)


if __name__ == '__main__':
    main()
