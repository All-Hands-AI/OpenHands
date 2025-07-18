"""Test cases for EventStream secret replacement functionality."""

from datetime import datetime

from openhands.events.action import CmdRunAction
from openhands.events.serialization.event import event_to_dict
from openhands.events.stream import EventStream
from openhands.storage import get_file_store


class TestEventStreamSecrets:
    """Test secret replacement in EventStream."""

    def test_secrets_replaced_in_content(self):
        """Test that secrets are properly replaced in event content."""
        file_store = get_file_store('memory', {})
        stream = EventStream('test_session', file_store)

        # Set up a secret
        stream.set_secrets({'api_key': 'secret123'})

        # Create an event with the secret in the command
        action = CmdRunAction(
            command='curl -H "Authorization: Bearer secret123" https://api.example.com'
        )
        action._timestamp = datetime.now().isoformat()

        # Convert to dict and apply secret replacement
        data = event_to_dict(action)
        data_with_secrets_replaced = stream._replace_secrets(data)

        # The secret should be replaced in the command
        assert '<secret_hidden>' in data_with_secrets_replaced['args']['command']
        assert 'secret123' not in data_with_secrets_replaced['args']['command']

    def test_timestamp_not_affected_by_secret_replacement(self):
        """Test that timestamps are not corrupted by secret replacement."""
        file_store = get_file_store('memory', {})
        stream = EventStream('test_session', file_store)

        # Set up a secret that appears in the current date (e.g., "18" for 2025-07-18)
        stream.set_secrets({'test_secret': '18'})

        # Create an event with a timestamp
        action = CmdRunAction(command='echo "hello world"')
        action._timestamp = '2025-07-18T17:01:36.799608'  # Contains "18"

        # Convert to dict and apply secret replacement
        data = event_to_dict(action)
        original_timestamp = data['timestamp']
        data_with_secrets_replaced = stream._replace_secrets(data)

        # The timestamp should NOT be affected by secret replacement
        assert data_with_secrets_replaced['timestamp'] == original_timestamp
        assert '<secret_hidden>' not in data_with_secrets_replaced['timestamp']
        assert (
            '18' in data_with_secrets_replaced['timestamp']
        )  # Original value preserved

    def test_protected_fields_not_affected_by_secret_replacement(self):
        """Test that protected system fields are not affected by secret replacement."""
        file_store = get_file_store('memory', {})
        stream = EventStream('test_session', file_store)

        # Set up secrets that might appear in system fields
        stream.set_secrets(
            {
                'secret1': '123',  # Could appear in ID
                'secret2': 'user',  # Could appear in source
                'secret3': 'run',  # Could appear in action/observation
                'secret4': 'Running',  # Could appear in message
            }
        )

        # Create test data with protected fields
        data = {
            'id': 123,
            'timestamp': '2025-07-18T17:01:36.799608',
            'source': 'user',
            'cause': 123,
            'action': 'run',
            'observation': 'run',
            'message': 'Running command: echo hello',
            'content': 'This contains secret1: 123 and secret2: user and secret3: run',
        }

        data_with_secrets_replaced = stream._replace_secrets(data)

        # Protected fields should not be affected at top level
        assert data_with_secrets_replaced['id'] == 123
        assert data_with_secrets_replaced['timestamp'] == '2025-07-18T17:01:36.799608'
        assert data_with_secrets_replaced['source'] == 'user'
        assert data_with_secrets_replaced['cause'] == 123
        assert data_with_secrets_replaced['action'] == 'run'
        assert data_with_secrets_replaced['observation'] == 'run'
        assert data_with_secrets_replaced['message'] == 'Running command: echo hello'

        # But non-protected fields should have secrets replaced
        assert '<secret_hidden>' in data_with_secrets_replaced['content']
        assert '123' not in data_with_secrets_replaced['content']
        assert 'user' not in data_with_secrets_replaced['content']
        # Note: 'run' should still be replaced in content since it's not a protected field

    def test_nested_dict_secret_replacement(self):
        """Test that secrets are replaced in nested dictionaries while preserving protected fields."""
        file_store = get_file_store('memory', {})
        stream = EventStream('test_session', file_store)

        stream.set_secrets({'secret': 'password123'})

        # Create nested data structure
        data = {
            'timestamp': '2025-07-18T17:01:36.799608',
            'args': {
                'command': 'login --password password123',
                'env': {
                    'SECRET_KEY': 'password123',
                    'timestamp': 'password123_timestamp',  # This should be replaced since it's not top-level
                },
            },
        }

        data_with_secrets_replaced = stream._replace_secrets(data)

        # Top-level timestamp should be protected
        assert data_with_secrets_replaced['timestamp'] == '2025-07-18T17:01:36.799608'

        # Nested secrets should be replaced
        assert '<secret_hidden>' in data_with_secrets_replaced['args']['command']
        assert (
            data_with_secrets_replaced['args']['env']['SECRET_KEY'] == '<secret_hidden>'
        )
        assert (
            '<secret_hidden>' in data_with_secrets_replaced['args']['env']['timestamp']
        )

        # Original secret should not appear in nested content
        assert 'password123' not in data_with_secrets_replaced['args']['command']
        assert (
            'password123' not in data_with_secrets_replaced['args']['env']['SECRET_KEY']
        )
        assert (
            'password123' not in data_with_secrets_replaced['args']['env']['timestamp']
        )


if __name__ == '__main__':
    test = TestEventStreamSecrets()
    try:
        test.test_secrets_replaced_in_content()
        print('✓ test_secrets_replaced_in_content passed')
    except Exception as e:
        print(f'✗ test_secrets_replaced_in_content failed: {e}')

    try:
        test.test_timestamp_not_affected_by_secret_replacement()
        print('✓ test_timestamp_not_affected_by_secret_replacement passed')
    except Exception as e:
        print(f'✗ test_timestamp_not_affected_by_secret_replacement failed: {e}')

    try:
        test.test_protected_fields_not_affected_by_secret_replacement()
        print('✓ test_protected_fields_not_affected_by_secret_replacement passed')
    except Exception as e:
        print(f'✗ test_protected_fields_not_affected_by_secret_replacement failed: {e}')

    try:
        test.test_nested_dict_secret_replacement()
        print('✓ test_nested_dict_secret_replacement passed')
    except Exception as e:
        print(f'✗ test_nested_dict_secret_replacement failed: {e}')
        import traceback

        traceback.print_exc()

    print('All tests completed!')
