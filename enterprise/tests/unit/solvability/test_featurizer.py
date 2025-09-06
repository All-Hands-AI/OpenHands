import pytest
from integrations.solvability.models.featurizer import Feature, FeatureEmbedding


def test_feature_to_tool_description_field():
    """Test to_tool_description_field property."""
    feature = Feature(identifier='test', description='Test description')
    field = feature.to_tool_description_field

    # There's not much structure here, but we can check the expected type and make
    # sure the other fields are propagated.
    assert field['type'] == 'boolean'
    assert field['description'] == 'Test description'


def test_feature_embedding_dimensions(feature_embedding):
    """Test dimensions property."""
    dimensions = feature_embedding.dimensions
    assert isinstance(dimensions, list)
    assert set(dimensions) == {'feature1', 'feature2', 'feature3'}


def test_feature_embedding_coefficients(feature_embedding):
    """Test coefficient method."""
    # These values are manually computed from the results in the fixture's samples.
    assert feature_embedding.coefficient('feature1') == 0.5
    assert feature_embedding.coefficient('feature2') == 0.5
    assert feature_embedding.coefficient('feature3') == 1.0

    # Non-existent features should not have a coefficient.
    assert feature_embedding.coefficient('non_existent') is None


def test_featurizer_system_message(featurizer):
    """Test system_message method."""
    message = featurizer.system_message()
    assert message['role'] == 'system'
    assert message['content'] == 'Test system prompt'


def test_featurizer_user_message(featurizer):
    """Test user_message method."""
    # With cache
    message = featurizer.user_message('Test issue', set_cache=True)
    assert message['role'] == 'user'
    assert message['content'] == 'Test message prefix: Test issue'
    assert 'cache_control' in message
    assert message['cache_control']['type'] == 'ephemeral'

    # Without cache
    message = featurizer.user_message('Test issue', set_cache=False)
    assert message['role'] == 'user'
    assert message['content'] == 'Test message prefix: Test issue'
    assert 'cache_control' not in message


def test_featurizer_tool_choice(featurizer):
    """Test tool_choice property."""
    tool_choice = featurizer.tool_choice
    assert tool_choice['type'] == 'function'
    assert tool_choice['function']['name'] == 'call_featurizer'


def test_featurizer_tool_description(featurizer):
    """Test tool_description property."""
    tool_desc = featurizer.tool_description
    assert tool_desc['type'] == 'function'
    assert tool_desc['function']['name'] == 'call_featurizer'
    assert 'description' in tool_desc['function']

    # Check that all features are included in the properties
    properties = tool_desc['function']['parameters']['properties']
    for feature in featurizer.features:
        assert feature.identifier in properties
        assert properties[feature.identifier]['type'] == 'boolean'
        assert properties[feature.identifier]['description'] == feature.description


@pytest.mark.parametrize('samples', [1, 10, 100])
def test_featurizer_embed(samples, featurizer, mock_llm_config):
    """Test the embed method to ensure it generates the right number of samples and computes the metadata correctly."""
    embedding = featurizer.embed(
        'Test issue', llm_config=mock_llm_config, samples=samples
    )

    # We should get the right number of samples.
    assert len(embedding.samples) == samples

    # Because of the mocks, all the samples should be the same (and be correct).
    assert all(sample == embedding.samples[0] for sample in embedding.samples)
    assert embedding.samples[0]['feature1'] is True
    assert embedding.samples[0]['feature2'] is False
    assert embedding.samples[0]['feature3'] is True

    # And all the metadata should be correct (we know the token counts because
    # they're mocked, so just count once per sample).
    assert embedding.prompt_tokens == 10 * samples
    assert embedding.completion_tokens == 5 * samples

    # These timings are real, so best we can do is check that they're positive.
    assert embedding.response_latency > 0.0


@pytest.mark.parametrize('samples', [1, 10, 100])
@pytest.mark.parametrize('batch_size', [1, 10, 100])
def test_featurizer_embed_batch(samples, batch_size, featurizer, mock_llm_config):
    """Test the embed_batch method to ensure it correctly handles all issues in the batch."""
    embeddings = featurizer.embed_batch(
        [f'Issue {i}' for i in range(batch_size)],
        llm_config=mock_llm_config,
        samples=samples,
    )

    # Make sure that we get an embedding for each issue.
    assert len(embeddings) == batch_size

    # Since the embeddings are computed from a mocked completionc all, they should
    # all be the same. We can check that they're well-formatted by applying the same
    # checks as in `test_featurizer_embed`.
    for embedding in embeddings:
        assert all(sample == embedding.samples[0] for sample in embedding.samples)
        assert embedding.samples[0]['feature1'] is True
        assert embedding.samples[0]['feature2'] is False
        assert embedding.samples[0]['feature3'] is True

        assert len(embedding.samples) == samples
        assert embedding.prompt_tokens == 10 * samples
        assert embedding.completion_tokens == 5 * samples
        assert embedding.response_latency >= 0.0


