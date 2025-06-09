import os
from pathlib import Path

from openhands.integrations.service_types import ProviderType
from openhands.microagent import BaseMicroagent, KnowledgeMicroagent


def test_bitbucket_microagent_loading():
    """Test that the Bitbucket microagent can be loaded correctly."""
    microagent_path = (
        Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        / 'microagents'
        / 'bitbucket.md'
    )
    assert microagent_path.exists(), 'Bitbucket microagent file not found'

    microagent = BaseMicroagent.load(microagent_path)

    assert isinstance(microagent, KnowledgeMicroagent)
    assert microagent.name == 'bitbucket'
    assert microagent.metadata.type == 'knowledge'
    assert microagent.metadata.version == '1.0.0'
    assert microagent.metadata.agent == 'CodeActAgent'
    assert 'bitbucket' in microagent.metadata.triggers
    assert 'git' in microagent.metadata.triggers


def test_bitbucket_microagent_trigger_matching():
    """Test that the Bitbucket microagent triggers correctly."""
    microagent_path = (
        Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        / 'microagents'
        / 'bitbucket.md'
    )
    microagent = BaseMicroagent.load(microagent_path)

    assert isinstance(microagent, KnowledgeMicroagent)

    # Test that the microagent triggers on "bitbucket"
    assert microagent.match_trigger('I need help with bitbucket') == 'bitbucket'

    # Test that the microagent triggers on "git"
    assert microagent.match_trigger('I need help with git') == 'git'

    # Test that the microagent doesn't trigger on unrelated text
    assert microagent.match_trigger('I need help with something else') is None


def test_provider_type_enum():
    """Test that the ProviderType enum includes Bitbucket."""
    assert ProviderType.BITBUCKET.value == 'bitbucket'

    # Test that we can convert from string to enum
    assert ProviderType('bitbucket') == ProviderType.BITBUCKET
