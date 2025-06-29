import os
import sys
from collections import deque
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from litellm import ChatCompletionToolParam

    from openhands.events.action import Action

from openhands.agenthub.codeact_agent.tools.bash import create_cmd_run_tool
from openhands.agenthub.codeact_agent.tools.browser import BrowserTool
from openhands.agenthub.codeact_agent.tools.condensation_request import (
    CondensationRequestTool,
)
from openhands.agenthub.codeact_agent.tools.finish import FinishTool
from openhands.agenthub.codeact_agent.tools.ipython import IPythonTool
from openhands.agenthub.codeact_agent.tools.llm_based_edit import LLMBasedFileEditTool
from openhands.agenthub.codeact_agent.tools.str_replace_editor import (
    create_str_replace_editor_tool,
)
from openhands.agenthub.codeact_agent.tools.think import ThinkTool

# Import automation tools locally to avoid circular imports
try:
    from .tools.content_creation import ContentCreationTool
    from .tools.research import ResearchTool
    from .tools.task_planner import TaskPlannerTool
    from .tools.verification import VerificationTool
    from .tools.workflow_orchestrator import WorkflowOrchestratorTool
except ImportError:
    # Fallback if tools are not available
    ResearchTool = None
    ContentCreationTool = None
    TaskPlannerTool = None
    WorkflowOrchestratorTool = None
    VerificationTool = None
from openhands.controller.agent import Agent
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.action import AgentFinishAction, MessageAction
from openhands.llm.llm import LLM
from openhands.memory.condenser import Condenser
from openhands.memory.conversation_memory import ConversationMemory
from openhands.runtime.plugins import (
    AgentSkillsRequirement,
    JupyterRequirement,
    PluginRequirement,
)
from openhands.utils.prompt import PromptManager


class TaskType(Enum):
    """Types of tasks the automation agent can handle."""

    RESEARCH = 'research'
    CONTENT_CREATION = 'content_creation'
    SOFTWARE_DEVELOPMENT = 'software_development'
    DATA_ANALYSIS = 'data_analysis'
    AUTOMATION = 'automation'
    WORKFLOW = 'workflow'
    MIXED = 'mixed'


class TaskStatus(Enum):
    """Status of a task."""

    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    FAILED = 'failed'
    PAUSED = 'paused'


