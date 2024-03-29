import os
import pytest
import subprocess
import logging
import shutil
import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CASES_DIR = os.path.join(SCRIPT_DIR, 'cases')
AGENTHUB_DIR = os.path.join(SCRIPT_DIR, '../../', 'agenthub')

def agents():
    agents = []
    for agent in os.listdir(AGENTHUB_DIR):
        if os.path.isdir(os.path.join(AGENTHUB_DIR, agent)) and agent.endswith('_agent'):
            agents.append(agent)
    return agents

@pytest.fixture(scope="session")
def test_cases_dir():
    return CASES_DIR

@pytest.fixture
def task_file(test_cases_dir, request):
    test_case_dir = os.path.dirname(request.module.__file__)
    task_file_path = os.path.join(test_case_dir, 'task.txt')
    return task_file_path

@pytest.fixture
def workspace_dir(test_cases_dir, request):
    test_case_dir = os.path.dirname(request.module.__file__)
    workspace_dir = os.path.join(test_case_dir, 'workspace')
    return workspace_dir

@pytest.fixture
def model(request):
    return request.config.getoption("model", default="gpt-4-0125-preview")

@pytest.fixture
def run_test_case(test_cases_dir, workspace_dir, request):
    def _run_test_case(agent, case):
        case_dir = os.path.join(test_cases_dir, case)
        task = open(os.path.join(case_dir, 'task.txt'), 'r').read().strip()
        outputs_dir = os.path.join(case_dir, 'outputs')
        agent_dir = os.path.join(outputs_dir, agent)

        if not os.path.exists(agent_dir):
            os.makedirs(agent_dir)

        shutil.rmtree(os.path.join(agent_dir, 'workspace'), ignore_errors=True)
        if os.path.isdir(os.path.join(case_dir, 'start')):
            os.copytree(os.path.join(case_dir, 'start'), os.path.join(agent_dir, 'workspace'))
        else:
            os.makedirs(os.path.join(agent_dir, 'workspace'))
        agents_ref = {
            "langchains_agent":"LangchainsAgent",
            "codeact_agent":"CodeActAgent"
        }
        process = subprocess.Popen(["python3", f"{SCRIPT_DIR}/../../opendevin/main.py", "-d", f"{os.path.join(agent_dir, 'workspace')}", "-c", f"{agents_ref[agent]}", "-t", f"{task}", "-m", "gpt-4-0125-preview"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        stdout, stderr = process.communicate()
        logging.info(f"Stdout: {stdout}")
        logging.error(f"Stderr: {stderr}")

        assert process.returncode == 0
        return os.path.join(agent_dir, 'workspace')

    return _run_test_case

def pytest_configure(config):
    now = datetime.datetime.now()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(f"test_results_{now.strftime('%Y%m%d_%H%M%S')}.log"),
            logging.StreamHandler()
        ]
    )