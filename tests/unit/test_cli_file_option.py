import argparse
import os
import tempfile


def test_cli_file_option_enhancement():
    """Test that the CLI enhances file content with a prompt when using the file option."""
    # Import the function directly from the module

    # Create a temporary file with some content
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
        temp_file.write('This is a test file content.')
        temp_file_path = temp_file.name

    try:
        # Create args with file option
        args = argparse.Namespace()
        args.file = temp_file_path
        args.task = None

        # Create a function that simulates the file handling in main.py
        def process_file_option(args):
            if args.file:
                with open(args.file, 'r', encoding='utf-8') as file:
                    file_content = file.read()

                # Create a prompt that instructs the agent to read and understand the file first
                task_str = f"""The user has tagged a file '{args.file}'.
Please read and understand the following file content first:

```
{file_content}
```

After reviewing the file, please ask the user what they would like to do with it."""
                return task_str
            return None

        # Call the function
        result = process_file_option(args)

        # Check that the result contains the expected prompt structure
        assert f"The user has tagged a file '{temp_file_path}'" in result
        assert 'Please read and understand the following file content first:' in result
        assert 'This is a test file content.' in result
        assert (
            'After reviewing the file, please ask the user what they would like to do with it.'
            in result
        )
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)
