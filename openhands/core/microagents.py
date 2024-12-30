"""MicroAgent system for OpenHands."""

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml
from pydantic import BaseModel, Field, field_validator


def parse_markdown_with_frontmatter(content: str) -> Tuple[dict, str]:
    """Parse markdown file with YAML frontmatter.

    Format:
    ```
    ---
    key: value
    ---
    markdown content
    ```
    """
    pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(pattern, content, re.DOTALL)
    if not match:
        raise ValueError('Invalid markdown format. Expected YAML frontmatter.')

    frontmatter = yaml.safe_load(match.group(1))
    markdown = match.group(2).strip()
    return frontmatter, markdown


class TriggerType(str, Enum):
    """Type of trigger for knowledge-based agents."""

    REPOSITORY = 'repository'
    KEYWORD = 'keyword'


class TaskType(str, Enum):
    """Type of task-based agent."""

    WORKFLOW = 'workflow'
    SNIPPET = 'snippet'
    GUIDE = 'guide'


class InputValidation(BaseModel):
    """Validation rules for task inputs."""

    pattern: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None


class TaskInput(BaseModel):
    """Input parameter for task-based agents."""

    name: str
    description: str
    type: str
    required: bool = True
    default: Optional[Any] = None
    validation: Optional[InputValidation] = None


class MicroAgent(BaseModel):
    """Base class for all microagents."""

    name: str
    version: str = Field(default='1.0.0')  # Default for legacy support
    author: str = Field(default='openhands')  # Default for legacy support
    agent: str = Field(default='CodeActAgent')  # Default for legacy support
    category: str = Field(default='development')  # Default for legacy support
    tags: List[str] = Field(default_factory=list)
    requires: List[str] = Field(default_factory=list)
    legacy: bool = Field(default=False, exclude=True)  # Internal field for validation

    model_config = {
        'validate_assignment': True,
        'validate_default': True,
        'extra': 'allow',  # Allow extra fields like 'legacy'
    }

    @classmethod
    def from_markdown(cls, path: Union[str, Path]) -> 'MicroAgent':
        """Load a microagent from a markdown file with frontmatter."""
        with open(path) as f:
            content = f.read()

        frontmatter, markdown = parse_markdown_with_frontmatter(content)

        # Determine agent type from frontmatter
        if 'trigger_type' in frontmatter:
            return KnowledgeAgent(content=markdown, **frontmatter)
        elif 'task_type' in frontmatter:
            return TaskAgent(content=markdown, **frontmatter)
        else:
            # Legacy format - infer from content/structure
            if any(key in frontmatter for key in ['inputs', 'variables']):
                frontmatter['task_type'] = 'workflow'
                return TaskAgent(content=markdown, **frontmatter)
            else:
                return KnowledgeAgent.from_legacy(content=markdown, **frontmatter)


class KnowledgeAgent(MicroAgent):
    """Knowledge-based microagent with repository or keyword triggers."""

    trigger_type: TriggerType = Field(default=TriggerType.KEYWORD)
    trigger_pattern: Optional[str] = Field(None, description='For repository triggers')
    triggers: Optional[List[str]] = Field(None, description='For keyword triggers')
    priority: Optional[int] = Field(None, description='For repository triggers')
    file_patterns: Optional[List[str]] = None
    content: str  # The markdown content

    @field_validator('trigger_pattern', mode='before')
    @classmethod
    def validate_repo_trigger(cls, v: Optional[str], info):
        """Validate repository trigger pattern."""
        trigger_type = info.data.get('trigger_type')
        if trigger_type == TriggerType.REPOSITORY and not v:
            raise ValueError('trigger_pattern is required for repository triggers')
        return v

    @field_validator('triggers', mode='before')
    @classmethod
    def validate_keyword_trigger(cls, v: Optional[List[str]], info):
        """Validate keyword triggers."""
        trigger_type = info.data.get('trigger_type')
        if trigger_type == TriggerType.KEYWORD and not v:
            # For legacy support, don't validate triggers for legacy agents
            if not info.data.get('legacy', False):
                raise ValueError('triggers is required for keyword triggers')
        return v

    @classmethod
    def from_legacy(cls, content: str, **kwargs):
        """Create a KnowledgeAgent from legacy format."""
        kwargs['trigger_type'] = TriggerType.KEYWORD
        kwargs['triggers'] = None  # None for legacy agents
        kwargs['legacy'] = True  # Mark as legacy agent
        return cls(content=content, **kwargs)


class TaskAgent(MicroAgent):
    """Task-based microagent with user inputs."""

    task_type: TaskType
    inputs: List[TaskInput]
    content: str  # The markdown content


