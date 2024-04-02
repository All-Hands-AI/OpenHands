import sys
import pytest

from opendevin import config

if __name__ == '__main__':
    """Main entry point of the script.

    This script runs pytest with specific arguments and configuration.

    Usage:
        python script_name.py [--OPENAI_API_KEY=<api_key>] [--model=<model_name>]

    """
    args = ['-v', 'evaluation/regression/cases']
    for arg in sys.argv[1:]:
        if arg.startswith('--OPENAI_API_KEY='):
            config.config['OPENAI_API_KEY'] = arg.split('=')[1]
        elif arg.startswith('--model='):
            args.append(f'-o model={arg.split('=')[1]}')
    pytest.main(args)