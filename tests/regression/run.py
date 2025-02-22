#!/usr/bin/env python3
import os
import sys
import yaml
import shutil
import asyncio
import tempfile
from pathlib import Path

import openhands.agenthub  # noqa: F401 - import to register agents
from openhands.core.config import AppConfig, setup_config_from_args
from openhands.core.main import run_controller, auto_continue_response
from openhands.events.action import MessageAction


def run_test_case(case_dir: Path) -> bool:
    """Run a single test case.
    
    Args:
        case_dir: Path to the test case directory
        
    Returns:
        bool: True if test passed, False if failed
    """
    case_name = case_dir.name
    print(f"Running test case: {case_name}")

    # Read case configuration
    timeout = 120  # Default timeout 2 minutes
    required = True
    case_yaml = case_dir / "case.yaml"
    
    if case_yaml.exists():
        with open(case_yaml) as f:
            config = yaml.safe_load(f)
            if config:
                timeout = config.get("timeout", timeout)
                required = config.get("required", required)

    # Create temp directory
    if os.getenv('NO_CLEANUP'):
        # Create a directory in /tmp that won't be automatically cleaned up
        temp_dir = tempfile.mkdtemp(prefix=f'openhands_regression_{case_name}_')
        print(f"Test directory (NO_CLEANUP): {temp_dir}")
        temp_path = Path(temp_dir)
    else:
        # Use context manager which will clean up automatically
        temp_dir_ctx = tempfile.TemporaryDirectory()
        temp_dir = temp_dir_ctx.name
        temp_path = Path(temp_dir)
        
    try:

        # Check if git repo and commit-ish are specified
        if case_yaml.exists():
            with open(case_yaml) as f:
                config = yaml.safe_load(f)
                if config and "git" in config:
                    repo = config["git"]
                    commit = config.get("commit-ish", "main")
                    os.system(f"git clone {repo} {temp_dir}")
                    os.system(f"cd {temp_dir} && git checkout {commit}")

        # Copy prompt and test script
        shutil.copy2(case_dir / "prompt.txt", temp_path / "prompt.txt")
        shutil.copy2(case_dir / "test.sh", temp_path / "test.sh")
        os.chmod(temp_path / "test.sh", 0o755)  # Make test.sh executable

        # Read the prompt
        with open(case_dir / "prompt.txt") as f:
            task_str = f.read()

        # Set up OpenHands configuration
        class Args:
            def __init__(self):
                self.no_auto_continue = False
                self.name = case_name
                self.model = "gpt-4"
                self.headless = True
                self.agent_cls = "CodeActAgent"
                self.max_budget_per_task = 100
                self.max_iterations = 100
                self.cli_multiline_input = False
                self.file_store = None
                self.save_trajectory_path = None
                self.replay_trajectory_path = None
                self.config_file = str(Path(__file__).parent.parent.parent / "config.toml")
                self.llm_config = None
                # Set workspace paths for Docker mounting
                self.workspace_base = str(temp_path)
                self.workspace_mount_path = str(temp_path)
                self.workspace_mount_path_in_sandbox = "/workspace"

        config = setup_config_from_args(Args())
        initial_user_action = MessageAction(content=task_str)

        # Change to temp directory for test execution
        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            # Run OpenHands
            asyncio.run(
                run_controller(
                    config=config,
                    initial_user_action=initial_user_action,
                    fake_user_response_fn=auto_continue_response,
                    headless_mode=True,
                )
            )

            # Run the test script
            test_result = os.system("./test.sh")
            if test_result != 0:
                print(f"Test case {case_name} failed")
                if required:
                    return False
            else:
                print(f"Test case {case_name} passed")
                return True

        except Exception as e:
            print(f"Error running test case {case_name}: {e}")
            if required:
                return False
            return True
        finally:
            os.chdir(original_cwd)
            if not os.getenv('NO_CLEANUP'):
                temp_dir_ctx.cleanup()

    return True


def main():
    # Find and run all test cases
    regression_dir = Path(__file__).parent
    cases_dir = regression_dir / "cases"
    
    all_passed = True
    for case_dir in cases_dir.iterdir():
        if case_dir.is_dir():
            if not run_test_case(case_dir):
                all_passed = False

    if all_passed:
        print("All tests completed successfully")
        sys.exit(0)
    else:
        print("Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()