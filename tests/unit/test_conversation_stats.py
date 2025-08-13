import base64
import pickle
from unittest.mock import patch

import pytest

from openhands.core.config import LLMConfig, OpenHandsConfig
from openhands.llm.llm import LLM
from openhands.llm.llm_registry import LLMRegistry, RegistryEvent
from openhands.llm.metrics import Metrics
from openhands.server.services.conversation_stats import ConversationStats
from openhands.storage.memory import InMemoryFileStore


@pytest.fixture
def mock_file_store():
    """Create a mock file store for testing."""
    return InMemoryFileStore({})


@pytest.fixture
def conversation_stats(mock_file_store):
    """Create a ConversationStats instance for testing."""
    return ConversationStats(
        file_store=mock_file_store,
        conversation_id='test-conversation-id',
        user_id='test-user-id',
    )


@pytest.fixture
def mock_llm_registry():
    """Create a mock LLM registry that properly simulates LLM registration."""
    config = OpenHandsConfig()
    registry = LLMRegistry(config=config, agent_cls=None, retry_listener=None)
    return registry


@pytest.fixture
def connected_registry_and_stats(mock_llm_registry, conversation_stats):
    """Connect the LLMRegistry and ConversationStats properly."""
    # Subscribe to LLM registry events to track metrics
    mock_llm_registry.subscribe(conversation_stats.register_llm)
    return mock_llm_registry, conversation_stats


def test_conversation_stats_initialization(conversation_stats):
    """Test that ConversationStats initializes correctly."""
    assert conversation_stats.conversation_id == 'test-conversation-id'
    assert conversation_stats.user_id == 'test-user-id'
    assert conversation_stats.service_to_metrics == {}
    assert isinstance(conversation_stats.restored_metrics, dict)


def test_save_metrics(conversation_stats, mock_file_store):
    """Test that metrics are saved correctly."""
    # Add a service with metrics
    service_id = 'test-service'
    metrics = Metrics(model_name='gpt-4')
    metrics.add_cost(0.05)
    conversation_stats.service_to_metrics[service_id] = metrics

    # Save metrics
    conversation_stats.save_metrics()

    # Verify that metrics were saved to the file store
    try:
        # Verify the saved content can be decoded and unpickled
        encoded = mock_file_store.read(conversation_stats.metrics_path)
        pickled = base64.b64decode(encoded)
        restored = pickle.loads(pickled)

        assert service_id in restored
        assert restored[service_id].accumulated_cost == 0.05
    except FileNotFoundError:
        pytest.fail(f'File not found: {conversation_stats.metrics_path}')


def test_maybe_restore_metrics(mock_file_store):
    """Test that metrics are restored correctly."""
    # Create metrics to save
    service_id = 'test-service'
    metrics = Metrics(model_name='gpt-4')
    metrics.add_cost(0.1)
    service_to_metrics = {service_id: metrics}

    # Serialize and save metrics
    pickled = pickle.dumps(service_to_metrics)
    serialized_metrics = base64.b64encode(pickled).decode('utf-8')

    # Create a new ConversationStats with pre-populated file store
    conversation_id = 'test-conversation-id'
    user_id = 'test-user-id'

    # Get the correct path using the same function as ConversationStats
    from openhands.storage.locations import get_conversation_stats_filename

    metrics_path = get_conversation_stats_filename(conversation_id, user_id)

    # Write to the correct path
    mock_file_store.write(metrics_path, serialized_metrics)

    # Create ConversationStats which should restore metrics
    stats = ConversationStats(
        file_store=mock_file_store, conversation_id=conversation_id, user_id=user_id
    )

    # Verify metrics were restored
    assert service_id in stats.restored_metrics
    assert stats.restored_metrics[service_id].accumulated_cost == 0.1


def test_get_combined_metrics(conversation_stats):
    """Test that combined metrics are calculated correctly."""
    # Add multiple services with metrics
    service1 = 'service1'
    metrics1 = Metrics(model_name='gpt-4')
    metrics1.add_cost(0.05)
    metrics1.add_token_usage(
        prompt_tokens=100,
        completion_tokens=50,
        cache_read_tokens=0,
        cache_write_tokens=0,
        context_window=8000,
        response_id='resp1',
    )

    service2 = 'service2'
    metrics2 = Metrics(model_name='gpt-3.5')
    metrics2.add_cost(0.02)
    metrics2.add_token_usage(
        prompt_tokens=200,
        completion_tokens=100,
        cache_read_tokens=0,
        cache_write_tokens=0,
        context_window=4000,
        response_id='resp2',
    )

    conversation_stats.service_to_metrics[service1] = metrics1
    conversation_stats.service_to_metrics[service2] = metrics2

    # Get combined metrics
    combined = conversation_stats.get_combined_metrics()

    # Verify combined metrics
    assert combined.accumulated_cost == 0.07  # 0.05 + 0.02
    assert combined.accumulated_token_usage.prompt_tokens == 300  # 100 + 200
    assert combined.accumulated_token_usage.completion_tokens == 150  # 50 + 100
    assert (
        combined.accumulated_token_usage.context_window == 8000
    )  # max of 8000 and 4000


