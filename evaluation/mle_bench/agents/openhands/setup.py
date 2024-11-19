import argparse
import os
from pathlib import Path

from templates import additional_notes_template, config_template
from utils import get_gpu_generation

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CODE_DIR = Path(os.getenv('CODE_DIR'))
AGENT_DIR = Path(os.getenv('AGENT_DIR'))

parser = argparse.ArgumentParser()
parser.add_argument('--agent', type=str, required=True)
parser.add_argument('--model', type=str, required=True)
parser.add_argument('--max_time_in_hours', type=float, required=True)
parser.add_argument('--max_steps', type=int, required=True)
parser.add_argument('--shm_size', type=str, required=True)
args, other_args = parser.parse_known_args()

gpu_generation = get_gpu_generation()
type_of_processor = gpu_generation if gpu_generation else 'CPU'

config = config_template.substitute(
    workspace_base='/home',
    workspace_mount_path_in_sandbox='/home',
    max_steps=args.max_steps,
    model=args.model,
    api_key=OPENAI_API_KEY,
    agent=args.agent,
    shm_size=args.shm_size,
)

additional_notes = additional_notes_template.substitute(
    type_of_processor=type_of_processor,
    max_time_in_hours=args.max_time_in_hours,
    max_steps=args.max_steps,
    workspace=CODE_DIR,
)

with open(AGENT_DIR / 'config.toml', 'w') as file:
    file.write(config.strip())

with open('/home/instructions.txt', 'r') as file:
    partial_instructions = file.read()

instructions = partial_instructions + additional_notes

with open('/home/full_instructions.txt', 'w') as file:
    file.write(instructions.strip())
