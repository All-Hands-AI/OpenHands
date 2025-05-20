import asyncio
import os
import shutil
import time
from unittest.mock import MagicMock, patch

import pytest

from openhands.controller.agent import Agent
from openhands.core.config import AppConfig
from openhands.core.main import run_controller
from openhands.core.schema.agent import AgentState
from openhands.events.action.agent import RecallAction
from openhands.events.action.message import MessageAction, SystemMessageAction
from openhands.events.event import EventSource
from openhands.events.observation.agent import (
    RecallObservation,
    RecallType,
)
from openhands.events.serialization.observation import observation_from_dict
from openhands.events.stream import EventStream
from openhands.llm import LLM
from openhands.llm.metrics import Metrics
from openhands.memory.memory import Memory
from openhands.runtime.impl.action_execution.action_execution_client import (
    ActionExecutionClient,
)
from openhands.storage.memory import InMemoryFileStore
from openhands.utils.prompt import (
    ConversationInstructions,
    PromptManager,
    RepositoryInfo,
    RuntimeInfo,
)


@pytest.fixture
def file_store():
    """Create a temporary file store for testing."""
    return InMemoryFileStore({})


@pytest.fixture
def event_stream(file_store):
    """Create a test event stream."""
    return EventStream(sid='test_sid', file_store=file_store)