def test_get_metrics_for_service(conversation_stats):
    """Test that metrics for a specific service are retrieved correctly."""
    # Add a service with metrics
    service_id = 'test-service'
    metrics = Metrics(model_name='gpt-4')
    metrics.add_cost(0.05)
    conversation_stats.service_to_metrics[service_id] = metrics

    # Get metrics for the service
    retrieved_metrics = conversation_stats.get_metrics_for_service(service_id)

    # Verify metrics
    assert retrieved_metrics.accumulated_cost == 0.05
    assert retrieved_metrics is metrics  # Should be the same object

    # Test getting metrics for non-existent service
    # Use a specific exception message pattern instead of a blind Exception
    with pytest.raises(Exception, match='LLM service does not exist'):
        conversation_stats.get_metrics_for_service('non-existent-service')


def test_register_llm_with_new_service(conversation_stats):
    """Test registering a new LLM service."""
    # Create a real LLM instance with a mock config
    llm_config = LLMConfig(
        model='gpt-4o',
        api_key='test_key',
        num_retries=2,
        retry_min_wait=1,
        retry_max_wait=2,
    )

    # Patch the LLM class to avoid actual API calls
    with patch('openhands.llm.llm.litellm_completion'):
        llm = LLM(service_id='new-service', config=llm_config)

        # Create a registry event
        service_id = 'new-service'
        event = RegistryEvent(llm=llm, service_id=service_id)

        # Register the LLM
        conversation_stats.register_llm(event)

        # Verify the service was registered
        assert service_id in conversation_stats.service_to_metrics
        assert conversation_stats.service_to_metrics[service_id] is llm.metrics


def test_register_llm_with_restored_metrics(conversation_stats):
    """Test registering an LLM service with restored metrics."""
    # Create restored metrics
    service_id = 'restored-service'
    restored_metrics = Metrics(model_name='gpt-4')
    restored_metrics.add_cost(0.1)
    conversation_stats.restored_metrics = {service_id: restored_metrics}

    # Create a real LLM instance with a mock config
    llm_config = LLMConfig(
        model='gpt-4o',
        api_key='test_key',
        num_retries=2,
        retry_min_wait=1,
        retry_max_wait=2,
    )

    # Patch the LLM class to avoid actual API calls
    with patch('openhands.llm.llm.litellm_completion'):
        llm = LLM(service_id=service_id, config=llm_config)

        # Create a registry event
        event = RegistryEvent(llm=llm, service_id=service_id)

        # Register the LLM
        conversation_stats.register_llm(event)

        # Verify the service was registered with restored metrics
        assert service_id in conversation_stats.service_to_metrics
        assert conversation_stats.service_to_metrics[service_id] is llm.metrics
        assert llm.metrics.accumulated_cost == 0.1  # Restored cost

        # Verify restored_metrics was deleted
        assert not hasattr(conversation_stats, 'restored_metrics')


def test_llm_registry_notifications(connected_registry_and_stats):
    """Test that LLM registry notifications update conversation stats."""
    mock_llm_registry, conversation_stats = connected_registry_and_stats

    # Create a new LLM through the registry
    service_id = 'test-service'
    llm_config = LLMConfig(
        model='gpt-4o',
        api_key='test_key',
        num_retries=2,
        retry_min_wait=1,
        retry_max_wait=2,
    )

    # Get LLM from registry (this should trigger the notification)
    llm = mock_llm_registry.get_llm(service_id, llm_config)

    # Verify the service was registered in conversation stats
    assert service_id in conversation_stats.service_to_metrics
    assert conversation_stats.service_to_metrics[service_id] is llm.metrics

    # Add some metrics to the LLM
    llm.metrics.add_cost(0.05)
    llm.metrics.add_token_usage(
        prompt_tokens=100,
        completion_tokens=50,
        cache_read_tokens=0,
        cache_write_tokens=0,
        context_window=8000,
        response_id='resp1',
    )

    # Verify the metrics are reflected in conversation stats
    assert conversation_stats.service_to_metrics[service_id].accumulated_cost == 0.05
    assert (
        conversation_stats.service_to_metrics[
            service_id
        ].accumulated_token_usage.prompt_tokens
        == 100
    )
    assert (
        conversation_stats.service_to_metrics[
            service_id
        ].accumulated_token_usage.completion_tokens
        == 50
    )

    # Get combined metrics and verify
    combined = conversation_stats.get_combined_metrics()
    assert combined.accumulated_cost == 0.05
    assert combined.accumulated_token_usage.prompt_tokens == 100
    assert combined.accumulated_token_usage.completion_tokens == 50


