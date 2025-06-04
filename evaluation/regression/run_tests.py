import argparse

import pytest

from openhands.config import load_openhands_config

config = load_openhands_config()

if __name__ == '__main__':
    """Main entry point of the script.

    This script runs pytest with specific arguments and configuration.

    Usage:
        python script_name.py [--OPENAI_API_KEY=<api_key>] [--model=<model_name>]

    """
    parser = argparse.ArgumentParser(
        description='This script runs pytest with specific arguments and configuration.'
    )
    parser.add_argument(
        '--OPENAI_API_KEY', type=str, required=True, help='Your OpenAI API key'
    )
    parser.add_argument(
        '--model', type=str, required=True, help='The model name to use'
    )

    parser_args = parser.parse_args()
    config.config['OPENAI_API_KEY'] = parser_args.OPENAI_API_KEY
    args = ['-v', 'evaluation/regression/cases', f'-o model={parser_args.model}']

    pytest.main(args)
