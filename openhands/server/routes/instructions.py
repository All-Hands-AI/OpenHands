import base64
import os
import uuid
from datetime import datetime
from typing import Dict, List

import requests

# In-memory storage for temporary microagents
TEMPORARY_MICROAGENTS: Dict[str, Dict] = {}


def get_repo_instructions(repo_name: str) -> Dict:
    """Get repository instructions from .openhands_instructions file."""
    token = os.environ.get('GITHUB_TOKEN')
    headers = {'Authorization': f'Bearer {token}'}
    url = f'https://api.github.com/repos/{repo_name}/contents/.openhands_instructions'

    response = requests.get(url, headers=headers)
    if response.status_code == 404:
        return {'instructions': '', 'tutorialUrl': '', 'hasInstructions': False}

    data = response.json()
    content = base64.b64decode(data['content']).decode('utf-8')
    return {
        'instructions': content,
        'tutorialUrl': data['html_url'],
        'hasInstructions': True,
    }


def create_instructions_pr(repo_name: str, instructions: str) -> Dict:
    """Create a PR to add/update .openhands_instructions file."""
    token = os.environ.get('GITHUB_TOKEN')
    headers = {'Authorization': f'Bearer {token}'}

    # Create a new branch
    branch_name = f'add-instructions-{uuid.uuid4().hex[:8]}'
    owner, repo = repo_name.split('/')

    # Get the latest commit SHA from main branch
    url = f'https://api.github.com/repos/{repo_name}/git/refs/heads/main'
    response = requests.get(url, headers=headers)
    sha = response.json()['object']['sha']

    # Create a new branch
    url = f'https://api.github.com/repos/{repo_name}/git/refs'
    data = {'ref': f'refs/heads/{branch_name}', 'sha': sha}
    response = requests.post(url, headers=headers, json=data)

    # Create/update the file
    url = f'https://api.github.com/repos/{repo_name}/contents/.openhands_instructions'
    data = {
        'message': 'Add/update repository instructions',
        'content': base64.b64encode(instructions.encode()).decode(),
        'branch': branch_name,
    }
    response = requests.put(url, headers=headers, json=data)

    # Create a PR
    url = f'https://api.github.com/repos/{repo_name}/pulls'
    data = {
        'title': 'Add/update repository instructions',
        'head': branch_name,
        'base': 'main',
        'body': 'This PR adds or updates the repository instructions in .openhands_instructions file.',
    }
    response = requests.post(url, headers=headers, json=data)
    pr_data = response.json()

    return {
        'success': response.status_code == 201,
        'pullRequestUrl': pr_data.get('html_url', ''),
        'message': 'Pull request created successfully',
    }


def get_repo_microagents(repo_name: str) -> List[Dict]:
    """Get repository microagents from .openhands/microagents directory."""
    token = os.environ.get('GITHUB_TOKEN')
    headers = {'Authorization': f'Bearer {token}'}

    # Get the tree for .openhands/microagents directory
    url = f'https://api.github.com/repos/{repo_name}/git/trees/main?recursive=1'
    response = requests.get(url, headers=headers)
    if response.status_code == 404:
        return []

    tree = response.json()['tree']
    agents = []
    for item in tree:
        if item['path'].startswith('.openhands/microagents/') and item['path'].endswith(
            '.md'
        ):
            name = item['path'].split('/')[-1].replace('.md', '')
            agents.append(
                {
                    'id': str(uuid.uuid4()),
                    'name': name,
                    'instructions': '',  # TODO: Load instructions from file
                    'isPermanent': True,
                    'createdAt': datetime.utcnow().isoformat(),
                }
            )

    # Add temporary agents
    for agent_id, agent in TEMPORARY_MICROAGENTS.items():
        if agent['repo_name'] == repo_name:
            agents.append(
                {
                    'id': agent_id,
                    'name': agent['name'],
                    'instructions': agent['instructions'],
                    'isPermanent': False,
                    'createdAt': agent['createdAt'],
                }
            )

    return agents


def add_temporary_microagent(repo_name: str, instructions: str) -> Dict:
    """Add a temporary microagent that will be stored in memory."""
    agent_id = str(uuid.uuid4())
    TEMPORARY_MICROAGENTS[agent_id] = {
        'repo_name': repo_name,
        'name': f'temp-agent-{agent_id[:8]}',
        'instructions': instructions,
        'createdAt': datetime.utcnow().isoformat(),
    }

    return {
        'success': True,
        'agentId': agent_id,
        'message': 'Temporary microagent added successfully',
    }


def add_permanent_microagent(repo_name: str, instructions: str) -> Dict:
    """Create a PR to add a permanent microagent in .openhands/microagents directory."""
    token = os.environ.get('GITHUB_TOKEN')
    headers = {'Authorization': f'Bearer {token}'}

    # Create a new branch
    branch_name = f'add-microagent-{uuid.uuid4().hex[:8]}'
    owner, repo = repo_name.split('/')

    # Get the latest commit SHA from main branch
    url = f'https://api.github.com/repos/{repo_name}/git/refs/heads/main'
    response = requests.get(url, headers=headers)
    sha = response.json()['object']['sha']

    # Create a new branch
    url = f'https://api.github.com/repos/{repo_name}/git/refs'
    data = {'ref': f'refs/heads/{branch_name}', 'sha': sha}
    response = requests.post(url, headers=headers, json=data)

    # Create the microagent file
    agent_id = str(uuid.uuid4())
    agent_name = f'agent-{agent_id[:8]}'
    url = f'https://api.github.com/repos/{repo_name}/contents/.openhands/microagents/{agent_name}.md'
    data = {
        'message': f'Add microagent {agent_name}',
        'content': base64.b64encode(instructions.encode()).decode(),
        'branch': branch_name,
    }
    response = requests.put(url, headers=headers, json=data)

    # Create a PR
    url = f'https://api.github.com/repos/{repo_name}/pulls'
    data = {
        'title': f'Add microagent {agent_name}',
        'head': branch_name,
        'base': 'main',
        'body': 'This PR adds a new microagent to the repository.',
    }
    response = requests.post(url, headers=headers, json=data)

    return {
        'success': response.status_code == 201,
        'agentId': agent_id,
        'message': 'Pull request created successfully',
    }
