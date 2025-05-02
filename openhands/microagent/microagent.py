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
        cls,
        path: Union[str, Path],
        microagent_dir: Path | None = None,
        file_content: str | None = None,
    ) -> 'BaseMicroagent':
        """Load a microagent from a markdown file with frontmatter.

        The agent's name is derived from its path relative to the microagent_dir.
        """
        path = Path(path) if isinstance(path, str) else path

        # Calculate derived name from relative path if microagent_dir is provided
        # Otherwise, we will rely on the name from metadata later
        derived_name = None
        if microagent_dir is not None:
            derived_name = str(path.relative_to(microagent_dir).with_suffix(''))

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
        }

        # Infer the agent type:
        # 1. If triggers exist -> KNOWLEDGE
        # 2. Else (no triggers) -> REPO
        inferred_type: MicroagentType
        if metadata.triggers:
            inferred_type = MicroagentType.KNOWLEDGE
        else:
            # No triggers, default to REPO unless metadata explicitly says otherwise (which it shouldn't for REPO)
            # This handles cases where 'type' might be missing or defaulted by Pydantic
            inferred_type = MicroagentType.REPO_KNOWLEDGE

        if inferred_type not in subclass_map:
            # This should theoretically not happen with the logic above
            raise ValueError(f'Could not determine microagent type for: {path}')

        # Use derived_name if available (from relative path), otherwise fallback to metadata.name
        agent_name = derived_name if derived_name is not None else metadata.name

        agent_class = subclass_map[inferred_type]
        return agent_class(
            name=agent_name,
            content=content,
            metadata=metadata,
            source=str(path),
            type=inferred_type,
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
            raise ValueError(
                f'RepoMicroagent initialized with incorrect type: {self.type}'
            )


def load_microagents_from_dir(
    microagent_dir: Union[str, Path],
) -> tuple[dict[str, RepoMicroagent], dict[str, KnowledgeMicroagent]]:
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

    # Load all agents from microagents directory
    logger.debug(f'Loading agents from {microagent_dir}')
    if microagent_dir.exists():
        for file in microagent_dir.rglob('*.md'):
            logger.debug(f'Checking file {file}...')
            # skip README.md
            if file.name == 'README.md':
                continue
            try:
                agent = BaseMicroagent.load(file, microagent_dir)
                if isinstance(agent, RepoMicroagent):
                    repo_agents[agent.name] = agent
                elif isinstance(agent, KnowledgeMicroagent):
                    knowledge_agents[agent.name] = agent
                logger.debug(f'Loaded agent {agent.name} from {file}')
            except Exception as e:
                raise ValueError(f'Error loading agent from {file}: {e}')

    return repo_agents, knowledge_agents