@pytest.fixture
def memory(event_stream):
    """Create a test memory instance."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    memory = Memory(event_stream, 'test_sid')
    yield memory
    loop.close()


@pytest.fixture
def prompt_dir(tmp_path):
    # Copy contents from "openhands/agenthub/codeact_agent" to the temp directory
    shutil.copytree(
        'openhands/agenthub/codeact_agent/prompts', tmp_path, dirs_exist_ok=True
    )

    # Return the temporary directory path
    return tmp_path


@pytest.fixture
def mock_agent():
    # Create a dummy agent for the controller
    agent = MagicMock(spec=Agent)
    agent.llm = MagicMock(spec=LLM)
    agent.llm.metrics = Metrics()
    agent.llm.config = AppConfig().get_llm_config()

    # Add a proper system message mock
    system_message = SystemMessageAction(content='Test system message')
    system_message._source = EventSource.AGENT
    system_message._id = -1  # Set invalid ID to avoid the ID check
    agent.get_system_message.return_value = system_message


@pytest.mark.asyncio
async def test_memory_on_event_exception_handling(memory, event_stream, mock_agent):
    """Test that exceptions in Memory.on_event are properly handled via status callback."""
    # Create a mock runtime
    runtime = MagicMock(spec=ActionExecutionClient)
    runtime.event_stream = event_stream

    # Mock Memory method to raise an exception
    with patch.object(
        memory, '_on_workspace_context_recall', side_effect=Exception('Test error')
    ):
        state = await run_controller(
            config=AppConfig(),
            initial_user_action=MessageAction(content='Test message'),
            runtime=runtime,
            sid='test',
            agent=mock_agent,
            fake_user_response_fn=lambda _: 'repeat',
            memory=memory,
        )

        # Verify that the controller's last error was set
        assert state.iteration == 0
        assert state.agent_state == AgentState.ERROR
        assert state.last_error == 'Error: Exception'


@pytest.mark.asyncio
async def test_memory_on_workspace_context_recall_exception_handling(
    memory, event_stream, mock_agent
):
    """Test that exceptions in Memory._on_workspace_context_recall are properly handled via status callback."""
    # Create a mock runtime
    runtime = MagicMock(spec=ActionExecutionClient)
    runtime.event_stream = event_stream

    # Mock Memory._on_workspace_context_recall to raise an exception
    with patch.object(
        memory,
        '_find_microagent_knowledge',
        side_effect=Exception('Test error from _find_microagent_knowledge'),
    ):
        state = await run_controller(
            config=AppConfig(),
            initial_user_action=MessageAction(content='Test message'),
            runtime=runtime,
            sid='test',
            agent=mock_agent,
            fake_user_response_fn=lambda _: 'repeat',
            memory=memory,
        )

        # Verify that the controller's last error was set
        assert state.iteration == 0
        assert state.agent_state == AgentState.ERROR
        assert state.last_error == 'Error: Exception'


@pytest.mark.asyncio
async def test_memory_with_microagents():
    """Test that Memory loads microagents from the global directory and processes microagent actions.

    This test verifies that:
    1. Memory loads microagents from the global GLOBAL_MICROAGENTS_DIR
    2. When a microagent action with a trigger word is processed, a RecallObservation is created
    """
    # Create a mock event stream
    event_stream = MagicMock(spec=EventStream)

    # Initialize Memory to use the global microagents dir
    memory = Memory(
        event_stream=event_stream,
        sid='test-session',
    )

    # Verify microagents were loaded - at least one microagent should be loaded
    # from the global directory that's in the repo
    assert len(memory.knowledge_microagents) > 0

    # Check for the derived name 'flarglebargle'
    derived_name = 'flarglebargle'
    assert derived_name in memory.knowledge_microagents

    # Create a microagent action with the trigger word
    microagent_action = RecallAction(
        query='Hello, flarglebargle!', recall_type=RecallType.KNOWLEDGE
    )

    # Set the source to USER
    microagent_action._source = EventSource.USER  # type: ignore[attr-defined]

    # Mock the event_stream.add_event method
    added_events = []

    def original_add_event(event, source):
        added_events.append((event, source))

    event_stream.add_event = original_add_event

    # Add the microagent action to the event stream
    event_stream.add_event(microagent_action, EventSource.USER)

    # Clear the events list to only capture new events
    added_events.clear()

    # Process the microagent action
    await memory._on_event(microagent_action)

    # Verify a RecallObservation was added to the event stream
    assert len(added_events) == 1
    observation, source = added_events[0]
    assert isinstance(observation, RecallObservation)
    assert source == EventSource.ENVIRONMENT
    assert observation.recall_type == RecallType.KNOWLEDGE

    # We should have at least one microagent: flarglebargle (triggered by keyword)
    # Note: The default-tools microagent might not be loaded in tests
    assert len(observation.microagent_knowledge) == 1

    # Find the flarglebargle microagent in the list
    flarglebargle_knowledge = None
    for knowledge in observation.microagent_knowledge:
        if knowledge.name == derived_name:
            flarglebargle_knowledge = knowledge
            break

    # Check against the derived name
    assert flarglebargle_knowledge is not None
    assert flarglebargle_knowledge.name == derived_name
    assert flarglebargle_knowledge.trigger == 'flarglebargle'
    assert 'magic word' in flarglebargle_knowledge.content


def test_memory_repository_info(prompt_dir, file_store):
    """Test that Memory adds repository info to RecallObservations."""
    # real event stream
    event_stream = EventStream(sid='test-session', file_store=file_store)

    # Create a test repo microagent first
    repo_microagent_name = 'test_repo_microagent'
    repo_microagent_content = """---
name: test_repo
type: repo
agent: CodeActAgent
---

