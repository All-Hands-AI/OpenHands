import tempfile

from openhands.microagent.microagent import (
    BaseMicroagent,
    KnowledgeMicroagent,
    TaskMicroagent,
)
from openhands.microagent.types import MicroagentType


def test_task_microagent_creation():
    """Test that a TaskMicroagent is created correctly."""
    content = """---
name: test_task
version: 1.0.0
author: openhands
agent: CodeActAgent
triggers:
- /test_task
inputs:
  - name: TEST_VAR
    description: "Test variable"
---

This is a test task microagent with a variable: ${test_var}.
"""

    with tempfile.NamedTemporaryFile(suffix='.md') as f:
        f.write(content.encode())
        f.flush()

        agent = BaseMicroagent.load(f.name)

        assert isinstance(agent, TaskMicroagent)
        assert agent.type == MicroagentType.TASK
        assert agent.name == 'test_task'
        assert '/test_task' in agent.triggers
        assert "If the user didn't provide any of these variables" in agent.content


def test_task_microagent_variable_extraction():
    """Test that variables are correctly extracted from the content."""
    content = """---
name: test_task
version: 1.0.0
author: openhands
agent: CodeActAgent
triggers:
- /test_task
inputs:
  - name: var1
    description: "Variable 1"
---

This is a test with variables: ${var1}, ${var2}, and ${var3}.
"""

    with tempfile.NamedTemporaryFile(suffix='.md') as f:
        f.write(content.encode())
        f.flush()

        agent = BaseMicroagent.load(f.name)

        assert isinstance(agent, TaskMicroagent)
        variables = agent.extract_variables(agent.content)
        assert set(variables) == {'var1', 'var2', 'var3'}
        assert agent.requires_user_input()


def test_knowledge_microagent_no_prompt():
    """Test that a regular KnowledgeMicroagent doesn't get the prompt."""
    content = """---
name: test_knowledge
version: 1.0.0
author: openhands
agent: CodeActAgent
triggers:
- test_knowledge
---

This is a test knowledge microagent.
"""

    with tempfile.NamedTemporaryFile(suffix='.md') as f:
        f.write(content.encode())
        f.flush()

        agent = BaseMicroagent.load(f.name)

        assert isinstance(agent, KnowledgeMicroagent)
        assert agent.type == MicroagentType.KNOWLEDGE
        assert "If the user didn't provide any of these variables" not in agent.content


def test_task_microagent_trigger_addition():
    """Test that a trigger is added if not present."""
    content = """---
name: test_task
version: 1.0.0
author: openhands
agent: CodeActAgent
inputs:
  - name: TEST_VAR
    description: "Test variable"
---

This is a test task microagent.
"""

    with tempfile.NamedTemporaryFile(suffix='.md') as f:
        f.write(content.encode())
        f.flush()

        agent = BaseMicroagent.load(f.name)

        assert isinstance(agent, TaskMicroagent)
        assert '/test_task' in agent.triggers


def test_task_microagent_no_duplicate_trigger():
    """Test that a trigger is not duplicated if already present."""
    content = """---
name: test_task
version: 1.0.0
author: openhands
agent: CodeActAgent
triggers:
- /test_task
- another_trigger
inputs:
  - name: TEST_VAR
    description: "Test variable"
---

This is a test task microagent.
"""

    with tempfile.NamedTemporaryFile(suffix='.md') as f:
        f.write(content.encode())
        f.flush()

        agent = BaseMicroagent.load(f.name)

        assert isinstance(agent, TaskMicroagent)
        assert agent.triggers.count('/test_task') == 1  # No duplicates
        assert len(agent.triggers) == 2


def test_task_microagent_match_trigger():
    """Test that a task microagent matches its trigger correctly."""
    content = """---
name: test_task
version: 1.0.0
author: openhands
agent: CodeActAgent
triggers:
- /test_task
inputs:
  - name: TEST_VAR
    description: "Test variable"
---

This is a test task microagent.
"""

    with tempfile.NamedTemporaryFile(suffix='.md') as f:
        f.write(content.encode())
        f.flush()

        agent = BaseMicroagent.load(f.name)

        assert isinstance(agent, TaskMicroagent)
        assert agent.match_trigger('/test_task') == '/test_task'
        assert (
            agent.match_trigger('  /test_task  ') == '/test_task'
        )  # Whitespace is trimmed
        assert (
            agent.match_trigger('This contains /test_task') is None
        )  # Not an exact match
        assert agent.match_trigger('/other_task') is None
