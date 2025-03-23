import hashlib
import os
import uuid
from typing import Callable, Tuple, Type

from pydantic import SecretStr

import openhands.agenthub  # noqa F401 (we import this to get the agents registered)
from openhands.controller import AgentController
from openhands.controller.agent import Agent
from openhands.controller.state.state import State
from openhands.core.config import (
    AppConfig,
)
from openhands.core.logger import openhands_logger as logger
from openhands.events import EventStream
from openhands.events.event import Event
from openhands.integrations.provider import ProviderToken, ProviderType, SecretStore
from openhands.llm.llm import LLM
from openhands.memory.memory import Memory
from openhands.microagent.microagent import BaseMicroAgent
from openhands.runtime import get_runtime_cls
from openhands.runtime.base import Runtime
from openhands.security import SecurityAnalyzer, options
from openhands.storage import get_file_store


def create_runtime(
    config: AppConfig,
    sid: str | None = None,
    headless_mode: bool = True,
    agent: Agent | None = None,
) -> Runtime:
    """Create a runtime for the agent to run on.

    Args:
        config: The app config.
        sid: (optional) The session id. IMPORTANT: please don't set this unless you know what you're doing.
            Set it to incompatible value will cause unexpected behavior on RemoteRuntime.
        headless_mode: Whether the agent is run in headless mode. `create_runtime` is typically called within evaluation scripts,
            where we don't want to have the VSCode UI open, so it defaults to True.
        agent: (optional) The agent instance to use for configuring the runtime.

    Returns:
        The created Runtime instance (not yet connected or initialized).
    """
    # if sid is provided on the command line, use it as the name of the event stream
    # otherwise generate it on the basis of the configured jwt_secret
    # we can do this better, this is just so that the sid is retrieved when we want to restore the session
    session_id = sid or generate_sid(config)

    # set up the event stream
    file_store = get_file_store(config.file_store, config.file_store_path)
    event_stream = EventStream(session_id, file_store)

    # set up the security analyzer
    if config.security.security_analyzer:
        options.SecurityAnalyzers.get(
            config.security.security_analyzer, SecurityAnalyzer
        )(event_stream)

    # agent class
    if agent:
        agent_cls = type(agent)
    else:
        agent_cls = Agent.get_cls(config.default_agent)

    # runtime and tools
    runtime_cls = get_runtime_cls(config.runtime)
    logger.debug(f'Initializing runtime: {runtime_cls.__name__}')
    runtime: Runtime = runtime_cls(
        config=config,
        event_stream=event_stream,
        sid=session_id,
        plugins=agent_cls.sandbox_plugins,
        headless_mode=headless_mode,
    )

    logger.debug(
        f'Runtime created with plugins: {[plugin.name for plugin in runtime.plugins]}'
    )

    return runtime


def initialize_repository_for_runtime(
    runtime: Runtime,
    selected_repository: str | None = None,
    github_token: SecretStr | None = None,
) -> str | None:
    """Initialize the repository for the runtime.

    Args:
        runtime: The runtime to initialize the repository for.
        selected_repository: (optional) The GitHub repository to use.
        github_token: (optional) The GitHub token to use.

    Returns:
        The repository directory path if a repository was cloned, None otherwise.
    """
    # clone selected repository if provided
    github_token = (
        SecretStr(os.environ.get('GITHUB_TOKEN')) if not github_token else github_token
    )

    secret_store = (
        SecretStore(
            provider_tokens={
                ProviderType.GITHUB: ProviderToken(token=SecretStr(github_token))
            }
        )
        if github_token
        else None
    )
    provider_tokens = secret_store.provider_tokens if secret_store else None

    repo_directory = None
    if selected_repository and provider_tokens:
        logger.debug(f'Selected repository {selected_repository}.')
        repo_directory = runtime.clone_repo(
            provider_tokens,
            selected_repository,
            None,
        )

    return repo_directory


def create_memory(
    runtime: Runtime,
    event_stream: EventStream,
    sid: str,
    selected_repository: str | None = None,
    repo_directory: str | None = None,
    status_callback: Callable | None = None,
) -> Memory:
    """Create a memory for the agent to use.

    Args:
        runtime: The runtime to use.
        event_stream: The event stream it will subscribe to.
        sid: The session id.
        selected_repository: The repository to clone and start with, if any.
        repo_directory: The repository directory, if any.
        status_callback: Optional callback function to handle status updates.
    """
    memory = Memory(
        event_stream=event_stream,
        sid=sid,
        status_callback=status_callback,
    )

    if runtime:
        # sets available hosts
        memory.set_runtime_info(runtime)

        # loads microagents from repo/.openhands/microagents
        microagents: list[BaseMicroAgent] = runtime.get_microagents_from_selected_repo(
            selected_repository
        )
        memory.load_user_workspace_microagents(microagents)

        if selected_repository and repo_directory:
            memory.set_repository_info(selected_repository, repo_directory)

    return memory


def create_agent(config: AppConfig) -> Agent:
    agent_cls: Type[Agent] = Agent.get_cls(config.default_agent)
    agent_config = config.get_agent_config(config.default_agent)
    llm_config = config.get_llm_config_from_agent(config.default_agent)
    agent = agent_cls(
        llm=LLM(config=llm_config),
        config=agent_config,
    )

    return agent


def create_controller(
    agent: Agent,
    runtime: Runtime,
    config: AppConfig,
    headless_mode: bool = True,
    replay_events: list[Event] | None = None,
) -> Tuple[AgentController, State | None]:
    event_stream = runtime.event_stream
    initial_state = None
    try:
        logger.debug(
            f'Trying to restore agent state from session {event_stream.sid} if available'
        )
        initial_state = State.restore_from_session(
            event_stream.sid, event_stream.file_store
        )
    except Exception as e:
        logger.debug(f'Cannot restore agent state: {e}')

    controller = AgentController(
        agent=agent,
        max_iterations=config.max_iterations,
        max_budget_per_task=config.max_budget_per_task,
        agent_to_llm_config=config.get_agent_to_llm_config_map(),
        event_stream=event_stream,
        initial_state=initial_state,
        headless_mode=headless_mode,
        confirmation_mode=config.security.confirmation_mode,
        replay_events=replay_events,
    )
    return (controller, initial_state)


def generate_sid(config: AppConfig, session_name: str | None = None) -> str:
    """Generate a session id based on the session name and the jwt secret."""
    session_name = session_name or str(uuid.uuid4())
    jwt_secret = config.jwt_secret

    hash_str = hashlib.sha256(f'{session_name}{jwt_secret}'.encode('utf-8')).hexdigest()
    return f'{session_name}-{hash_str[:16]}'
