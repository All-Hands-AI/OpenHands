import logging
from unittest.mock import patch

from openhands.core.logger import SensitiveDataFilter


@patch.dict(
    'os.environ',
    {
        'API_SECRET': 'super-secret-123',
        'AUTH_TOKEN': 'auth-token-456',
        'NORMAL_VAR': 'normal-value',
    },
    clear=True,
)
def test_sensitive_data_filter_basic():
    # Create a filter instance
    filter = SensitiveDataFilter()

    # Create a log record with sensitive data
    record = logging.LogRecord(
        name='test_logger',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg='API Secret: super-secret-123, Token: auth-token-456, Normal: normal-value',
        args=(),
        exc_info=None,
    )

    # Apply the filter
    filter.filter(record)

    # Check that sensitive data is masked but normal data isn't
    assert '******' in record.msg
    assert 'super-secret-123' not in record.msg
    assert 'auth-token-456' not in record.msg
    assert 'normal-value' in record.msg


@patch.dict('os.environ', {}, clear=True)
def test_sensitive_data_filter_empty_values():
    # Test with empty environment variables
    filter = SensitiveDataFilter()

    record = logging.LogRecord(
        name='test_logger',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg='No sensitive data here',
        args=(),
        exc_info=None,
    )

    # Apply the filter
    filter.filter(record)

    # Message should remain unchanged
    assert record.msg == 'No sensitive data here'


@patch.dict('os.environ', {'API_KEY': 'secret-key-789'}, clear=True)
def test_sensitive_data_filter_multiple_occurrences():
    # Test with multiple occurrences of the same sensitive data
    filter = SensitiveDataFilter()

    # Create a message with multiple occurrences of the same sensitive data
    record = logging.LogRecord(
        name='test_logger',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg='Key1: secret-key-789, Key2: secret-key-789',
        args=(),
        exc_info=None,
    )

    # Apply the filter
    filter.filter(record)

    # Check that all occurrences are masked
    assert record.msg.count('******') == 2
    assert 'secret-key-789' not in record.msg


@patch.dict(
    'os.environ',
    {
        'secret_KEY': 'secret-value-1',
        'API_secret': 'secret-value-2',
        'TOKEN_code': 'secret-value-3',
    },
    clear=True,
)
def test_sensitive_data_filter_case_sensitivity():
    # Test with different case variations in environment variable names
    filter = SensitiveDataFilter()

    record = logging.LogRecord(
        name='test_logger',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg='Values: secret-value-1, secret-value-2, secret-value-3',
        args=(),
        exc_info=None,
    )

    # Apply the filter
    filter.filter(record)

    # Check that all sensitive values are masked regardless of case
    assert 'secret-value-1' not in record.msg
    assert 'secret-value-2' not in record.msg
    assert 'secret-value-3' not in record.msg
    assert record.msg.count('******') == 3