@dataclass
class MicroAgentHub:
    """Central hub for managing microagents."""

    root_dir: Path
    repo_agents: Dict[str, KnowledgeAgent]
    keyword_agents: Dict[str, KnowledgeAgent]
    task_agents: Dict[str, TaskAgent]

    @classmethod
    def load(cls, root_dir: Optional[Union[str, Path]] = None) -> 'MicroAgentHub':
        """Load all microagents from the given directory."""
        # Default to the package's microagents directory
        root_dir = (
            Path(__file__).parent.parent.parent / 'microagents'
            if root_dir is None
            else Path(root_dir)
        )

        repo_agents = {}
        keyword_agents = {}
        task_agents = {}

        # Load knowledge agents
        knowledge_dir = root_dir / 'knowledge'
        if knowledge_dir.exists():
            for file in knowledge_dir.glob('*.md'):
                agent = MicroAgent.from_markdown(file)
                if not isinstance(agent, KnowledgeAgent):
                    continue

                if agent.trigger_type == TriggerType.REPOSITORY:
                    repo_agents[agent.name] = agent
                else:
                    keyword_agents[agent.name] = agent

        # Load task agents
        tasks_dir = root_dir / 'tasks'
        if tasks_dir.exists():
            for file in tasks_dir.glob('*.md'):
                agent = MicroAgent.from_markdown(file)
                if isinstance(agent, TaskAgent):
                    task_agents[agent.name] = agent

        return cls(
            root_dir=root_dir,
            repo_agents=repo_agents,
            keyword_agents=keyword_agents,
            task_agents=task_agents,
        )

    def get_repo_agents(self, repo_name: str) -> List[KnowledgeAgent]:
        """Get all repository agents that match the given repository name."""
        matching_agents = []
        for agent in self.repo_agents.values():
            # TODO: Implement proper glob pattern matching
            if agent.trigger_pattern and repo_name.startswith(
                agent.trigger_pattern.replace('*', '')
            ):
                matching_agents.append(agent)

        # Sort by priority (higher first)
        matching_agents.sort(key=lambda x: x.priority or 0, reverse=True)
        return matching_agents

    def get_keyword_agents(
        self, text: str, file_path: Optional[str] = None
    ) -> List[KnowledgeAgent]:
        """Get all keyword agents whose triggers match in the given text."""
        matching_agents = []
        for agent in self.keyword_agents.values():
            if not agent.triggers:
                continue

            # Check if any trigger word is present
            if any(trigger.lower() in text.lower() for trigger in agent.triggers):
                # Check file pattern if specified
                if agent.file_patterns and file_path:
                    # TODO: Implement proper glob pattern matching
                    if not any(
                        file_path.endswith(pattern.replace('*', ''))
                        for pattern in agent.file_patterns
                    ):
                        continue
                matching_agents.append(agent)

        return matching_agents

    def get_task_agent(self, name: str) -> Optional[TaskAgent]:
        """Get a task agent by name."""
        return self.task_agents.get(name)

    def list_task_agents(self, task_type: Optional[TaskType] = None) -> List[TaskAgent]:
        """List all task agents, optionally filtered by type."""
        if task_type is None:
            return list(self.task_agents.values())
        return [
            agent for agent in self.task_agents.values() if agent.task_type == task_type
        ]

    def process_task(self, task_name: str, inputs: Dict[str, Any]) -> Optional[str]:
        """Process a task with the given inputs."""
        agent = self.get_task_agent(task_name)
        if not agent:
            return None

        # Prepare template variables with defaults
        template_vars = {}
        for input_def in agent.inputs:
            if input_def.required and input_def.name not in inputs:
                raise ValueError(f'Missing required input: {input_def.name}')

            # Get value from inputs or use default
            value = inputs.get(input_def.name, input_def.default)
            template_vars[input_def.name] = value

            # Apply validation if specified
            if value is not None and input_def.validation:
                if input_def.validation.pattern:
                    if not re.match(input_def.validation.pattern, str(value)):
                        raise ValueError(
                            f'Input {input_def.name} does not match pattern: {input_def.validation.pattern}'
                        )
                if (
                    input_def.validation.min is not None
                    and value < input_def.validation.min
                ):
                    raise ValueError(
                        f'Input {input_def.name} must be >= {input_def.validation.min}'
                    )
                if (
                    input_def.validation.max is not None
                    and value > input_def.validation.max
                ):
                    raise ValueError(
                        f'Input {input_def.name} must be <= {input_def.validation.max}'
                    )

        # Process content
        result = agent.content
        for name, value in template_vars.items():
            if value is not None:  # Only replace if value is not None
                result = result.replace(f'${{{name}}}', str(value))

        return result
