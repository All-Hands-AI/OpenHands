#!/usr/bin/env python3
import os
import sys
import yaml
import shutil
import tempfile
import subprocess
from pathlib import Path


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
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Check if git repo and commit-ish are specified
        if case_yaml.exists():
            with open(case_yaml) as f:
                config = yaml.safe_load(f)
                if config and "git" in config:
                    repo = config["git"]
                    commit = config.get("commit-ish", "main")
                    subprocess.run(["git", "clone", repo, temp_dir], check=True)
                    subprocess.run(["git", "checkout", commit], cwd=temp_dir, check=True)

        # Copy prompt and test script
        shutil.copy2(case_dir / "prompt.txt", temp_path / "prompt.txt")
        shutil.copy2(case_dir / "test.sh", temp_path / "test.sh")
        os.chmod(temp_path / "test.sh", 0o755)  # Make test.sh executable

        # Run the agent in headless mode with timeout
        try:
            process = subprocess.run(
                ["python3", "-m", "openhands.core.main", "--headless"],
                input=(case_dir / "prompt.txt").read_text(),
                text=True,
                timeout=timeout,
                cwd=temp_dir
            )
            process.check_returncode()
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            print(f"Agent failed for test case {case_name}: {str(e)}")
            if required:
                return False
            return True

        # Run the test script
        try:
            subprocess.run(["./test.sh"], check=True, cwd=temp_dir)
            print(f"Test case {case_name} passed")
            return True
        except subprocess.CalledProcessError:
            print(f"Test case {case_name} failed")
            if required:
                return False
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