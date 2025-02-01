# OpenHands MicroAgent System Guide

This guide explains OpenHands' microagent system, which provides a flexible way to create specialized agents for different purposes.

## Table of Contents
1. [MicroAgent System Overview](#microagent-system-overview)
2. [Types of MicroAgents](#types-of-microagents)
3. [Creating MicroAgents](#creating-microagents)
4. [Implementation Examples](#implementation-examples)
5. [Best Practices](#best-practices)

## MicroAgent System Overview

The microagent system in OpenHands is built around the concept of specialized agents that can handle specific tasks or provide domain knowledge.

### Core Components

1. **MicroAgent Types**
```python
class MicroAgentType(str, Enum):
    KNOWLEDGE = 'knowledge'     # For specialized expertise
    REPO_KNOWLEDGE = 'repo'     # For repository-specific knowledge
    TASK = 'task'              # For task-based operations
```

2. **MicroAgent Metadata**
```python
class MicroAgentMetadata(BaseModel):
    name: str = 'default'
    type: MicroAgentType = Field(default=MicroAgentType.KNOWLEDGE)
    version: str = Field(default='1.0.0')
    agent: str = Field(default='CodeActAgent')
    triggers: list[str] = []  # For knowledge microagents
```

## Types of MicroAgents

### 1. Knowledge MicroAgents
Knowledge agents provide specialized expertise triggered by keywords:
```python
class KnowledgeMicroAgent(BaseMicroAgent):
    """Provides specialized expertise like:
    - Language best practices
    - Framework guidelines
    - Common patterns
    - Tool usage
    """
    def match_trigger(self, message: str) -> str | None:
        """Match triggers in the message"""
        message = message.lower()
        for trigger in self.triggers:
            if trigger.lower() in message:
                return trigger
        return None
```

### 2. Repository MicroAgents
Repository agents handle repository-specific knowledge:
```python
class RepoMicroAgent(BaseMicroAgent):
    """Handles repository-specific:
    - Guidelines
    - Team practices
    - Project workflows
    - Documentation references
    """
```

### 3. Task MicroAgents
Task agents handle specific operations:
```python
class TaskMicroAgent(BaseMicroAgent):
    """Handles task-based operations with:
    - Defined inputs
    - Specific workflows
    - Task-specific logic
    """
```

## Creating MicroAgents

### 1. Basic Structure
MicroAgents are created using markdown files with frontmatter:

```markdown
---
name: "python_best_practices"
type: "knowledge"
version: "1.0.0"
agent: "CodeActAgent"
triggers: ["python style", "pep8", "python guidelines"]
---

# Python Best Practices Guide

This guide covers Python coding standards and best practices:

1. Code Style
   - Follow PEP 8 guidelines
   - Use meaningful variable names
   - Keep functions focused and small

2. Documentation
   - Use docstrings for all public APIs
   - Include examples in docstrings
   - Keep comments up to date
```

### 2. Loading MicroAgents

```python
def load_microagents(directory: Path):
    """Load all microagents from a directory"""
    repo_agents, knowledge_agents, task_agents = {}, {}, {}
    
    for file in directory.rglob('*.md'):
        if file.name == 'README.md':
            continue
            
        try:
            agent = BaseMicroAgent.load(file)
            if isinstance(agent, RepoMicroAgent):
                repo_agents[agent.name] = agent
            elif isinstance(agent, KnowledgeMicroAgent):
                knowledge_agents[agent.name] = agent
            elif isinstance(agent, TaskMicroAgent):
                task_agents[agent.name] = agent
        except Exception as e:
            logger.error(f"Error loading agent from {file}: {e}")
    
    return repo_agents, knowledge_agents, task_agents
```

## Implementation Examples

### 1. Knowledge MicroAgent Example

```markdown
---
name: "git_workflow"
type: "knowledge"
version: "1.0.0"
agent: "CodeActAgent"
triggers: ["git workflow", "git branching", "git commit"]
---

# Git Workflow Guidelines

## Branching Strategy
- Use feature branches for new features
- Use hotfix branches for urgent fixes
- Always branch from main/master

## Commit Guidelines
- Write clear commit messages
- Use conventional commits format
- Keep commits focused and atomic

## Code Review Process
1. Create pull request
2. Request reviews
3. Address feedback
4. Merge when approved
```

### 2. Repository MicroAgent Example

```markdown
---
name: "project_guidelines"
type: "repo"
version: "1.0.0"
agent: "CodeActAgent"
---

# Project Guidelines

## Code Organization
- Source code in /src
- Tests in /tests
- Documentation in /docs

## Development Workflow
1. Setup development environment
   ```bash
   make setup-dev
   ```

2. Run tests
   ```bash
   make test
   ```

3. Build project
   ```bash
   make build
   ```

## Deployment Process
- Staging deployment on PR merge
- Production deployment on release tag
```

### 3. Task MicroAgent Example

```markdown
---
name: "code_review"
type: "task"
version: "1.0.0"
agent: "CodeActAgent"
---

# Code Review Task

## Review Process
1. Check code style
2. Verify test coverage
3. Review documentation
4. Check performance impact

## Review Checklist
- [ ] Code follows style guide
- [ ] Tests are comprehensive
- [ ] Documentation is updated
- [ ] No security issues
```

## Implementation Examples

### 1. Custom Knowledge Agent

```python
from openhands.microagent import KnowledgeMicroAgent
from openhands.microagent.types import MicroAgentMetadata, MicroAgentType

class PythonStyleAgent(KnowledgeMicroAgent):
    def __init__(self):
        super().__init__(
            name="python_style",
            content="""
            # Python Style Guide
            
            ## Naming Conventions
            - Use snake_case for functions and variables
            - Use PascalCase for classes
            - Use UPPERCASE for constants
            
            ## Code Layout
            - 4 spaces for indentation
            - Maximum line length: 88 characters
            - Two blank lines between top-level functions/classes
            """,
            metadata=MicroAgentMetadata(
                name="python_style",
                type=MicroAgentType.KNOWLEDGE,
                triggers=["python style", "pep8", "naming"]
            ),
            source="internal",
            type=MicroAgentType.KNOWLEDGE
        )
    
    def get_style_recommendation(self, code: str) -> str:
        """Analyze code and provide style recommendations"""
        recommendations = []
        
        # Check naming conventions
        if any(c.isupper() for c in code.split()):
            recommendations.append(
                "Use snake_case for function and variable names"
            )
        
        # Check line length
        if any(len(line) > 88 for line in code.splitlines()):
            recommendations.append(
                "Keep lines under 88 characters"
            )
        
        return "\n".join(recommendations)
```

### 2. Custom Repository Agent

```python
class ProjectSetupAgent(RepoMicroAgent):
    def __init__(self):
        super().__init__(
            name="project_setup",
            content="""
            # Project Setup Guide
            
            ## Development Environment
            1. Install dependencies:
               ```bash
               poetry install
               ```
            
            2. Setup pre-commit hooks:
               ```bash
               poetry run pre-commit install
               ```
            
            3. Configure environment:
               ```bash
               cp .env.example .env
               ```
            """,
            metadata=MicroAgentMetadata(
                name="project_setup",
                type=MicroAgentType.REPO_KNOWLEDGE
            ),
            source="internal",
            type=MicroAgentType.REPO_KNOWLEDGE
        )
    
    def get_setup_instructions(self, os_type: str) -> str:
        """Get OS-specific setup instructions"""
        if os_type.lower() == "windows":
            return """
            Windows Setup:
            1. Install WSL2
            2. Install Python 3.12
            3. Install Poetry
            4. Follow project setup
            """
        elif os_type.lower() == "linux":
            return """
            Linux Setup:
            1. Install Python 3.12
            2. Install Poetry
            3. Follow project setup
            """
        else:
            return "Unsupported OS"
```

### 3. Custom Task Agent

```python
class CodeReviewAgent(TaskMicroAgent):
    def __init__(self):
        super().__init__(
            name="code_review",
            content="""
            # Code Review Process
            
            ## Review Steps
            1. Code Quality Check
            2. Test Coverage Analysis
            3. Documentation Review
            4. Security Assessment
            
            ## Outputs
            - Review report
            - Action items
            - Approval status
            """,
            metadata=MicroAgentMetadata(
                name="code_review",
                type=MicroAgentType.TASK
            ),
            source="internal",
            type=MicroAgentType.TASK
        )
    
    async def review_code(self, code: str) -> dict:
        """Perform code review"""
        return {
            "quality": self._check_code_quality(code),
            "security": self._check_security(code),
            "documentation": self._check_documentation(code),
            "approval": self._get_approval_status()
        }
    
    def _check_code_quality(self, code: str) -> dict:
        # Implement code quality checks
        return {"status": "passed", "issues": []}
    
    def _check_security(self, code: str) -> dict:
        # Implement security checks
        return {"status": "passed", "vulnerabilities": []}
    
    def _check_documentation(self, code: str) -> dict:
        # Check documentation coverage
        return {"status": "passed", "missing_docs": []}
    
    def _get_approval_status(self) -> str:
        return "approved"
```

## Best Practices

### 1. MicroAgent Design

1. **Single Responsibility**
```python
class FocusedAgent(KnowledgeMicroAgent):
    """Agent focused on one specific task/domain"""
    def __init__(self):
        super().__init__(
            name="focused_agent",
            content="Specific domain knowledge",
            metadata=MicroAgentMetadata(
                name="focused_agent",
                type=MicroAgentType.KNOWLEDGE,
                triggers=["specific_topic"]
            )
        )
```

2. **Clear Documentation**
```python
class WellDocumentedAgent(TaskMicroAgent):
    """
    Agent with clear documentation and examples
    
    Attributes:
        name: Agent identifier
        content: Task instructions
        metadata: Agent configuration
    
    Examples:
        >>> agent = WellDocumentedAgent()
        >>> result = agent.process_task({"input": "data"})
    """
```

3. **Error Handling**
```python
class ResilientAgent(BaseMicroAgent):
    def process_safely(self, input_data: dict) -> dict:
        try:
            return self._process(input_data)
        except ValueError as e:
            logger.error(f"Invalid input: {e}")
            return {"error": "Invalid input", "details": str(e)}
        except Exception as e:
            logger.error(f"Processing error: {e}")
            return {"error": "Processing failed", "details": str(e)}
```

### 2. Testing MicroAgents

1. **Unit Tests**
```python
import pytest
from openhands.microagent import KnowledgeMicroAgent

def test_knowledge_agent():
    agent = KnowledgeMicroAgent(
        name="test_agent",
        content="Test content",
        metadata=MicroAgentMetadata(
            name="test_agent",
            triggers=["test"]
        )
    )
    
    # Test trigger matching
    assert agent.match_trigger("test message") == "test"
    assert agent.match_trigger("unrelated") is None
```

2. **Integration Tests**
```python
@pytest.mark.asyncio
async def test_agent_workflow():
    # Setup
    agent = TaskMicroAgent(...)
    event_stream = EventStream(...)
    
    # Test workflow
    result = await agent.process_task(
        {"input": "test_data"},
        event_stream
    )
    
    assert result["status"] == "success"
    assert "output" in result
```

### 3. Performance Considerations

1. **Resource Management**
```python
class EfficientAgent(BaseMicroAgent):
    def __init__(self):
        super().__init__()
        self.cache = {}
        self.max_cache_size = 1000
    
    def process_with_cache(self, input_data: str) -> str:
        if input_data in self.cache:
            return self.cache[input_data]
        
        result = self._process(input_data)
        
        # Manage cache size
        if len(self.cache) >= self.max_cache_size:
            self.cache.pop(next(iter(self.cache)))
        
        self.cache[input_data] = result
        return result
```

2. **Async Operations**
```python
class AsyncAgent(BaseMicroAgent):
    async def process_batch(
        self,
        items: list[dict]
    ) -> list[dict]:
        """Process multiple items concurrently"""
        tasks = [
            self._process_item(item)
            for item in items
        ]
        return await asyncio.gather(*tasks)
    
    async def _process_item(self, item: dict) -> dict:
        # Process individual item
        return {"result": "processed"}
```

Remember to:
- Keep agents focused and single-purpose
- Provide clear documentation
- Implement proper error handling
- Write comprehensive tests
- Consider performance implications
- Use appropriate caching strategies