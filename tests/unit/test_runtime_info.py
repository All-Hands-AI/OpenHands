from openhands.utils.prompt import RuntimeInfo


def test_runtime_info_default_initialization():
    """Test that RuntimeInfo initializes with default values."""
    runtime_info = RuntimeInfo(date='2025-05-15')

    assert runtime_info.date == '2025-05-15'
    assert runtime_info.available_hosts == {}
    assert runtime_info.additional_agent_instructions == ''
    assert runtime_info.custom_secrets_descriptions == {}


def test_runtime_info_custom_initialization():
    """Test that RuntimeInfo initializes with custom values."""
    runtime_info = RuntimeInfo(
        date='2025-05-15',
        available_hosts={'host1': 8080, 'host2': 8081},
        additional_agent_instructions='Custom instructions',
        custom_secrets_descriptions={
            'API_KEY': 'Your API key for service X',
            'DB_PASSWORD': 'Database password',
        },
    )

    assert runtime_info.date == '2025-05-15'
    assert runtime_info.available_hosts == {'host1': 8080, 'host2': 8081}
    assert runtime_info.additional_agent_instructions == 'Custom instructions'
    assert runtime_info.custom_secrets_descriptions == {
        'API_KEY': 'Your API key for service X',
        'DB_PASSWORD': 'Database password',
    }


def test_runtime_info_custom_secrets_descriptions_empty():
    """Test that custom_secrets_descriptions can be empty."""
    runtime_info = RuntimeInfo(date='2025-05-15', custom_secrets_descriptions={})

    assert runtime_info.custom_secrets_descriptions == {}


def test_runtime_info_custom_secrets_descriptions_single_item():
    """Test that custom_secrets_descriptions can have a single item."""
    runtime_info = RuntimeInfo(
        date='2025-05-15',
        custom_secrets_descriptions={'API_KEY': 'Your API key for service X'},
    )

    assert runtime_info.custom_secrets_descriptions == {
        'API_KEY': 'Your API key for service X'
    }


def test_runtime_info_custom_secrets_descriptions_multiple_items():
    """Test that custom_secrets_descriptions can have multiple items."""
    secrets_dict = {
        'API_KEY': 'Your API key for service X',
        'DB_PASSWORD': 'Database password',
        'SECRET_TOKEN': 'Authentication token',
        'PRIVATE_KEY': 'SSH private key',
    }

    runtime_info = RuntimeInfo(
        date='2025-05-15', custom_secrets_descriptions=secrets_dict
    )

    assert runtime_info.custom_secrets_descriptions == secrets_dict