class Task:
    """Represents a task with its metadata and status."""

    def __init__(
        self,
        task_id: str,
        description: str,
        task_type: TaskType,
        priority: int = 1,
        dependencies: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        self.task_id = task_id
        self.description = description
        self.task_type = task_type
        self.priority = priority
        self.dependencies = dependencies or []
        self.metadata = metadata or {}
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.subtasks: list['Task'] = []

    def to_dict(self) -> dict[str, Any]:
        """Convert task to dictionary representation."""
        return {
            'task_id': self.task_id,
            'description': self.description,
            'task_type': self.task_type.value,
            'priority': self.priority,
            'dependencies': self.dependencies,
            'metadata': self.metadata,
            'status': self.status.value,
            'result': self.result,
            'error': self.error,
            'subtasks': [subtask.to_dict() for subtask in self.subtasks],
        }


class AutomationAgent(Agent):
    VERSION = '1.0'
    """
    The Automation Agent is a comprehensive AI agent designed for full task automation.

    This agent combines multiple specialized capabilities to handle complex, multi-step tasks
    similar to Manus.im, including:

    1. **Research**: Gather and analyze information from multiple sources
    2. **Content Creation**: Generate reports, documents, and presentations
    3. **Software Development**: Write, test, and deploy code
    4. **Data Analysis**: Process and visualize data
    5. **Workflow Automation**: Orchestrate complex multi-step processes
    6. **Task Planning**: Break down complex tasks into manageable subtasks
    7. **Verification**: Validate results and iterate on improvements

    ### Key Features:

    - **Autonomous Operation**: Can work independently with minimal human intervention
    - **Multi-Agent Coordination**: Orchestrates multiple specialized agents
    - **Task Planning**: Automatically breaks down complex tasks
    - **Context Awareness**: Maintains context across long-running tasks
    - **Result Verification**: Validates outputs and iterates for improvement
    - **Integration Hub**: Connects with external tools and APIs

    ### Architecture:

    The agent uses a hierarchical task management system where complex tasks are broken
    down into subtasks, each handled by specialized tools or sub-agents. The main agent
    acts as an orchestrator, coordinating the execution and ensuring quality results.
    """

    sandbox_plugins: list[PluginRequirement] = [
        AgentSkillsRequirement(),
        JupyterRequirement(),
    ]

    def __init__(
        self,
        llm: LLM,
        config: AgentConfig,
    ) -> None:
        """Initializes a new instance of the AutomationAgent class.

        Parameters:
        - llm (LLM): The llm to be used by this agent
        - config (AgentConfig): The configuration for this agent
        """
        # Initialize task management first
        self.tasks: dict[str, Task] = {}
        self.current_task: Optional[Task] = None
        self.task_counter = 0

        # Autonomous mode settings (using extended config)
        extended_config = (
            config.extended.model_dump() if hasattr(config, 'extended') else {}
        )
        self.autonomous_mode = extended_config.get('autonomous_mode', False)
        self.max_iterations = extended_config.get('max_iterations', 50)
        self.current_iteration = 0

        super().__init__(llm, config)
        self.pending_actions: deque['Action'] = deque()
        self.reset()
        self.tools = self._get_tools()

        # Create a ConversationMemory instance
        self.conversation_memory = ConversationMemory(self.config, self.prompt_manager)

        self.condenser = Condenser.from_config(self.config.condenser)
        logger.debug(f'Using condenser: {type(self.condenser)}')

    @property
    def prompt_manager(self) -> PromptManager:
        if self._prompt_manager is None:
            self._prompt_manager = PromptManager(
                prompt_dir=os.path.join(os.path.dirname(__file__), 'prompts'),
                system_prompt_filename=self.config.system_prompt_filename,
            )

        return self._prompt_manager

    def _get_tools(self) -> list['ChatCompletionToolParam']:
        """Get all available tools for the automation agent."""
        # For these models, we use short tool descriptions ( < 1024 tokens)
        # to avoid hitting the OpenAI token limit for tool descriptions.
        SHORT_TOOL_DESCRIPTION_LLM_SUBSTRS = ['gpt-', 'o3', 'o1', 'o4']

        use_short_tool_desc = False
        if self.llm is not None:
            use_short_tool_desc = any(
                model_substr in self.llm.config.model
                for model_substr in SHORT_TOOL_DESCRIPTION_LLM_SUBSTRS
            )

        tools = []

        # Core tools from CodeAct agent
        if self.config.enable_cmd:
            tools.append(create_cmd_run_tool(use_short_description=use_short_tool_desc))
        if self.config.enable_think:
            tools.append(ThinkTool)
        if self.config.enable_finish:
            tools.append(FinishTool)
        if self.config.enable_condensation_request:
            tools.append(CondensationRequestTool)
        if self.config.enable_browsing:
            if sys.platform == 'win32':
                logger.warning('Windows runtime does not support browsing yet')
            else:
                tools.append(BrowserTool)
        if self.config.enable_jupyter:
            tools.append(IPythonTool)
        if self.config.enable_llm_editor:
            tools.append(LLMBasedFileEditTool)
        elif self.config.enable_editor:
            tools.append(
                create_str_replace_editor_tool(
                    use_short_description=use_short_tool_desc
                )
            )

        # Automation-specific tools (if available)
        automation_tools = [
            ResearchTool,
            ContentCreationTool,
            TaskPlannerTool,
            WorkflowOrchestratorTool,
            VerificationTool,
        ]

        # Only add tools that are not None
        for tool in automation_tools:
            if tool is not None:
                tools.append(tool)

        return tools

    def reset(self) -> None:
        """Resets the Automation Agent's internal state."""
        super().reset()
        self.pending_actions.clear()
        self.tasks.clear()
        self.current_task = None
        self.task_counter = 0
        self.current_iteration = 0

    def create_task(
        self,
        description: str,
        task_type: TaskType,
        priority: int = 1,
        dependencies: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Task:
        """Create a new task."""
        self.task_counter += 1
        task_id = f'task_{self.task_counter}'

        task = Task(
            task_id=task_id,
            description=description,
            task_type=task_type,
            priority=priority,
            dependencies=dependencies,
            metadata=metadata,
        )

        self.tasks[task_id] = task
        logger.info(f'Created task {task_id}: {description}')
        return task

    def get_next_task(self) -> Optional[Task]:
        """Get the next task to execute based on priority and dependencies."""
        available_tasks = []

        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING:
                # Check if all dependencies are completed
                dependencies_met = all(
                    self.tasks.get(dep_id, Task('', '', TaskType.MIXED)).status
                    == TaskStatus.COMPLETED
                    for dep_id in task.dependencies
                )

                if dependencies_met:
                    available_tasks.append(task)

        if not available_tasks:
            return None

        # Sort by priority (higher priority first)
        available_tasks.sort(key=lambda t: t.priority, reverse=True)
        return available_tasks[0]

    def step(self, state: State) -> 'Action':
        """
        Performs one step using the Automation Agent.
        This includes task planning, execution, and verification.
        """
        if self.pending_actions:
            return self.pending_actions.popleft()

        # Check if we've exceeded max iterations in autonomous mode
        if self.autonomous_mode and self.current_iteration >= self.max_iterations:
            logger.warning(
                f'Reached maximum iterations ({self.max_iterations}) in autonomous mode'
            )
            return AgentFinishAction(
                outputs={'error': 'Maximum iterations reached in autonomous mode'},
                thought='Reached maximum iterations in autonomous mode',
            )

        self.current_iteration += 1

        # Get the latest user message
        latest_user_message = None
        for event in reversed(state.history):
            if isinstance(event, MessageAction) and event.source == 'user':
                latest_user_message = event
                break

        if latest_user_message is None:
            return MessageAction(
                content="Hello! I'm the Automation Agent. I can help you with complex tasks including research, content creation, software development, data analysis, and workflow automation. What would you like me to help you with?"
            )

        # If this is a new conversation or we don't have a current task, analyze the user's request
        if not self.current_task:
            return self._analyze_and_plan_task(latest_user_message.content, state)

        # Continue with current task
        return self._continue_current_task(state)

    def _analyze_and_plan_task(self, user_request: str, state: State) -> 'Action':
        """Analyze user request and create a task plan."""
        # Use the task planner to break down the request

        # Create a planning task
        planning_task = self.create_task(
            description=f'Plan and analyze: {user_request}',
            task_type=TaskType.MIXED,
            priority=10,
        )

        self.current_task = planning_task
        planning_task.status = TaskStatus.IN_PROGRESS

        # Return a message action to start the planning process
        return MessageAction(
            content=f"I'll help you with: {user_request}\n\nLet me analyze this task and create a comprehensive plan. I'll break it down into manageable steps and execute them systematically."
        )

    def _continue_current_task(self, state: State) -> 'Action':
        """Continue executing the current task."""
        if not self.current_task:
            return MessageAction(content='No current task to continue.')

        # Check if current task is completed
        if self.current_task.status == TaskStatus.COMPLETED:
            # Get next task
            next_task = self.get_next_task()
            if next_task:
                self.current_task = next_task
                next_task.status = TaskStatus.IN_PROGRESS
                return MessageAction(
                    content=f'Starting next task: {next_task.description}'
                )
            else:
                # All tasks completed
                return AgentFinishAction(
                    outputs={
                        'completed_tasks': [
                            task.to_dict()
                            for task in self.tasks.values()
                            if task.status == TaskStatus.COMPLETED
                        ],
                        'summary': 'All tasks have been completed successfully.',
                    },
                    thought='All tasks completed successfully',
                )

        # Execute current task based on its type
        return self._execute_task_step(self.current_task, state)

    def _execute_task_step(self, task: Task, state: State) -> 'Action':
        """Execute a single step of the given task."""
        if task.task_type == TaskType.RESEARCH:
            return self._execute_research_step(task, state)
        elif task.task_type == TaskType.CONTENT_CREATION:
            return self._execute_content_creation_step(task, state)
        elif task.task_type == TaskType.SOFTWARE_DEVELOPMENT:
            return self._execute_development_step(task, state)
        elif task.task_type == TaskType.DATA_ANALYSIS:
            return self._execute_data_analysis_step(task, state)
        elif task.task_type == TaskType.AUTOMATION:
            return self._execute_automation_step(task, state)
        elif task.task_type == TaskType.WORKFLOW:
            return self._execute_workflow_step(task, state)
        else:  # MIXED
            return self._execute_mixed_step(task, state)

    def _execute_research_step(self, task: Task, state: State) -> 'Action':
        """Execute a research task step."""
        # Use browsing and research tools to gather information
        return MessageAction(content=f'Executing research task: {task.description}')

    def _execute_content_creation_step(self, task: Task, state: State) -> 'Action':
        """Execute a content creation task step."""
        return MessageAction(
            content=f'Executing content creation task: {task.description}'
        )

    def _execute_development_step(self, task: Task, state: State) -> 'Action':
        """Execute a software development task step."""
        return MessageAction(content=f'Executing development task: {task.description}')

    def _execute_data_analysis_step(self, task: Task, state: State) -> 'Action':
        """Execute a data analysis task step."""
        return MessageAction(
            content=f'Executing data analysis task: {task.description}'
        )

    def _execute_automation_step(self, task: Task, state: State) -> 'Action':
        """Execute an automation task step."""
        return MessageAction(content=f'Executing automation task: {task.description}')

    def _execute_workflow_step(self, task: Task, state: State) -> 'Action':
        """Execute a workflow task step."""
        return MessageAction(content=f'Executing workflow task: {task.description}')

    def _execute_mixed_step(self, task: Task, state: State) -> 'Action':
        """Execute a mixed task step."""
        return MessageAction(content=f'Executing mixed task: {task.description}')

    def get_task_status(self) -> dict[str, Any]:
        """Get current status of all tasks."""
        return {
            'current_task': self.current_task.to_dict() if self.current_task else None,
            'all_tasks': [task.to_dict() for task in self.tasks.values()],
            'autonomous_mode': self.autonomous_mode,
            'current_iteration': self.current_iteration,
            'max_iterations': self.max_iterations,
        }