def test_multiple_llm_services(connected_registry_and_stats):
    """Test tracking metrics for multiple LLM services."""
    mock_llm_registry, conversation_stats = connected_registry_and_stats

    # Create multiple LLMs through the registry
    service1 = 'service1'
    service2 = 'service2'

    llm_config1 = LLMConfig(
        model='gpt-4o',
        api_key='test_key',
        num_retries=2,
        retry_min_wait=1,
        retry_max_wait=2,
    )

    llm_config2 = LLMConfig(
        model='gpt-3.5-turbo',
        api_key='test_key',
        num_retries=2,
        retry_min_wait=1,
        retry_max_wait=2,
    )

    # Get LLMs from registry (this should trigger notifications)
    llm1 = mock_llm_registry.get_llm(service1, llm_config1)
    llm2 = mock_llm_registry.get_llm(service2, llm_config2)

    # Add different metrics to each LLM
    llm1.metrics.add_cost(0.05)
    llm1.metrics.add_token_usage(
        prompt_tokens=100,
        completion_tokens=50,
        cache_read_tokens=0,
        cache_write_tokens=0,
        context_window=8000,
        response_id='resp1',
    )

    llm2.metrics.add_cost(0.02)
    llm2.metrics.add_token_usage(
        prompt_tokens=200,
        completion_tokens=100,
        cache_read_tokens=0,
        cache_write_tokens=0,
        context_window=4000,
        response_id='resp2',
    )

    # Verify services were registered in conversation stats
    assert service1 in conversation_stats.service_to_metrics
    assert service2 in conversation_stats.service_to_metrics

    # Verify individual metrics
    assert conversation_stats.service_to_metrics[service1].accumulated_cost == 0.05
    assert conversation_stats.service_to_metrics[service2].accumulated_cost == 0.02

    # Get combined metrics and verify
    combined = conversation_stats.get_combined_metrics()
    assert combined.accumulated_cost == 0.07  # 0.05 + 0.02
    assert combined.accumulated_token_usage.prompt_tokens == 300  # 100 + 200
    assert combined.accumulated_token_usage.completion_tokens == 150  # 50 + 100
    assert (
        combined.accumulated_token_usage.context_window == 8000
    )  # max of 8000 and 4000


def test_save_and_restore_workflow(mock_file_store):
    """Test the full workflow of saving and restoring metrics."""
    # Create initial conversation stats
    conversation_id = 'test-conversation-id'
    user_id = 'test-user-id'

    stats1 = ConversationStats(
        file_store=mock_file_store, conversation_id=conversation_id, user_id=user_id
    )

    # Add a service with metrics
    service_id = 'test-service'
    metrics = Metrics(model_name='gpt-4')
    metrics.add_cost(0.05)
    metrics.add_token_usage(
        prompt_tokens=100,
        completion_tokens=50,
        cache_read_tokens=0,
        cache_write_tokens=0,
        context_window=8000,
        response_id='resp1',
    )
    stats1.service_to_metrics[service_id] = metrics

    # Save metrics
    stats1.save_metrics()

    # Create a new conversation stats instance that should restore the metrics
    stats2 = ConversationStats(
        file_store=mock_file_store, conversation_id=conversation_id, user_id=user_id
    )

    # Verify metrics were restored
    assert service_id in stats2.restored_metrics
    assert stats2.restored_metrics[service_id].accumulated_cost == 0.05
    assert (
        stats2.restored_metrics[service_id].accumulated_token_usage.prompt_tokens == 100
    )
    assert (
        stats2.restored_metrics[service_id].accumulated_token_usage.completion_tokens
        == 50
    )

    # Create a real LLM instance with a mock config
    llm_config = LLMConfig(
        model='gpt-4o',
        api_key='test_key',
        num_retries=2,
        retry_min_wait=1,
        retry_max_wait=2,
    )

    # Patch the LLM class to avoid actual API calls
    with patch('openhands.llm.llm.litellm_completion'):
        llm = LLM(service_id=service_id, config=llm_config)

        # Create a registry event
        event = RegistryEvent(llm=llm, service_id=service_id)

        # Register the LLM to trigger restoration
        stats2.register_llm(event)

        # Verify metrics were applied to the LLM
        assert llm.metrics.accumulated_cost == 0.05
        assert llm.metrics.accumulated_token_usage.prompt_tokens == 100
        assert llm.metrics.accumulated_token_usage.completion_tokens == 50