REPOSITORY INSTRUCTIONS: This is a test repository.
"""

    # Create a temporary repo microagent file
    os.makedirs(os.path.join(prompt_dir, 'micro'), exist_ok=True)
    with open(
        os.path.join(prompt_dir, 'micro', f'{repo_microagent_name}.md'), 'w'
    ) as f:
        f.write(repo_microagent_content)

    # Patch the global microagents directory to use our test directory
    test_microagents_dir = os.path.join(prompt_dir, 'micro')
    with patch('openhands.memory.memory.GLOBAL_MICROAGENTS_DIR', test_microagents_dir):
        # Initialize Memory
        memory = Memory(
            event_stream=event_stream,
            sid='test-session',
        )

        # Set repository info
        memory.set_repository_info('owner/repo', '/workspace/repo')

        # Create and add the first user message
        user_message = MessageAction(content='First user message')
        user_message._source = EventSource.USER  # type: ignore[attr-defined]
        event_stream.add_event(user_message, EventSource.USER)

        # Create and add the microagent action
        microagent_action = RecallAction(
            query='First user message', recall_type=RecallType.WORKSPACE_CONTEXT
        )
        microagent_action._source = EventSource.USER  # type: ignore[attr-defined]
        event_stream.add_event(microagent_action, EventSource.USER)

        # Give it a little time to process
        time.sleep(0.3)

        # Get all events from the stream
        events = list(event_stream.get_events())

        # Find the RecallObservation event
        microagent_obs_events = [
            event for event in events if isinstance(event, RecallObservation)
        ]

        # We should have at least one RecallObservation
        assert len(microagent_obs_events) > 0

        # Get the first RecallObservation
        observation = microagent_obs_events[0]
        assert observation.recall_type == RecallType.WORKSPACE_CONTEXT
        assert observation.repo_name == 'owner/repo'
        assert observation.repo_directory == '/workspace/repo'
        assert 'This is a test repository' in observation.repo_instructions

    # Clean up
    os.remove(os.path.join(prompt_dir, 'micro', f'{repo_microagent_name}.md'))


@pytest.mark.asyncio
async def test_memory_with_agent_microagents():
    """Test that Memory processes microagent based on trigger words from agent messages."""
    # Create a mock event stream
    event_stream = MagicMock(spec=EventStream)

    # Initialize Memory to use the global microagents dir
    memory = Memory(
        event_stream=event_stream,
        sid='test-session',
    )

    # Verify microagents were loaded - at least one microagent should be loaded
    # from the global directory that's in the repo
    assert len(memory.knowledge_microagents) > 0

    # Check for the derived name 'flarglebargle'
    derived_name = 'flarglebargle'
    assert derived_name in memory.knowledge_microagents

    # Create a microagent action with the trigger word
    microagent_action = RecallAction(
        query='Hello, flarglebargle!', recall_type=RecallType.KNOWLEDGE
    )

    # Set the source to AGENT
    microagent_action._source = EventSource.AGENT  # type: ignore[attr-defined]

    # Mock the event_stream.add_event method
    added_events = []

    def original_add_event(event, source):
        added_events.append((event, source))

    event_stream.add_event = original_add_event

    # Add the microagent action to the event stream
    event_stream.add_event(microagent_action, EventSource.AGENT)

    # Clear the events list to only capture new events
    added_events.clear()

    # Process the microagent action
    await memory._on_event(microagent_action)

    # Verify a RecallObservation was added to the event stream
    assert len(added_events) == 1
    observation, source = added_events[0]
    assert isinstance(observation, RecallObservation)
    assert source == EventSource.ENVIRONMENT
    assert observation.recall_type == RecallType.KNOWLEDGE

    # We should have at least one microagent: flarglebargle (triggered by keyword)
    # Note: The default-tools microagent might not be loaded in tests
    assert len(observation.microagent_knowledge) == 1

    # Find the flarglebargle microagent in the list
    flarglebargle_knowledge = None
    for knowledge in observation.microagent_knowledge:
        if knowledge.name == derived_name:
            flarglebargle_knowledge = knowledge
            break

    # Check against the derived name
    assert flarglebargle_knowledge is not None
    assert flarglebargle_knowledge.name == derived_name
    assert flarglebargle_knowledge.trigger == 'flarglebargle'
    assert 'magic word' in flarglebargle_knowledge.content


@pytest.mark.asyncio
async def test_custom_secrets_descriptions():
    """Test that custom_secrets_descriptions are properly stored in memory and included in RecallObservation."""
    # Create a mock event stream
    event_stream = MagicMock(spec=EventStream)

    # Initialize Memory
    memory = Memory(
        event_stream=event_stream,
        sid='test-session',
    )

    # Create a mock runtime with custom secrets descriptions
    mock_runtime = MagicMock()
    mock_runtime.web_hosts = {'test-host.example.com': 8080}
    mock_runtime.additional_agent_instructions = 'Test instructions'

    # Define custom secrets descriptions
    custom_secrets = {
        'API_KEY': 'API key for external service',
        'DATABASE_URL': 'Connection string for the database',
        'SECRET_TOKEN': 'Authentication token for secure operations',
    }

    # Set runtime info with custom secrets
    memory.set_runtime_info(mock_runtime, custom_secrets)

    # Set repository info
    memory.set_repository_info('test-owner/test-repo', '/workspace/test-repo')

    # Create a workspace context recall action
    recall_action = RecallAction(
        query='Initial message', recall_type=RecallType.WORKSPACE_CONTEXT
    )
    recall_action._source = EventSource.USER  # type: ignore[attr-defined]

    # Mock the event_stream.add_event method
    added_events = []

    def mock_add_event(event, source):
        added_events.append((event, source))

    event_stream.add_event = mock_add_event

    # Process the recall action
    await memory._on_event(recall_action)

    # Verify a RecallObservation was added to the event stream
    assert len(added_events) == 1
    observation, source = added_events[0]

    # Verify the observation is a RecallObservation
    assert isinstance(observation, RecallObservation)
    assert source == EventSource.ENVIRONMENT
    assert observation.recall_type == RecallType.WORKSPACE_CONTEXT

    # Verify custom_secrets_descriptions are included in the observation
    assert observation.custom_secrets_descriptions == custom_secrets

    # Verify repository info is included
    assert observation.repo_name == 'test-owner/test-repo'
    assert observation.repo_directory == '/workspace/test-repo'

    # Verify runtime info is included
    assert observation.runtime_hosts == {'test-host.example.com': 8080}
    assert observation.additional_agent_instructions == 'Test instructions'


def test_custom_secrets_descriptions_serialization(prompt_dir):
    """Test that custom_secrets_descriptions are properly serialized in the message for the LLM."""
    # Create a PromptManager with the test prompt directory
    prompt_manager = PromptManager(prompt_dir)

    # Create a RuntimeInfo with custom_secrets_descriptions
    custom_secrets = {
        'API_KEY': 'API key for external service',
        'DATABASE_URL': 'Connection string for the database',
        'SECRET_TOKEN': 'Authentication token for secure operations',
    }
    runtime_info = RuntimeInfo(
        date='2025-05-15',
        available_hosts={'test-host.example.com': 8080},
        additional_agent_instructions='Test instructions',
        custom_secrets_descriptions=custom_secrets,
    )

    # Create a RepositoryInfo
    repository_info = RepositoryInfo(
        repo_name='test-owner/test-repo', repo_directory='/workspace/test-repo'
    )

    conversation_instructions = ConversationInstructions(
        content='additional agent context for the task'
    )

    # Build the workspace context message
    workspace_context = prompt_manager.build_workspace_context(
        repository_info=repository_info,
        runtime_info=runtime_info,
        repo_instructions='Test repository instructions',
        conversation_instructions=conversation_instructions,
    )

    # Verify that the workspace context includes the custom_secrets_descriptions
    assert '<CUSTOM_SECRETS>' in workspace_context
    for secret_name, secret_description in custom_secrets.items():
        assert f'$**{secret_name}**' in workspace_context
        assert secret_description in workspace_context

    assert '<CONVERSATION_INSTRUCTIONS>' in workspace_context
    assert 'additional agent context for the task' in workspace_context


@pytest.mark.asyncio
async def test_conversation_instructions_in_memory(prompt_dir, file_store, monkeypatch):
    """Test that conversation_instructions in init session gets stored into memory and rendered in the Jinja template."""
    import uuid
    from unittest.mock import AsyncMock, MagicMock, patch

    from openhands.core.config import AppConfig
    from openhands.server.data_models.agent_loop_info import AgentLoopInfo
    from openhands.server.routes.manage_conversations import _create_new_conversation
    from openhands.server.session.conversation_init_data import ConversationInitData
    from openhands.storage.data_models.conversation_metadata import ConversationTrigger
    from openhands.storage.data_models.settings import Settings

    # Define the conversation instructions content
    conversation_instructions_content = (
        'Follow these specific instructions for the conversation'
    )

    # Create a test conversation ID
    test_conversation_id = uuid.uuid4().hex

    # Create a real event stream for testing
    event_stream = EventStream(sid=test_conversation_id, file_store=file_store)

    # Create a real Memory instance for testing
    memory = Memory(
        event_stream=event_stream,
        sid=test_conversation_id,
    )

    # Create mock settings
    mock_settings = Settings(
        llm_model='test-model',
        llm_api_key='test-api-key',
    )

    # Create a mock settings store
    mock_settings_store = AsyncMock()
    mock_settings_store.load = AsyncMock(return_value=mock_settings)

    # Create a mock conversation store
    mock_conversation_store = AsyncMock()
    mock_conversation_store.exists = AsyncMock(return_value=False)
    mock_conversation_store.save_metadata = AsyncMock()

    # Create a mock for the conversation manager
    mock_conversation_manager = AsyncMock()

    # Create a mock config
    mock_config = MagicMock(spec=AppConfig)

    # Variables to capture the ConversationInitData
    captured_init_data = None

    # Create a spy for Memory.set_conversation_instructions
    original_set_conversation_instructions = Memory.set_conversation_instructions
    set_conversation_instructions_calls = []

    def spy_set_conversation_instructions(self, instructions):
        set_conversation_instructions_calls.append(instructions)
        return original_set_conversation_instructions(self, instructions)

    # Patch the Memory.set_conversation_instructions method with our spy
    monkeypatch.setattr(
        Memory, 'set_conversation_instructions', spy_set_conversation_instructions
    )

    # Create a mock for maybe_start_agent_loop that captures the ConversationInitData
    async def mock_maybe_start_agent_loop(
        sid, init_data, user_id, initial_user_msg=None, replay_json=None
    ):
        nonlocal captured_init_data
        captured_init_data = init_data

        # Mock the _create_memory method to simulate what happens in AgentSession
        async def mock_create_memory(
            selected_repository,
            repo_directory,
            conversation_instructions,
            custom_secrets_descriptions,
        ):
            # Create a mock runtime with the required attributes
            mock_runtime = MagicMock()
            mock_runtime.web_hosts = {'test-host.example.com': 8080}
            mock_runtime.additional_agent_instructions = None

            # This simulates what happens in AgentSession._create_memory
            memory.set_runtime_info(mock_runtime, custom_secrets_descriptions)
            memory.set_conversation_instructions(conversation_instructions)
            return memory

        # Create a mock agent session
        mock_agent_session = AsyncMock()
        mock_agent_session._create_memory.side_effect = mock_create_memory

        # Call the mocked _create_memory method with the conversation_instructions
        await mock_agent_session._create_memory(
            selected_repository='test-owner/test-repo',
            repo_directory='/workspace/test-repo',
            conversation_instructions=init_data.conversation_instructions,
            custom_secrets_descriptions={},
        )

        # Create a workspace context recall action
        recall_action = RecallAction(
            query='Initial message', recall_type=RecallType.WORKSPACE_CONTEXT
        )
        recall_action._source = EventSource.USER  # type: ignore[attr-defined]

        # Add the recall action to the event stream
        event_stream.add_event(recall_action, EventSource.USER)

        # Process the recall action
        await memory._on_event(recall_action)

        # Return a mock AgentLoopInfo
        return AgentLoopInfo(
            conversation_id=sid,
            url=f'http://localhost/{sid}',
            session_api_key='test-api-key',
            event_store=event_stream,
        )

    # Set the side effect for maybe_start_agent_loop
    mock_conversation_manager.maybe_start_agent_loop.side_effect = (
        mock_maybe_start_agent_loop
    )

    # Mock the necessary dependencies
    with (
        patch(
            'openhands.server.routes.manage_conversations.ConversationStoreImpl'
        ) as mock_store_cls,
        patch(
            'openhands.server.routes.manage_conversations.SettingsStoreImpl'
        ) as mock_settings_cls,
        patch(
            'openhands.server.routes.manage_conversations.conversation_manager',
            mock_conversation_manager,
        ),
        patch('openhands.server.routes.manage_conversations.config', mock_config),
        patch(
            'openhands.server.routes.manage_conversations.uuid.uuid4',
            return_value=MagicMock(hex=test_conversation_id),
        ),
    ):
        # Set up the mocks
        mock_store_cls.get_instance = AsyncMock(return_value=mock_conversation_store)
        mock_settings_cls.get_instance = AsyncMock(return_value=mock_settings_store)

        # Call _create_new_conversation with conversation_instructions
        agent_loop_info = await _create_new_conversation(
            user_id='test-user',
            git_provider_tokens=None,
            custom_secrets=None,
            selected_repository='test-owner/test-repo',
            selected_branch='main',
            initial_user_msg='Hello',
            image_urls=None,
            replay_json=None,
            conversation_trigger=ConversationTrigger.GUI,
            conversation_instructions=conversation_instructions_content,
        )

        # Verify the conversation was created successfully
        assert agent_loop_info is not None
        assert agent_loop_info.conversation_id == test_conversation_id

        # Verify that conversation_instructions was passed to ConversationInitData
        assert captured_init_data is not None
        assert isinstance(captured_init_data, ConversationInitData)
        assert (
            captured_init_data.conversation_instructions
            == conversation_instructions_content
        )

        # Verify that set_conversation_instructions was called with the correct parameter
        assert len(set_conversation_instructions_calls) > 0
        assert conversation_instructions_content in set_conversation_instructions_calls

        # Get all events from the stream
        events = list(event_stream.get_events())

        # Find the RecallObservation event
        recall_obs_events = [
            event for event in events if isinstance(event, RecallObservation)
        ]

        # We should have at least one RecallObservation
        assert len(recall_obs_events) > 0

        # Get the first RecallObservation
        observation = recall_obs_events[0]

        # Verify conversation_instructions is included in the observation
        assert (
            observation.conversation_instructions == conversation_instructions_content
        )

        # Now test that it's rendered in the Jinja template
        # Create a PromptManager with the test prompt directory
        prompt_manager = PromptManager(prompt_dir)

        # Create a RuntimeInfo
        runtime_info = RuntimeInfo(
            date='2025-05-15',
            available_hosts={'test-host.example.com': 8080},
        )

        # Create a RepositoryInfo
        repository_info = RepositoryInfo(
            repo_name='test-owner/test-repo', repo_directory='/workspace/test-repo'
        )

        # Create ConversationInstructions
        conversation_instructions = ConversationInstructions(
            content=conversation_instructions_content
        )

        # Build the workspace context message
        workspace_context = prompt_manager.build_workspace_context(
            repository_info=repository_info,
            runtime_info=runtime_info,
            conversation_instructions=conversation_instructions,
        )

        # Verify conversation_instructions is rendered in the template
        assert '<CONVERSATION_INSTRUCTIONS>' in workspace_context
        assert conversation_instructions_content in workspace_context


def test_serialization_deserialization_with_custom_secrets():
    """Test that RecallObservation can be serialized and deserialized with custom_secrets_descriptions."""
    # This simulates an older version of the RecallObservation
    legacy_observation = {
        'message': 'Added workspace context',
        'observation': 'recall',
        'content': 'Test content',
        'extras': {
            'recall_type': 'workspace_context',
            'repo_name': 'test-owner/test-repo',
            'repo_directory': '/workspace/test-repo',
            'repo_instructions': 'Test repository instructions',
            'runtime_hosts': {'test-host.example.com': 8080},
            'additional_agent_instructions': 'Test instructions',
            'date': '2025-05-15',
            'microagent_knowledge': [],  # Intentionally omitting custom_secrets_descriptions
        },
    }

    legacy_observation = observation_from_dict(legacy_observation)

    # Verify that the observation was created successfully
    assert legacy_observation.recall_type == RecallType.WORKSPACE_CONTEXT
    assert legacy_observation.repo_name == 'test-owner/test-repo'
    assert legacy_observation.repo_directory == '/workspace/test-repo'


def test_memory_multiple_repo_microagents(prompt_dir, file_store):
    """Test that Memory loads and concatenates multiple repo microagents correctly."""
    # Create real event stream
    event_stream = EventStream(sid='test-session', file_store=file_store)

    # Create two test repo microagents
    repo_microagent1_name = 'test_repo_microagent1'
    repo_microagent1_content = """---
