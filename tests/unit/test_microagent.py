import os
import tempfile

import pytest

from openhands.utils.microagent import MicroAgent, MicroAgentMetadata


def test_microagent_metadata():
    metadata = MicroAgentMetadata(
        name='test_agent', agent='test_agent_type', triggers=['trigger1', 'trigger2']
    )
    assert metadata.name == 'test_agent'
    assert metadata.agent == 'test_agent_type'
    assert metadata.triggers == ['trigger1', 'trigger2']


def test_microagent_file_not_found():
    with pytest.raises(FileNotFoundError):
        MicroAgent('/nonexistent/path')


def test_microagent_load_and_properties():
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("""---
name: test_agent
agent: test_agent_type
triggers:
  - trigger1
  - trigger2
---
This is the content
""")
        f.flush()

        try:
            agent = MicroAgent(f.name)
            assert agent.name == 'test_agent'
            assert agent.agent == 'test_agent_type'
            assert agent.triggers == ['trigger1', 'trigger2']
            assert agent.content.strip() == 'This is the content'
            assert isinstance(agent.metadata, MicroAgentMetadata)
        finally:
            os.unlink(f.name)


def test_microagent_get_trigger():
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("""---
name: test_agent
agent: test_agent_type
triggers:
  - Hello World
  - Test Trigger
---
Content
""")
        f.flush()

        try:
            agent = MicroAgent(f.name)
            assert agent.get_trigger('hello world test') == 'Hello World'
            assert agent.get_trigger('TEST TRIGGER') == 'Test Trigger'
            assert agent.get_trigger('no match') is None
        finally:
            os.unlink(f.name)
