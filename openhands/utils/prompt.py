import os
from dataclasses import dataclass, field
from itertools import islice

from jinja2 import Template

from openhands.controller.state.state import State
from openhands.core.config import AgentConfig
from openhands.core.message import Message, TextContent
from openhands.events.observation.agent import MicroagentKnowledge


@dataclass
class RuntimeInfo:
    date: str
    available_hosts: dict[str, int] = field(default_factory=dict)
    additional_agent_instructions: str = ''
    custom_secrets_descriptions: dict[str, str] = field(default_factory=dict)


@dataclass
class RepositoryInfo:
    """Information about a GitHub repository that has been cloned."""

    repo_name: str | None = None
    repo_directory: str | None = None


@dataclass
class ConversationInstructions:
    """
    Optional instructions the agent must follow throughout the conversation while addressing the user's initial task

    Examples include

        1. Resolver instructions: you're responding to GitHub issue #1234, make sure to open a PR when you are done
        2. Slack instructions: make sure to check whether any of the context attached is relevant to the task <context_messages>
    """

    content: str = ''


class PromptManager:
    """
    Manages prompt templates and includes information from the user's workspace micro-agents and global micro-agents.

    This class is dedicated to loading and rendering prompts (system prompt, user prompt).

    Attributes:
        prompt_dir: Directory containing prompt templates.
    """

    def __init__(
        self,
        prompt_dir: str,
        config: AgentConfig,
        system_prompt_filename: str = 'system_prompt.j2',
    ):
        self.prompt_dir: str = prompt_dir
        self.config: AgentConfig = config

        # Load the correct system prompt based on the config
        if self.config.enable_llm_diff:
            system_template_name = 'system_prompt_llm_diff'
        else:
            system_template_name = 'system_prompt'
        self.system_template: Template = self._load_template(system_template_name)

        # Load other templates
        self.user_template: Template = self._load_template('user_prompt')
        self.additional_info_template: Template = self._load_template('additional_info')
        self.microagent_info_template: Template = self._load_template('microagent_info')

    def _load_system_template(self, system_prompt_filename: str) -> Template:
        """Load the system prompt template using the specified filename."""
        # Remove .j2 extension if present to use with _load_template
        template_name = system_prompt_filename
        if template_name.endswith('.j2'):
            template_name = template_name[:-3]

        try:
            return self._load_template(template_name)
        except FileNotFoundError:
            # Provide a more specific error message for system prompt files
            template_path = os.path.join(self.prompt_dir, f'{template_name}.j2')
            raise FileNotFoundError(
                f'System prompt file "{system_prompt_filename}" not found at {template_path}. '
                f'Please ensure the file exists in the prompt directory: {self.prompt_dir}'
            )

    def _load_template(self, template_name: str) -> Template:
        if self.prompt_dir is None:
            raise ValueError('Prompt directory is not set')
        template_path = os.path.join(self.prompt_dir, f'{template_name}.j2')
        if not os.path.exists(template_path):
            raise FileNotFoundError(f'Prompt file {template_path} not found')
        with open(template_path, 'r') as file:
            return Template(file.read())

    def get_system_message(self) -> str:
        return self.system_template.render().strip()

    def get_example_user_message(self) -> str:
        """This is an initial user message that can be provided to the agent
        before *actual* user instructions are provided.

        It can be used to provide a demonstration of how the agent
        should behave in order to solve the user's task. And it may
        optionally contain some additional context about the user's task.
        These additional context will convert the current generic agent
        into a more specialized agent that is tailored to the user's task.
        """

        return self.user_template.render().strip()

    def build_workspace_context(
        self,
        repository_info: RepositoryInfo | None,
        runtime_info: RuntimeInfo | None,
        conversation_instructions: ConversationInstructions | None,
        repo_instructions: str = '',
    ) -> str:
        """Renders the additional info template with the stored repository/runtime info."""
        return self.additional_info_template.render(
            repository_info=repository_info,
            repository_instructions=repo_instructions,
            runtime_info=runtime_info,
            conversation_instructions=conversation_instructions,
        ).strip()

    def build_microagent_info(
        self,
        triggered_agents: list[MicroagentKnowledge],
    ) -> str:
        """Renders the microagent info template with the triggered agents.

        Args:
            triggered_agents: A list of MicroagentKnowledge objects containing information
                              about triggered microagents.
        """
        return self.microagent_info_template.render(
            triggered_agents=triggered_agents
        ).strip()

    def add_turns_left_reminder(self, messages: list[Message], state: State) -> None:
        latest_user_message = next(
            islice(
                (
                    m
                    for m in reversed(messages)
                    if m.role == 'user'
                    and any(isinstance(c, TextContent) for c in m.content)
                ),
                1,
            ),
            None,
        )
        if latest_user_message:
            reminder_text = ''
            # Every 10 steps
            if state.iteration_flag.current_value % 10 == 0:
                reminder_text += """\n\n## WORKFLOW REMINDER: ## Key Requirements & Constraints

1.  **Understand the problem** very well: it is a bug report, and you know humans don't always write good descriptions. Explore the codebase to understand the related code and the problem in depth. It is possible that the solution needs to be a bit more extensive than just the stated text. Don't exagerate though: don't do unrelated refactoring, but also don't interpret the description too strictly.
2.  **Focus on the issues:** Implement the fix focusing on non-test files related to the issue.
2.  **Environment Ready:** The Python environment is pre-configured with all dependencies. Do not install packages.
3.  **Mandatory Testing Procedure:**
    *   **Create Test to Reproduce the Issue:** *Before* implementing any fix, you MUST create a *new test* (separate from existing tests) that specifically reproduces the issue.
            * Take existing tests as example to understand the testing format/structure.
            * Enhance this test with edge cases.
            * Run this test to confirm reproduction.
    *   **Verify Fix:** After implementing the fix, run your test again to verify the issue is resolved.
    *   **Identify ALL Relevant Tests:** You MUST perform a **dedicated search and analysis** to identify **all** existing unit tests potentially affected by your changes. This includes:
        *   Tests in the same module/directory as the changed files (e.g., `tests/` subdirectories).
        *   Tests explicitly importing or using the modified code/classes/functions.
        *   Tests mentioned in the issue description or related documentation.
        *   Tests covering functionalities that *depend on* the modified code (analyze callers/dependencies if necessary).
        **If you cannot confidently identify a specific subset, you MUST identify and plan to run the entire test suite for the modified application or module(s). State your identified test scope clearly.**
    *   **Run Identified Relevant Tests:** You MUST execute the **complete set** of relevant existing unit tests you identified in the previous step. Ensure you are running the *correct and comprehensive set* of tests. You MUST NOT modify these existing tests.
    *   **Final Check & Verification:** Before finishing, ensure **all** identified relevant existing tests pass. **Explicitly confirm that you have considered potential omissions in your test selection and believe the executed tests comprehensively cover the impact of your changes.** Failing to identify and run the *complete* relevant set constitutes a failure. If any identified tests fail, revise your fix. Passing all relevant tests is the primary measure of success.
4.  **Defensive Programming:** Actively practice defensive programming: anticipate and handle potential edge cases, unexpected inputs, and different ways the affected code might be called **to ensure the fix works reliably and allows relevant tests to pass.** Analyze the potential impact on other parts of the codebase.
5.  **Final Review:** Compare your solution against the original issue and the base commit ({instance["base_commit"]}) to ensure completeness and test passage.

## General Workflow Guidance

*   Prioritize understanding the problem, exploring the code, planning your fix, implementing it carefully using the required diff format, and **thoroughly testing** according to the **Mandatory Testing Procedure**.
*   Consider trade-offs between different solutions. The goal is a **robust change that makes the relevant tests pass.** Quality, correctness, and reliability are key.
*   Actively practice defensive programming: anticipate and handle potential edge cases, unexpected inputs, and different ways the affected code might be called **to ensure the fix works reliably and allows relevant tests to pass.** Analyze the potential impact on other parts of the codebase.

*   IMPORTANT: Your solution will be tested by additional hidden tests, so do not assume the task is complete just because visible tests pass! Refine the solution until you are confident that it is robust and comprehensive according to the **Defensive Programming** requirement.

## Final Note
Be thorough in your exploration, testing, and reasoning. It's fine if your thinking process is lengthy - quality and completeness are more important than brevity.

---
"""
            reminder_text += f'ENVIRONMENT REMINDER: You have {state.iteration_flag.max_value - state.iteration_flag.current_value} turns left to complete the task. When finished reply with <finish></finish>.'
            latest_user_message.content.append(TextContent(text=reminder_text))
