import io
from pathlib import Path
from typing import Union

import frontmatter
from pydantic import BaseModel

from openhands.core.exceptions import (
    MicroAgentValidationError,
)
from openhands.core.logger import openhands_logger as logger
from openhands.microagent.types import (
    MicroAgentMetadata,
    MicroAgentType,
    TaskProgress,
    TaskStep,
)


class BaseMicroAgent(BaseModel):
    """Base class for all microagents."""

    name: str
    content: str
    metadata: MicroAgentMetadata
    source: str  # path to the file
    type: MicroAgentType

    @classmethod
    def load(
        cls, path: Union[str, Path], file_content: str | None = None
    ) -> 'BaseMicroAgent':
        """Load a microagent from a markdown file with frontmatter."""
        path = Path(path) if isinstance(path, str) else path

        # Only load directly from path if file_content is not provided
        if file_content is None:
            with open(path) as f:
                file_content = f.read()

        # Legacy repo instructions are stored in .openhands_instructions
        if path.name == '.openhands_instructions':
            return RepoMicroAgent(
                name='repo_legacy',
                content=file_content,
                metadata=MicroAgentMetadata(name='repo_legacy'),
                source=str(path),
                type=MicroAgentType.REPO_KNOWLEDGE,
            )

        file_io = io.StringIO(file_content)
        loaded = frontmatter.load(file_io)
        content = loaded.content
        try:
            metadata = MicroAgentMetadata(**loaded.metadata)
        except Exception as e:
            raise MicroAgentValidationError(f'Error loading metadata: {e}') from e

        # Create appropriate subclass based on type
        subclass_map = {
            MicroAgentType.KNOWLEDGE: KnowledgeMicroAgent,
            MicroAgentType.REPO_KNOWLEDGE: RepoMicroAgent,
            MicroAgentType.TASK: TaskMicroAgent,
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


class KnowledgeMicroAgent(BaseMicroAgent):
    """Knowledge micro-agents provide specialized expertise that's triggered by keywords in conversations. They help with:
    - Language best practices
    - Framework guidelines
    - Common patterns
    - Tool usage
    """

    def __init__(self, **data):
        super().__init__(**data)
        if self.type != MicroAgentType.KNOWLEDGE:
            raise ValueError('KnowledgeMicroAgent must have type KNOWLEDGE')

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


class RepoMicroAgent(BaseMicroAgent):
    """MicroAgent specialized for repository-specific knowledge and guidelines.

    RepoMicroAgents are loaded from `.openhands/microagents/repo.md` files within repositories
    and contain private, repository-specific instructions that are automatically loaded when
    working with that repository. They are ideal for:
        - Repository-specific guidelines
        - Team practices and conventions
        - Project-specific workflows
        - Custom documentation references
    """

    def __init__(self, **data):
        super().__init__(**data)
        if self.type != MicroAgentType.REPO_KNOWLEDGE:
            raise ValueError('RepoMicroAgent must have type REPO_KNOWLEDGE')


class TaskMicroAgent(BaseMicroAgent):
    """MicroAgent specialized for task-based operations.

    TaskMicroAgents help track and manage tasks by:
    - Creating markdown files to track task progress
    - Managing task steps with checkboxes
    - Supporting task review and completion tracking
    """

    def __init__(self, **data):
        super().__init__(**data)
        if self.type != MicroAgentType.TASK:
            raise ValueError('TaskMicroAgent must have type TASK')
        self._progress = None

    def _write_progress_file(self, file_path: Path) -> None:
        """Write the current task progress to a markdown file.

        Args:
            file_path: Path to write the file to
        """
        if not self._progress:
            raise ValueError('No task progress being tracked')

        content = [
            f'# {self._progress.title}\n',
            f'{self._progress.description}\n',
            '## Task Steps\n',
        ]

        for i, step in enumerate(self._progress.steps, 1):
            checkbox = '- [x]' if step.completed else '- [ ]'
            content.append(f'{checkbox} {i}. {step.description}\n')

            for j, subtask in enumerate(step.subtasks, 1):
                sub_checkbox = '- [x]' if subtask.completed else '- [ ]'
                content.append(f'    {sub_checkbox} {i}.{j}. {subtask.description}\n')

        content.extend(
            [
                '\n## Review Notes\n',
                self._progress.review_notes or '_No review notes yet._\n',
                '\n## Status\n',
                f"Task Status: {'Completed' if self._progress.completed else 'In Progress'}\n",
            ]
        )

        with open(file_path, 'w') as f:
            f.write(''.join(content))

    def create_progress_file(
        self,
        title: str,
        description: str,
        steps: list[Union[str, dict[str, list[str]]]],
        output_dir: Path,
    ) -> Path:
        """Create a markdown file to track task progress.

        Args:
            title: Task title
            description: Task description
            steps: List of task steps to complete. Each step can be either:
                  - A string for a simple step
                  - A dict with a single key-value pair where:
                    - key is the main step description
                    - value is a list of subtask descriptions
            output_dir: Directory to save the progress file

        Returns:
            Path to the created progress file

        Example:
            steps = [
                "Simple step 1",
                {"Complex step 2": ["Subtask 2.1", "Subtask 2.2"]},
                "Simple step 3"
            ]
        """
        task_steps = []
        for step in steps:
            if isinstance(step, str):
                task_steps.append(TaskStep(description=step))
            elif isinstance(step, dict):
                if not step:  # Empty dict
                    raise ValueError(
                        'Each step must be either a string or a dict with subtasks'
                    )
                try:
                    main_step, subtasks = next(iter(step.items()))
                    if not isinstance(subtasks, list):
                        raise ValueError(
                            'Each step must be either a string or a dict with subtasks'
                        )
                    task_steps.append(
                        TaskStep(
                            description=main_step,
                            subtasks=[
                                TaskStep(description=subtask) for subtask in subtasks
                            ],
                        )
                    )
                except (StopIteration, TypeError, ValueError):
                    raise ValueError(
                        'Each step must be either a string or a dict with subtasks'
                    )
            else:
                raise ValueError(
                    'Each step must be either a string or a dict with subtasks'
                )

        self._progress = TaskProgress(
            title=title,
            description=description,
            steps=task_steps,
        )

        # Create output directory and file
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{title.lower().replace(' ', '_')}_progress.md"

        # Write initial content
        self._write_progress_file(output_file)
        return output_file

    def update_step_status(
        self,
        step_index: int,
        completed: bool,
        file_path: Path,
        subtask_index: int | None = None,
    ) -> None:
        """Update the completion status of a task step or subtask.

        Args:
            step_index: Index of the step to update (1-based)
            completed: Whether the step is completed
            file_path: Path to the progress file
            subtask_index: Optional index of the subtask to update (1-based).
                         If None, updates the main step status.
        """
        if not self._progress:
            raise ValueError(
                'No task progress being tracked. Create a progress file first.'
            )

        if not (1 <= step_index <= len(self._progress.steps)):
            raise ValueError(f'Invalid step index {step_index}')

        step = self._progress.steps[step_index - 1]

        if subtask_index is not None:
            if not step.subtasks:
                raise ValueError(f'Step {step_index} has no subtasks')
            if not (1 <= subtask_index <= len(step.subtasks)):
                raise ValueError(
                    f'Invalid subtask index {subtask_index} for step {step_index}'
                )
            step.subtasks[subtask_index - 1].completed = completed
        else:
            step.completed = completed

        # Write updated content
        self._write_progress_file(file_path)

    def add_review_notes(self, notes: str, file_path: Path) -> None:
        """Add review notes to the task progress.

        Args:
            notes: Review notes to add
            file_path: Path to the progress file
        """
        if not self._progress:
            raise ValueError(
                'No task progress being tracked. Create a progress file first.'
            )

        # Update review notes
        self._progress.review_notes = notes

        # Write updated content
        self._write_progress_file(file_path)

    def mark_completed(self, file_path: Path) -> None:
        """Mark the task as completed.

        Args:
            file_path: Path to the progress file
        """
        if not self._progress:
            raise ValueError(
                'No task progress being tracked. Create a progress file first.'
            )

        # Update completion status
        self._progress.completed = True

        # Write updated content
        self._write_progress_file(file_path)


def load_microagents_from_dir(
    microagent_dir: Union[str, Path],
) -> tuple[
    dict[str, RepoMicroAgent], dict[str, KnowledgeMicroAgent], dict[str, TaskMicroAgent]
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
                agent = BaseMicroAgent.load(file)
                if isinstance(agent, RepoMicroAgent):
                    repo_agents[agent.name] = agent
                elif isinstance(agent, KnowledgeMicroAgent):
                    knowledge_agents[agent.name] = agent
                elif isinstance(agent, TaskMicroAgent):
                    task_agents[agent.name] = agent
                logger.debug(f'Loaded agent {agent.name} from {file}')
            except Exception as e:
                raise ValueError(f'Error loading agent from {file}: {e}')

    return repo_agents, knowledge_agents, task_agents
