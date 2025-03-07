import json
import os
from collections import deque

import openhands
from openhands.controller.agent import Agent
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import Message, TextContent
from openhands.events.action import (
    Action,
    AgentFinishAction,
    MessageAction,
    CmdRunAction,
    FileReadAction,
    FileWriteAction,
    BrowseURLAction,
    IPythonRunCellAction,
)
from openhands.llm.llm import LLM
from openhands.memory.condenser import Condenser
from openhands.memory.conversation_memory import ConversationMemory
from openhands.runtime.plugins import (
    AgentSkillsRequirement,
    JupyterRequirement,
    PluginRequirement,
)
from openhands.utils.prompt import PromptManager


class DevinAgent(Agent):
    VERSION = '1.0'
    """
    The Devin Agent is an autonomous software engineering agent.
    
    It has the following key capabilities:
    1. Long-term planning and reasoning
    2. Code creation, execution, and testing
    3. Bug detection and fixing
    4. Feedback handling
    5. Adaptation to new technologies
    6. End-to-end application building and deployment
    
    The agent works by:
    1. Planning: Breaking down tasks into smaller steps
    2. Execution: Executing each step using appropriate tools
    3. Verification: Verifying the results of each step
    4. Adaptation: Adapting the plan based on results and feedback
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
        """Initializes a new instance of the DevinAgent class.

        Parameters:
        - llm (LLM): The llm to be used by this agent
        - config (AgentConfig): The configuration for this agent
        """
        super().__init__(llm, config)
        self.pending_actions: deque[Action] = deque()
        self.reset()
        
        # Initialize planning system
        self.current_plan = []
        self.current_step_index = 0
        
        # Initialize prompt manager
        self.prompt_manager = PromptManager(
            microagent_dir=os.path.join(
                os.path.dirname(os.path.dirname(openhands.__file__)),
                'microagents',
            )
            if self.config.enable_prompt_extensions
            else None,
            prompt_dir=os.path.join(os.path.dirname(__file__), 'prompts'),
            disabled_microagents=self.config.disabled_microagents,
        )

        # Create a ConversationMemory instance
        self.conversation_memory = ConversationMemory(self.prompt_manager)

        self.condenser = Condenser.from_config(self.config.condenser)
        logger.debug(f'Using condenser: {type(self.condenser)}')

    def reset(self) -> None:
        """Resets the Devin Agent."""
        super().reset()
        self.pending_actions.clear()
        self.current_plan = []
        self.current_step_index = 0

    def step(self, state: State) -> Action:
        """Performs one step using the Devin Agent.
        
        This method implements the core logic of the Devin Agent:
        1. If there are pending actions, execute them
        2. If there is no current plan, create one
        3. If there is a current plan, execute the next step
        4. If the plan is complete, create a new plan or finish

        Parameters:
        - state (State): used to get updated info

        Returns:
        - An Action to be executed
        """
        # Continue with pending actions if any
        if self.pending_actions:
            return self.pending_actions.popleft()

        # Check for exit command
        latest_user_message = state.get_last_user_message()
        if latest_user_message and latest_user_message.content.strip() == '/exit':
            return AgentFinishAction()

        # Prepare what we want to send to the LLM
        messages = self._get_messages(state)
        
        # If there is no current plan, create one
        if not self.current_plan:
            # Generate a plan using the LLM
            planning_messages = self._create_planning_messages(messages)
            planning_response = self.llm.completion(messages=self.llm.format_messages_for_llm(planning_messages))
            self.current_plan = self._parse_plan(planning_response.content)
            self.current_step_index = 0
            
            # Inform the user about the plan
            plan_message = "計画を立てました：\n\n" + "\n".join([f"{i+1}. {step}" for i, step in enumerate(self.current_plan)])
            self.pending_actions.append(MessageAction(content=plan_message))
            return self.pending_actions.popleft()
        
        # If there is a current plan, execute the next step
        if self.current_step_index < len(self.current_plan):
            current_step = self.current_plan[self.current_step_index]
            
            # Generate action for the current step
            step_messages = self._create_step_execution_messages(messages, current_step)
            step_response = self.llm.completion(messages=self.llm.format_messages_for_llm(step_messages))
            actions = self._parse_actions(step_response.content)
            
            # Add actions to pending actions
            for action in actions:
                self.pending_actions.append(action)
            
            # Increment step index if this is the last action for this step
            if not self._is_intermediate_action(actions[-1]):
                self.current_step_index += 1
            
            return self.pending_actions.popleft()
        
        # If the plan is complete, finish or create a new plan
        return AgentFinishAction()

    def _get_messages(self, state: State) -> list[Message]:
        """Constructs the message history for the LLM conversation.

        Args:
            state (State): The current state object containing conversation history and other metadata

        Returns:
            list[Message]: A list of formatted messages ready for LLM consumption
        """
        if not self.prompt_manager:
            raise Exception('Prompt Manager not instantiated.')

        # Use conversation_memory to process events
        messages = self.conversation_memory.process_initial_messages(
            with_caching=self.llm.is_caching_prompt_active()
        )

        # Condense the events from the state
        events = self.condenser.condensed_history(state)

        logger.debug(
            f'Processing {len(events)} events from a total of {len(state.history)} events'
        )

        messages = self.conversation_memory.process_events(
            condensed_history=events,
            initial_messages=messages,
            max_message_chars=self.llm.config.max_message_chars,
            vision_is_active=self.llm.vision_is_active(),
            enable_som_visual_browsing=self.config.enable_som_visual_browsing,
        )

        messages = self._enhance_messages(messages)

        if self.llm.is_caching_prompt_active():
            self.conversation_memory.apply_prompt_caching(messages)

        return messages

    def _enhance_messages(self, messages: list[Message]) -> list[Message]:
        """Enhances the user message with additional context based on keywords matched.

        Args:
            messages (list[Message]): The list of messages to enhance

        Returns:
            list[Message]: The enhanced list of messages
        """
        assert self.prompt_manager, 'Prompt Manager not instantiated.'

        results: list[Message] = []
        is_first_message_handled = False
        prev_role = None

        for msg in messages:
            if msg.role == 'user' and not is_first_message_handled:
                is_first_message_handled = True
                # compose the first user message with examples
                self.prompt_manager.add_examples_to_initial_message(msg)

                # and/or repo/runtime info
                if self.config.enable_prompt_extensions:
                    self.prompt_manager.add_info_to_initial_message(msg)

            # enhance the user message with additional context based on keywords matched
            if msg.role == 'user':
                self.prompt_manager.enhance_message(msg)

                # Add double newline between consecutive user messages
                if prev_role == 'user' and len(msg.content) > 0:
                    # Find the first TextContent in the message to add newlines
                    for content_item in msg.content:
                        if isinstance(content_item, TextContent):
                            # If the previous message was also from a user, prepend two newlines to ensure separation
                            content_item.text = '\n\n' + content_item.text
                            break

            results.append(msg)
            prev_role = msg.role

        return results
        
    def _create_planning_messages(self, messages: list[Message]) -> list[Message]:
        """Creates messages for planning.
        
        Args:
            messages (list[Message]): The base messages
            
        Returns:
            list[Message]: Messages for planning
        """
        # Create a copy of the messages
        planning_messages = messages.copy()
        
        # Add planning instruction
        planning_instruction = Message(
            role="system",
            content="あなたはタスクを小さなステップに分割する計画立案者です。ユーザーのタスクを分析し、実行可能な小さなステップに分割してください。各ステップは具体的で、実行可能であるべきです。計画は以下の形式で返してください：\n\n1. ステップ1の説明\n2. ステップ2の説明\n...\n\n計画のみを返し、他の説明は含めないでください。"
        )
        planning_messages.append(planning_instruction)
        
        return planning_messages
        
    def _parse_plan(self, response: str) -> list[str]:
        """Parses the plan from the LLM response.
        
        Args:
            response (str): The LLM response
            
        Returns:
            list[str]: The parsed plan steps
        """
        # Simple parsing logic - split by numbered lines
        lines = response.strip().split('\n')
        plan = []
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() and '. ' in line):
                # Extract the step description after the number and dot
                step = line.split('. ', 1)[1]
                plan.append(step)
        
        return plan
        
    def _create_step_execution_messages(self, messages: list[Message], current_step: str) -> list[Message]:
        """Creates messages for executing a step.
        
        Args:
            messages (list[Message]): The base messages
            current_step (str): The current step to execute
            
        Returns:
            list[Message]: Messages for executing the step
        """
        # Create a copy of the messages
        step_messages = messages.copy()
        
        # Add step execution instruction
        step_instruction = Message(
            role="system",
            content=f"現在のステップを実行してください：{current_step}\n\n以下のアクションを使用できます：\n1. CmdRunAction - シェルコマンドを実行\n2. FileReadAction - ファイルを読み込む\n3. FileWriteAction - ファイルに書き込む\n4. BrowseURLAction - URLを閲覧\n5. IPythonRunCellAction - Pythonコードを実行\n6. MessageAction - ユーザーにメッセージを送信\n\nステップを実行するために必要なアクションを返してください。"
        )
        step_messages.append(step_instruction)
        
        return step_messages
        
    def _parse_actions(self, response: str) -> list[Action]:
        """Parses actions from the LLM response.
        
        Args:
            response (str): The LLM response
            
        Returns:
            list[Action]: The parsed actions
        """
        # Simple parsing logic - this would need to be more sophisticated in a real implementation
        actions = []
        
        # For now, just create a message action with the response
        actions.append(MessageAction(content=f"ステップ実行中: {response[:100]}..."))
        
        # This is a placeholder - in a real implementation, we would parse the response
        # to extract actual actions like CmdRunAction, FileReadAction, etc.
        
        return actions
        
    def _is_intermediate_action(self, action: Action) -> bool:
        """Determines if an action is an intermediate action.
        
        Args:
            action (Action): The action to check
            
        Returns:
            bool: True if the action is intermediate, False otherwise
        """
        # For now, consider all actions as non-intermediate
        return False
