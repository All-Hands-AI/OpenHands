import os
import sys
import pytest

if __name__ == '__main__':
    args = ['-v', 'evaluation/regression/cases']
    for arg in sys.argv[1:]:
        if arg.startswith('--OPENAI_API_KEY='):
            os.environ['OPENAI_API_KEY'] = arg.split('=')[1]
        elif arg.startswith('--model='):
            args.append(f'-o model={arg.split('=')[1]}')
    pytest.main(args)