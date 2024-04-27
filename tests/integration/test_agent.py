import os
import asyncio
import subprocess


from opendevin.main import main


def test_write_simple_script():
    task = "Write a shell script 'hello.sh' that prints 'hello'."
    asyncio.run(main(task))

    # Verify the script file exists
    script_path = 'workspace/hello.sh'
    assert os.path.exists(script_path), 'The file "hello.sh" does not exist'

    # Run the script and capture the output
    result = subprocess.run(['bash', script_path], capture_output=True, text=True)

    # Verify the output from the script
    assert result.stdout.strip() == 'hello', f'Expected output "hello", but got "{result.stdout.strip()}"'