REPOSITORY INSTRUCTIONS: This is the first test repository.
"""

    repo_microagent2_name = 'test_repo_microagent2'
    repo_microagent2_content = """---
name: test_repo2
type: repo
agent: CodeActAgent
---

REPOSITORY INSTRUCTIONS: This is the second test repository.
"""

    # Create temporary repo microagent files
    os.makedirs(os.path.join(prompt_dir, 'micro'), exist_ok=True)
    with open(
        os.path.join(prompt_dir, 'micro', f'{repo_microagent1_name}.md'), 'w'
    ) as f:
        f.write(repo_microagent1_content)

    with open(
        os.path.join(prompt_dir, 'micro', f'{repo_microagent2_name}.md'), 'w'
    ) as f:
        f.write(repo_microagent2_content)

    # Patch the global microagents directory to use our test directory
    test_microagents_dir = os.path.join(prompt_dir, 'micro')
    with patch('openhands.memory.memory.GLOBAL_MICROAGENTS_DIR', test_microagents_dir):
        # Initialize Memory
        memory = Memory(
            event_stream=event_stream,
            sid='test-session',
        )

        # Set repository info
        memory.set_repository_info('owner/repo', '/workspace/repo')

        # Create and add the first user message
        user_message = MessageAction(content='First user message')
        user_message._source = EventSource.USER  # type: ignore[attr-defined]
        event_stream.add_event(user_message, EventSource.USER)

        # Create and add the microagent action
        microagent_action = RecallAction(
            query='First user message', recall_type=RecallType.WORKSPACE_CONTEXT
        )
        microagent_action._source = EventSource.USER  # type: ignore[attr-defined]
        event_stream.add_event(microagent_action, EventSource.USER)

        # Give it a little time to process
        time.sleep(0.3)

        # Get all events from the stream
        events = list(event_stream.get_events())

        # Find the RecallObservation event
        microagent_obs_events = [
            event for event in events if isinstance(event, RecallObservation)
        ]

        # We should have one RecallObservation
        assert len(microagent_obs_events) > 0

        # Get the first RecallObservation
        observation = microagent_obs_events[0]
        assert observation.recall_type == RecallType.WORKSPACE_CONTEXT
        assert observation.repo_name == 'owner/repo'
        assert observation.repo_directory == '/workspace/repo'
        assert 'This is the first test repository' in observation.repo_instructions
        assert 'This is the second test repository' in observation.repo_instructions

    # Clean up
    os.remove(os.path.join(prompt_dir, 'micro', f'{repo_microagent1_name}.md'))
    os.remove(os.path.join(prompt_dir, 'micro', f'{repo_microagent2_name}.md'))