def test_featurizer_embed_batch_thread_safety(featurizer, mock_llm_config, monkeypatch):
    """Test embed_batch maintains correct ordering and handles concurrent execution safely."""
    import time
    from unittest.mock import MagicMock

    # Create unique responses for each issue to verify ordering
    def create_mock_response(issue_index):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [MagicMock()]
        # Each issue gets a unique feature pattern based on its index
        mock_response.choices[0].message.tool_calls[0].function.arguments = (
            f'{{"feature1": {str(issue_index % 2 == 0).lower()}, '
            f'"feature2": {str(issue_index % 3 == 0).lower()}, '
            f'"feature3": {str(issue_index % 5 == 0).lower()}}}'
        )
        mock_response.usage.prompt_tokens = 10 + issue_index
        mock_response.usage.completion_tokens = 5 + issue_index
        return mock_response

    # Track call order and add delays to simulate varying processing times
    call_count = 0
    call_order = []

    def mock_completion(*args, **kwargs):
        nonlocal call_count
        # Extract issue index from the message content
        messages = kwargs.get('messages', args[0] if args else [])
        message_content = messages[1]['content']
        issue_index = int(message_content.split('Issue ')[-1])
        call_order.append(issue_index)

        # Add varying delays to simulate real-world conditions
        # Later issues process faster to test race conditions
        delay = 0.01 * (20 - issue_index)
        time.sleep(delay)

        call_count += 1
        return create_mock_response(issue_index)

    def mock_llm_class(*args, **kwargs):
        mock_llm_instance = MagicMock()
        mock_llm_instance.completion = mock_completion
        return mock_llm_instance

    monkeypatch.setattr(
        'integrations.solvability.models.featurizer.LLM', mock_llm_class
    )

    # Test with a large enough batch to stress concurrency
    batch_size = 20
    issues = [f'Issue {i}' for i in range(batch_size)]

    embeddings = featurizer.embed_batch(issues, llm_config=mock_llm_config, samples=1)

    # Verify we got all embeddings
    assert len(embeddings) == batch_size

    # Verify each embedding corresponds to its correct issue index
    for i, embedding in enumerate(embeddings):
        assert len(embedding.samples) == 1
        sample = embedding.samples[0]

        # Check the unique pattern matches the issue index
        assert sample['feature1'] == (i % 2 == 0)
        assert sample['feature2'] == (i % 3 == 0)
        assert sample['feature3'] == (i % 5 == 0)

        # Check token counts match
        assert embedding.prompt_tokens == 10 + i
        assert embedding.completion_tokens == 5 + i

    # Verify all issues were processed
    assert call_count == batch_size
    assert len(set(call_order)) == batch_size  # All unique indices


def test_featurizer_embed_batch_exception_handling(
    featurizer, mock_llm_config, monkeypatch
):
    """Test embed_batch handles exceptions in individual tasks correctly."""
    from unittest.mock import MagicMock

    def mock_completion(*args, **kwargs):
        # Extract issue index from the message content
        messages = kwargs.get('messages', args[0] if args else [])
        message_content = messages[1]['content']
        issue_index = int(message_content.split('Issue ')[-1])

        # Make some issues fail
        if issue_index in [2, 5, 7]:
            raise ValueError(f'Simulated error for issue {issue_index}')

        # Return normal response for others
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [MagicMock()]
        mock_response.choices[0].message.tool_calls[
            0
        ].function.arguments = '{"feature1": true, "feature2": false, "feature3": true}'
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        return mock_response

    def mock_llm_class(*args, **kwargs):
        mock_llm_instance = MagicMock()
        mock_llm_instance.completion = mock_completion
        return mock_llm_instance

    monkeypatch.setattr(
        'integrations.solvability.models.featurizer.LLM', mock_llm_class
    )

    issues = [f'Issue {i}' for i in range(10)]

    # The method should raise an exception when any task fails
    with pytest.raises(ValueError) as exc_info:
        featurizer.embed_batch(issues, llm_config=mock_llm_config, samples=1)

    # Verify it's one of our expected errors
    assert 'Simulated error for issue' in str(exc_info.value)


def test_featurizer_embed_batch_no_none_values(featurizer, mock_llm_config):
    """Test that embed_batch never returns None values in the results list."""
    # Test with various batch sizes to ensure no None values slip through
    for batch_size in [1, 5, 10, 20]:
        issues = [f'Issue {i}' for i in range(batch_size)]
        embeddings = featurizer.embed_batch(
            issues, llm_config=mock_llm_config, samples=1
        )

        # Verify no None values in results
        assert all(embedding is not None for embedding in embeddings)
        assert all(isinstance(embedding, FeatureEmbedding) for embedding in embeddings)
