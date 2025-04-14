import io
from pathlib import Path
from typing import Union

import frontmatter
from pydantic import BaseModel

from openhands.core.exceptions import (
    MicroagentValidationError,
)
from openhands.core.logger import openhands_logger as logger
from openhands.microagent.types import MicroagentMetadata, MicroagentType


class BaseMicroagent(BaseModel):
    """Base class for all microagents."""

    name: str
    content: str
    metadata: MicroagentMetadata
    source: str  # path to the file
    type: MicroagentType

    @classmethod
    def load(
        cls, path: Union[str, Path], file_content: str | None = None
    ) -> 'BaseMicroagent':
        """Load a microagent from a markdown file with frontmatter."""
        path = Path(path) if isinstance(path, str) else path

        # Only load directly from path if file_content is not provided
        if file_content is None:
            with open(path) as f:
                file_content = f.read()

        # Legacy repo instructions are stored in .openhands_instructions
        if path.name == '.openhands_instructions':
            return RepoMicroagent(
                name='repo_legacy',
                content=file_content,
                metadata=MicroagentMetadata(name='repo_legacy'),
                source=str(path),
                type=MicroagentType.REPO_KNOWLEDGE,
            )

        file_io = io.StringIO(file_content)
        loaded = frontmatter.load(file_io)
        content = loaded.content

        # Handle case where there's no frontmatter or empty frontmatter
        metadata_dict = loaded.metadata or {}

        try:
            metadata = MicroagentMetadata(**metadata_dict)
        except Exception as e:
            raise MicroagentValidationError(f'Error loading metadata: {e}') from e

        # Create appropriate subclass based on type
        subclass_map = {
            MicroagentType.KNOWLEDGE: KnowledgeMicroagent,
            MicroagentType.REPO_KNOWLEDGE: RepoMicroagent,
            MicroagentType.TASK: TaskMicroagent,
        }
        if metadata.type not in subclass_map:
            raise ValueError(f'Unknown microagent type: {metadata.type}')

        agent_class = subclass_map[metadata.type]
        return agent_class(
            name=metadata.name,
            content=content,
            metadata=metadata,
            source=str(path),
            type=metadata.type,
        )


class KnowledgeMicroagent(BaseMicroagent):
    """Knowledge micro-agents provide specialized expertise that's triggered by keywords in conversations. They help with:
    - Language best practices
    - Framework guidelines
    - Common patterns
    - Tool usage
    """

    def __init__(self, **data):
        super().__init__(**data)
        if self.type != MicroagentType.KNOWLEDGE:
            raise ValueError('KnowledgeMicroagent must have type KNOWLEDGE')

    def match_trigger(self, message: str) -> str | None:
        """Match a trigger in the message.

        It returns the first trigger that matches the message.
        """
        message = message.lower()
        for trigger in self.triggers:
            if trigger.lower() in message:
                return trigger
        return None

    @property
    def triggers(self) -> list[str]:
        return self.metadata.triggers


class RepoMicroagent(BaseMicroagent):
    """Microagent specialized for repository-specific knowledge and guidelines.

    RepoMicroagents are loaded from `.openhands/microagents/repo.md` files within repositories
    and contain private, repository-specific instructions that are automatically loaded when
    working with that repository. They are ideal for:
        - Repository-specific guidelines
        - Team practices and conventions
        - Project-specific workflows
        - Custom documentation references
    """

    def __init__(self, **data):
        super().__init__(**data)
        if self.type != MicroagentType.REPO_KNOWLEDGE:
            raise ValueError('RepoMicroagent must have type REPO_KNOWLEDGE')


class TaskMicroagent(BaseMicroagent):
    """Microagent specialized for task-based operations."""

    def __init__(self, **data):
        super().__init__(**data)
        if self.type != MicroagentType.TASK:
            raise ValueError('TaskMicroagent must have type TASK')


def load_microagents_from_dir(
    microagent_dir: Union[str, Path],
) -> tuple[
    dict[str, RepoMicroagent], dict[str, KnowledgeMicroagent], dict[str, TaskMicroagent]
]:
    """Load all microagents from the given directory.

    Note, legacy repo instructions will not be loaded here.

    Args:
        microagent_dir: Path to the microagents directory (e.g. .openhands/microagents)

    Returns:
        Tuple of (repo_agents, knowledge_agents, task_agents) dictionaries
    """
    if isinstance(microagent_dir, str):
        microagent_dir = Path(microagent_dir)

    repo_agents = {}
    knowledge_agents = {}
    task_agents = {}

    # Load all agents from .openhands/microagents directory
    logger.debug(f'Loading agents from {microagent_dir}')
    if microagent_dir.exists():
        for file in microagent_dir.rglob('*.md'):
            logger.debug(f'Checking file {file}...')
            # skip README.md
            if file.name == 'README.md':
                continue
            try:
                agent = BaseMicroagent.load(file)
                if isinstance(agent, RepoMicroagent):
                    repo_agents[agent.name] = agent
                elif isinstance(agent, KnowledgeMicroagent):
                    knowledge_agents[agent.name] = agent
                elif isinstance(agent, TaskMicroagent):
                    task_agents[agent.name] = agent
                logger.debug(f'Loaded agent {agent.name} from {file}')
            except Exception as e:
                raise ValueError(f'Error loading agent from {file}: {e}')

    return repo_agents, knowledge_agents, task_agents
