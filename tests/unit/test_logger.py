import os
import logging
from openhands.core.logger import SensitiveDataFilter

def test_sensitive_data_filter_basic():
    # Create a test logger
    logger = logging.getLogger('test_logger')
    filter = SensitiveDataFilter()
    
    # Create a log record with sensitive data
    os.environ['API_SECRET'] = 'super-secret-123'
    os.environ['AUTH_TOKEN'] = 'auth-token-456'
    os.environ['NORMAL_VAR'] = 'normal-value'
    
    record = logging.LogRecord(
        name='test_logger',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg=f'API Secret: {os.environ["API_SECRET"]}, Token: {os.environ["AUTH_TOKEN"]}, Normal: {os.environ["NORMAL_VAR"]}',
        args=(),
        exc_info=None
    )
    
    # Apply the filter
    filter.filter(record)
    
    # Check that sensitive data is masked but normal data isn't
    assert '******' in record.msg
    assert 'super-secret-123' not in record.msg
    assert 'auth-token-456' not in record.msg
    assert 'normal-value' in record.msg

def test_sensitive_data_filter_empty_values():
    # Test with empty environment variables
    logger = logging.getLogger('test_logger')
    filter = SensitiveDataFilter()
    
    record = logging.LogRecord(
        name='test_logger',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg='No sensitive data here',
        args=(),
        exc_info=None
    )
    
    # Apply the filter
    filter.filter(record)
    
    # Message should remain unchanged
    assert record.msg == 'No sensitive data here'

def test_sensitive_data_filter_multiple_occurrences():
    # Test with multiple occurrences of the same sensitive data
    logger = logging.getLogger('test_logger')
    filter = SensitiveDataFilter()
    
    os.environ['API_KEY'] = 'secret-key-789'
    
    # Create a message with multiple occurrences of the same sensitive data
    record = logging.LogRecord(
        name='test_logger',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg=f'Key1: {os.environ["API_KEY"]}, Key2: {os.environ["API_KEY"]}',
        args=(),
        exc_info=None
    )
    
    # Apply the filter
    filter.filter(record)
    
    # Check that all occurrences are masked
    assert record.msg.count('******') == 2
    assert 'secret-key-789' not in record.msg

def test_sensitive_data_filter_case_sensitivity():
    # Test with different case variations in environment variable names
    logger = logging.getLogger('test_logger')
    filter = SensitiveDataFilter()
    
    os.environ['secret_KEY'] = 'secret-value-1'
    os.environ['API_secret'] = 'secret-value-2'
    os.environ['TOKEN_code'] = 'secret-value-3'
    
    record = logging.LogRecord(
        name='test_logger',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg=f'Values: {os.environ["secret_KEY"]}, {os.environ["API_secret"]}, {os.environ["TOKEN_code"]}',
        args=(),
        exc_info=None
    )
    
    # Apply the filter
    filter.filter(record)
    
    # Check that all sensitive values are masked regardless of case
    assert 'secret-value-1' not in record.msg
    assert 'secret-value-2' not in record.msg
    assert 'secret-value-3' not in record.msg
    assert record.msg.count('******') == 3