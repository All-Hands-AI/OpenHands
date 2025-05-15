from openhands.events.event import RecallType
from openhands.events.observation.agent import RecallObservation
from openhands.events.serialization import event_from_dict, event_to_dict


def test_recall_observation_serialization_with_custom_secrets_descriptions():
    """Test that RecallObservation serializes and deserializes custom_secrets_descriptions correctly."""
    # Create a RecallObservation with custom_secrets_descriptions
    custom_secrets = {
        'API_KEY': 'Your API key for service X',
        'DB_PASSWORD': 'Database password',
    }

    observation = RecallObservation(
        recall_type=RecallType.WORKSPACE_CONTEXT,
        repo_name='test_repo',
        repo_directory='/workspace/test_repo',
        repo_instructions='Test instructions',
        runtime_hosts={'host1': 8080},
        additional_agent_instructions='Custom instructions',
        date='2025-05-15',
        custom_secrets_descriptions=custom_secrets,
        content='Test content',
        microagent_knowledge=[],
    )

    # Serialize the observation
    serialized = event_to_dict(observation)

    # Verify that custom_secrets_descriptions is included in the serialized data
    assert 'extras' in serialized
    assert 'custom_secrets_descriptions' in serialized['extras']
    assert serialized['extras']['custom_secrets_descriptions'] == custom_secrets

    # Deserialize the observation
    deserialized = event_from_dict(serialized)

    # Verify that custom_secrets_descriptions is correctly deserialized
    assert isinstance(deserialized, RecallObservation)
    assert deserialized.custom_secrets_descriptions == custom_secrets


def test_recall_observation_serialization_with_empty_custom_secrets_descriptions():
    """Test that RecallObservation serializes and deserializes empty custom_secrets_descriptions correctly."""
    # Create a RecallObservation with empty custom_secrets_descriptions
    observation = RecallObservation(
        recall_type=RecallType.WORKSPACE_CONTEXT,
        repo_name='test_repo',
        repo_directory='/workspace/test_repo',
        repo_instructions='Test instructions',
        runtime_hosts={'host1': 8080},
        additional_agent_instructions='Custom instructions',
        date='2025-05-15',
        custom_secrets_descriptions={},
        content='Test content',
        microagent_knowledge=[],
    )

    # Serialize the observation
    serialized = event_to_dict(observation)

    # Verify that custom_secrets_descriptions is included in the serialized data
    assert 'extras' in serialized
    assert 'custom_secrets_descriptions' in serialized['extras']
    assert serialized['extras']['custom_secrets_descriptions'] == {}

    # Deserialize the observation
    deserialized = event_from_dict(serialized)

    # Verify that custom_secrets_descriptions is correctly deserialized
    assert isinstance(deserialized, RecallObservation)
    assert deserialized.custom_secrets_descriptions == {}
