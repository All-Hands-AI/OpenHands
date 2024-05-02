import random
import string
from dataclasses import dataclass
from typing import TYPE_CHECKING

import requests

from opendevin.core import config
from opendevin.core.schema import ActionType
from opendevin.core.schema.config import ConfigType
from opendevin.events.observation import (
    AgentErrorObservation,
    AgentMessageObservation,
    CmdOutputObservation,
    Observation,
)

from .action import Action

if TYPE_CHECKING:
    from opendevin.controller import AgentController


@dataclass
class GitHubPushAction(Action):
    """This pushes the current branch to github.

    To use this, you need to set the GITHUB_TOKEN environment variable.
    The agent will return a message with a URL that you can click to make a pull
    request.

    Attributes:
        owner: The owner of the source repo
        repo: The name of the source repo
        branch: The branch to push
        action: The action identifier
    """

    owner: str
    repo: str
    branch: str
    action: str = ActionType.PUSH

    async def run(self, controller: 'AgentController') -> Observation:
        github_token = config.get(ConfigType.GITHUB_TOKEN)
        if not github_token:
            return AgentErrorObservation('GITHUB_TOKEN is not set')

        # Create a random short string to use as a temporary remote
        random_remote = ''.join(
            ['opendevin_temp_'] + random.choices(string.ascii_lowercase, k=5)
        )

        # Set the temporary remote
        new_url = f'https://{github_token}@github.com/{self.owner}/{self.repo}.git'
        command = f'git remote add {random_remote} {new_url}'
        remote_add_result = controller.action_manager.run_command(
            command, background=False
        )
        if (
            not isinstance(remote_add_result, CmdOutputObservation)
            or remote_add_result.exit_code != 0
        ):
            return remote_add_result

        # Push the branch to the temporary remote
        command = f'git push {random_remote} {self.branch}'
        push_result = controller.action_manager.run_command(command, background=False)

        # Delete the temporary remote
        command = f'git remote remove {random_remote}'
        remote_remove_result = controller.action_manager.run_command(
            command, background=False
        )
        if (
            not isinstance(remote_remove_result, CmdOutputObservation)
            or remote_remove_result.exit_code != 0
        ):
            return remote_remove_result

        return push_result

    @property
    def message(self) -> str:
        return f'Pushing branch {self.branch} to {self.owner}/{self.repo}'


@dataclass
class GitHubSendPRAction(Action):
    """An action to send a github PR.

    To use this, you need to set the GITHUB_TOKEN environment variable.

    Attributes:
        owner: The owner of the source repo
        repo: The name of the source repo
        title: The title of the PR
        head: The branch to send the PR from
        head_repo: The repo to send the PR from
        base: The branch to send the PR to
        body: The body of the PR
    """

    owner: str
    repo: str
    title: str
    head: str
    head_repo: str | None
    base: str
    body: str | None
    action: str = ActionType.SEND_PR

    async def run(self, controller: 'AgentController') -> Observation:
        github_token = config.get(ConfigType.GITHUB_TOKEN)
        if not github_token:
            return AgentErrorObservation('GITHUB_TOKEN is not set')

        # API URL to create the pull request
        url = f'https://api.github.com/repos/{self.owner}/{self.repo}/pulls'

        # Headers to authenticate and request JSON responses
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json',
        }

        # Data for the pull request
        data = {
            'title': self.title,
            'head': self.head,
            'head_repo': self.head_repo,
            'base': self.base,
            'body': self.body,
        }
        data = {k: v for k, v in data.items() if v is not None}

        # Make the request
        response = requests.post(url, headers=headers, json=data)

        # Check for errors
        if response.status_code == 201:
            return AgentMessageObservation(
                'Pull request created successfully!\n'
                f'Pull request URL:{response.json()["html_url"]}'
            )
        else:
            return AgentErrorObservation(
                'Failed to create pull request\n'
                f'Status code: {response.status_code}\n'
                f'Response: {response.text}'
            )

    @property
    def message(self) -> str:
        return (
            f'Sending PR from {self.head_repo}:{self.head} to '
            f'{self.owner}:{self.base}'
        )
