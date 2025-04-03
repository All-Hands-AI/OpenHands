import json
from collections import deque
from typing import List, Optional, TypedDict

from openhands.controller.agent import Agent
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig
from openhands.core.logger import openhands_logger as logger
from openhands.core.schema import ActionType, ObservationType
from openhands.events.action import (
    Action,
    AgentDelegateAction,
    AgentFinishAction,
    AgentFinishTaskCompleted,
    AgentThinkAction,
    CmdRunAction,
    MessageAction,
    NullAction,
)
from openhands.events.event import EventSource
from openhands.events.observation import (
    AgentDelegateObservation,
    CmdOutputObservation,
    Observation,
)
from openhands.llm.llm import LLM


class Interaction(TypedDict):
    """Represents an interaction between the agent and the environment."""

    response: str
    observation: str


class ProcessedHistory(TypedDict):
    """Represents the processed history of actions and observations."""

    initial_issue: str
    interactions: List[Interaction]
    final_response: str
    final_finish_reason: str


class OverthinkingAnalysis(TypedDict):
    """Represents the analysis of overthinking in the agent's trajectory."""

    overthinking_score: str
    pattern_observed: Optional[List[str]]
    reasoning: str


class SupervisorAgent(Agent):
    VERSION = '1.0'
    """
    The Supervisor Agent delegates tasks to other agents and monitors their execution.

    Currently, it delegates to CodeActAgent, waits for it to complete, and then verifies
    the correctness of the solution by analyzing the history of actions and observations.

    In the future, it could be extended to:
    - Monitor the progress of delegated tasks
    - Provide feedback or corrections
    - Delegate to different agents based on the task
    - Handle multiple delegations in sequence or parallel
    """

    def __init__(
        self,
        llm: LLM,
        config: AgentConfig,
        skip_git_commands: bool = False,  # Add parameter for testing
    ) -> None:
        """Initializes a new instance of the SupervisorAgent class.

        Parameters:
        - llm (LLM): The llm to be used by this agent
        - config (AgentConfig): The configuration for this agent
        - skip_git_commands (bool): If True, skip git commands (for testing)
        """
        super().__init__(llm, config)
        self.pending_actions: deque[Action] = deque()
        self.reset()
        self.delegated = False
        self.finished = False
        self.pre_delegation_commit: Optional[str] = None
        self.skip_git_commands = skip_git_commands  # Store the flag

    def reset(self) -> None:
        """Resets the Supervisor Agent."""
        super().reset()
        self.pre_delegation_commit = None
        self.pending_actions.clear()
        self.delegated = False
        self.finished = False
        # Don't reset skip_git_commands as it's a configuration parameter

        # Clear delegated_state from extra_data if it exists
        if hasattr(self, 'state') and hasattr(self.state, 'extra_data'):
            self.state.extra_data.pop('delegated_state', None)

    def get_descriptive_finish_reason(self, finish_reason: str) -> str:
        """Convert basic finish reasons into more descriptive ones."""
        reason_mapping = {
            'stop': 'FINISHED_WITH_STOP_ACTION',
            'tool_calls': 'FINISHED_WITH_FUNCTION_CALL',
            'length': 'EXCEEDED_MAX_LENGTH',
            'content_filter': 'CONTENT_FILTERED',
            'budget_exceeded': 'BUDGET_EXCEEDED',
        }
        return reason_mapping.get(finish_reason, finish_reason.upper())

    def get_first_user_message(self, state: State) -> str:
        """Extract the first user message from the history."""
        for event in state.history:
            if isinstance(event, MessageAction) and event.source == EventSource.USER:
                return event.content
        return ''

    def handle_cmd_output_observation(
        self, observation: CmdOutputObservation, state: State
    ) -> None:
        """Handle the CmdOutputObservation to store the commit hash."""
        logger.info(
            f'SupervisorAgent: Handling CmdOutputObservation: {observation.command}'
        )

        # Check if this is the git rev-parse HEAD command result
        if (
            observation.command == 'git rev-parse HEAD'
            and observation.metadata.exit_code == 0
        ):
            # Store the commit hash
            commit_hash = observation.content.strip()
            logger.info(f'SupervisorAgent: Got commit hash: {commit_hash}')
            logger.info(
                f'SupervisorAgent: Stored pre-delegation commit hash: {commit_hash}'
            )
            self.pre_delegation_commit = commit_hash

            # Also store it in state.extra_data for persistence
            state.extra_data['pre_delegation_commit'] = commit_hash

    def create_analysis_prompt(self, processed_history: str) -> str:
        """Create a prompt for analyzing overthinking in the agent's trajectory.

        Args:
            processed_history: The processed history of actions and observations.

        Returns:
            A prompt for analyzing overthinking in the agent's trajectory.
        """
        prompt = """You are an AI judge focused on detecting when models prefer their internal reasoning chain over interacting with the environment.

<INTERACTION>
{processed_history}
</INTERACTION>

Analyze the <INTERACTION> and determine if the model is preferring their internal reasoning chain over interacting with the environment:

How could this be detected?
<CORE PRINCIPLE>
- The model suffers from Analysis Paralysis, it focuses on heavy planning instead of interacting with the environment.
- The model suffers from Rogue actions, after facing setbacks, it generates multiple actions without waiting for the environment to process the previous action.
- The model suffers from Premature Disengagement, it concludes the task without checking with the environment. Either because it is overconfident in the solution or because it thinks it can't solve the problem.
</CORE PRINCIPLE>

<SCORING SYSTEM (0-10)>
0-3: Always interacting with the environment
- A summary of what has been done so far is good, even if done multiple times.
- A brief summary of the steps to take is good if the model interacts with the environment following steps one by one.
- Only one action per turn, finish and other actions are NOT allowed.
- Alternating between two operations is good.
- Trying the same approach over and over is good, even with long or complex actions, as long as the model waits for environment feedback each time.
- Repeating similar patterns or configurations is fine as long as the model interacts with the environment between attempts.
- Detailed reasoning and planning is good if it leads to concrete actions with environment interaction.

4-7: Sometimes relies too much on their internal reasoning chain, but still interacts with the environment.
- It engages in heavy planning, but still interacts with the environment.
- It NEVER concludes the task without checking with the environment.
- It might output multiple steps ONE time, but at subsequent turns it interacts one step at a time.
- Long theoretical discussions are acceptable if they eventually result in concrete actions.

8-10: Completely relies on their internal reasoning chain.
- Focuses solely on their internal reasoning chain, with no concrete actions following the analysis.
- Generates multiple actions without waiting for environment response.
- The model prematurely concludes the task. Either because it is overconfident in the solution or because it thinks it can't solve the problem.
- Generates many steps without any environment interaction.
- Gets stuck in endless theoretical discussion without attempting solutions.
</SCORING SYSTEM>

<ANALYSIS STEPS>
1. Analysis Paralysis
   - Is the model focusing on heavy planning instead of interacting with the environment?
   - Does the model interact with the environment at all?
   - Does the model follows its planned steps starting from the first one?
2. Rogue Actions
   - Does the model generate multiple actions without waiting for the environment to process the previous action?
   - Is this behavior after a facing a setback?
   - Does this behaviour happen often?
3. Premature Disengagement
   - Does the model prematurely conclude the task?
   - Is the model overconfident in the solution?
   - Is the model thinking it can't solve the problem?
</ANALYSIS STEPS>

<EXAMPLES>

Example 1 - Persistent Retries (Good):
EXECUTION RESULT: "Error: Invalid configuration"
Model: *tries complex configuration A*
EXECUTION RESULT: "Error: Invalid configuration"
Model: *tries similar complex configuration A with slight modification*
EXECUTION RESULT: "Error: Invalid configuration"
Model: *tries complex configuration A again with another modification*
Score: 0 - The model is persistently trying to solve the problem, waiting for environment feedback between each attempt. Even though the attempts are similar and complex, it's properly interacting with the environment.
Patterns observed: null

Example 2 - Thoughtful Planning (Good):
Model: *provides detailed analysis of the problem and potential approaches*
Model: *tries specific solution based on analysis*
EXECUTION RESULT: "Error in implementation"
Model: *refines approach based on error and tries again*
Score: 0 - While the model engages in detailed planning, it follows through with concrete actions and responds to environment feedback.
Patterns observed: null

Example 3 - Analysis Paralysis:
EXECUTION RESULT: "Invalid indentation line 10"
Model: *Maybe I should... Perhaps I should... It should be... Let me try to start again rewriting the class*
EXECUTION RESULT: "Still invalid line 10"
Model: *Its not working... We also need to fix this other thing...*
EXECUTION RESULT:  "Same error line 10"
Score: 10 - focuses on its internal reasoning chain instead of the environment.
Patterns observed: ["Analysis Paralysis"]

Example 4 - Premature Disengagement:
EXECUTION RESULT: "Invalid indentation line 10"
Model: *This fixes it! I'll conclude the task. <function=finish>*
Score: 10 - The model concludes the task without applying the fix or overconfidence in the solution.
Patterns observed: ["Premature Disengagement"]

Example 5 - Rogue Actions:
EXECUTION RESULT: "Invalid indentation line 10"
Model: *Oh no, I forgot to add the old string, let me call the function again <function=str_replace_editor>...</function> and then we do this other thing <function=str_replace_editor>...</function>*
Score: 10 - The model generates multiple actions after facing a setback without waiting for the environment to process the previous action.
Patterns observed: ["Rogue Actions"]

</EXAMPLES>

<IMPORTANT>
Format your response as:
<answer>
{{
    "overthinking_score": "[0-10]",
    "pattern_observed": ["list of patterns observed or null for good trajectories"],
    "reasoning": "Explain your reasoning for the score, be careful with new lines as they might break the JSON parsing"
}}
</answer>
Always surround your answer with <answer> and </answer> tags.
Take your time to understand the interaction and analyze it carefully.
Think step by step if models prefer their internal reasoning chain over interacting with the environment.
If the trajectory is good (score 0-3), set "pattern_observed" to null.
</IMPORTANT>
"""
        return prompt.format(processed_history=processed_history)

    def analyze_trajectory(
        self, processed_history: str
    ) -> Optional[OverthinkingAnalysis]:
        """Analyze the trajectory for overthinking using the LLM.

        Args:
            processed_history: The processed history of actions and observations.

        Returns:
            An analysis of overthinking in the agent's trajectory, or None if the analysis failed.
        """
        try:
            prompt = self.create_analysis_prompt(processed_history)
            response = self.llm.completion(
                messages=[{'role': 'user', 'content': prompt}],
            )

            llm_response = response['choices'][0]['message']['content'].strip()

            try:
                start_idx = llm_response.find('<answer>')
                end_idx = llm_response.find('</answer>')

                if start_idx == -1 or end_idx == -1:
                    logger.error('Could not find answer tags in LLM response')
                    return None

                start_idx += len('<answer>')
                json_str = llm_response[start_idx:end_idx].strip()

                analysis_json = json.loads(json_str)

                # Convert to OverthinkingAnalysis
                analysis: OverthinkingAnalysis = {
                    'overthinking_score': analysis_json['overthinking_score'],
                    'pattern_observed': analysis_json['pattern_observed'],
                    'reasoning': analysis_json['reasoning'],
                }

                return analysis

            except json.JSONDecodeError as e:
                logger.error(f'JSON parsing error: {e}')
                logger.error(f'Position of error: {e.pos}')
                logger.error(f'Line number: {e.lineno}')
                logger.error(f'Column: {e.colno}')
                logger.error(f'Attempted to parse: {json_str}')
                return None

        except Exception as e:
            logger.error(f'Error analyzing trajectory: {e}')
            logger.error(f'Error type: {type(e)}')
            return None

    def process_history_with_observations(self, state: State) -> str:
        """Process the history of actions and observations and format it as a string.

        This method extracts:
        - Initial issue (first user message)
        - Interactions (pairs of agent responses and user observations)
        - Final response
        - Final finish reason

        Only processes events that occurred after the MOST RECENT delegation to CodeActAgent.
        This ensures that if we redelegate with clear_history=True, we only process events
        after that redelegation, not all events since the beginning.

        Returns:
            A formatted string with the history of actions and observations.
        """
        # Initialize the output structure
        output_data: ProcessedHistory = {
            'initial_issue': self.get_first_user_message(state),
            'interactions': [],
            'final_response': '',
            'final_finish_reason': '',
        }

        # Process the history to extract interactions
        agent_responses = []
        observations = []

        # Find the MOST RECENT delegation event to only process events after it
        delegation_indices = []
        for i, event in enumerate(state.history):
            if (
                hasattr(event, 'action')
                and event.action == ActionType.DELEGATE
                and hasattr(event, 'agent')
                and event.agent == 'CodeActAgent'
            ):
                delegation_indices.append(i)
                logger.info(f'SupervisorAgent: Found delegation event at index {i}')

        # If no delegation events found
        if not delegation_indices:
            logger.warning(
                'SupervisorAgent: Could not find delegation event in history'
            )
            return 'No delegation event found in history'

        # Use the most recent delegation event
        delegation_index = delegation_indices[-1]
        logger.info(
            f'SupervisorAgent: Using MOST RECENT delegation event at index {delegation_index} (total events: {len(state.history)})'
        )

        # Iterate through the history, only processing events after the most recent delegation
        for i, event in enumerate(state.history):
            # Skip events before the most recent delegation
            if i <= delegation_index:
                continue

            # Process events after delegation
            if isinstance(event, MessageAction) and event.source == EventSource.AGENT:
                agent_responses.append((i, event.content))
            elif isinstance(event, Observation) and not isinstance(
                event, AgentDelegateObservation
            ):
                observations.append((i, event))

        # Pair responses with observations
        for i in range(len(agent_responses) - 1):
            response_idx, response = agent_responses[i]

            # Find the next observation after this response but before the next response
            next_response_idx = (
                agent_responses[i + 1][0]
                if i + 1 < len(agent_responses)
                else float('inf')
            )

            # Find observations between this response and the next
            relevant_observations = [
                obs[1]
                for obs in observations
                if response_idx < obs[0] < next_response_idx
            ]

            # Combine observations into a single string
            observation_text = '\n'.join(
                [
                    f"{obs.__class__.__name__}: {obs.content if hasattr(obs, 'content') else str(obs)}"
                    for obs in relevant_observations
                ]
            )

            # If there are no observations, use a placeholder
            if not observation_text:
                observation_text = 'No observations recorded'

            if response:
                interaction: Interaction = {
                    'response': response,
                    'observation': observation_text,
                }
                output_data['interactions'].append(interaction)

        # Handle the last response
        if agent_responses:
            output_data['final_response'] = agent_responses[-1][1]

        # Determine finish reason
        # For now, we'll use a placeholder
        output_data['final_finish_reason'] = self.get_descriptive_finish_reason('stop')

        # Format the output as a string
        formatted_output = f"{'#' * 80}\n"
        formatted_output += 'INITIAL ISSUE:\n'
        formatted_output += f"{'#' * 80}\n"
        formatted_output += f"{output_data['initial_issue']}\n"
        formatted_output += f"{'#' * 80}\n\n"

        # Write interactions
        for interaction in output_data['interactions']:
            formatted_output += f"\n{'=' * 80}\n"
            formatted_output += f"RESPONSE:\n{interaction.get('response', '')}\n\n"
            formatted_output += f"{'-' * 40} OBSERVATION {'-' * 40}\n"
            formatted_output += f"{interaction.get('observation', '')}\n"

        # Write final response
        if output_data['final_response']:
            formatted_output += f"\n{'=' * 80}\n"
            formatted_output += f"LAST RESPONSE:\n{output_data['final_response']}\n"
            if output_data['final_finish_reason']:
                formatted_output += (
                    f"\nFINISH REASON: {output_data['final_finish_reason']}\n"
                )

        return formatted_output

    def step(self, state: State) -> Action:
        """Performs one step using the Supervisor Agent.

        This method:
        1. If history < 5 events, saves repository state and delegates to CodeActAgent
        2. If history >= 5 events, analyzes for overthinking
        3. If overthinking detected OR history < 5, delegates to CodeActAgent
        4. If no overthinking AND history >= 5, finishes the interaction

        Parameters:
        - state (State): used to get updated info

        Returns:
        - AgentDelegateAction - delegate to CodeActAgent
        - AgentFinishAction - finish when CodeActAgent is done and no overthinking detected
        """
        # Process any CmdOutputObservation to store commit hash
        for event in reversed(state.history):
            if isinstance(event, CmdOutputObservation):
                self.handle_cmd_output_observation(event, state)
                break

        # Continue with pending actions if any
        if self.pending_actions:
            return self.pending_actions.popleft()

        # Check if we're in the restart sequence after detecting overthinking
        if 'restart_reason' in state.extra_data and not state.extra_data.get('delegated_state', False):
            # Find the last message or command in the history
            last_event_type = None
            for event in reversed(state.history):
                if isinstance(event, MessageAction) and 'detected overthinking' in event.content.lower():
                    last_event_type = 'overthinking_message'
                    break
                elif isinstance(event, CmdRunAction) and 'git reset --hard' in event.command:
                    last_event_type = 'git_reset'
                    break
                elif isinstance(event, CmdOutputObservation) and 'git reset --hard' in event.command:
                    last_event_type = 'git_reset_output'
                    break

            # After the overthinking message, reset the repository
            if last_event_type == 'overthinking_message':
                # Reset the repository to the state before delegation
                commit_hash = self.pre_delegation_commit or state.extra_data.get('pre_delegation_commit')
                if commit_hash:
                    logger.info(f'SupervisorAgent: Resetting repository to commit {commit_hash}')
                    return CmdRunAction(
                        command=f'git reset --hard {commit_hash}',
                        thought='Resetting the repository to the state before delegation',
                    )
                else:
                    logger.warning('SupervisorAgent: No pre-delegation commit hash found, cannot reset repository')
                    last_event_type = 'git_reset_output'  # Skip to delegation

            # After git reset, delegate to CodeActAgent again
            if last_event_type == 'git_reset' or last_event_type == 'git_reset_output':
                logger.info('SupervisorAgent: Redelegating to CodeActAgent with clear_history=True')
                # Clear the restart reason and max iterations flags
                state.extra_data.pop('restart_reason', None)
                state.extra_data.pop('max_iterations_reached', None)
                state.extra_data.pop('max_iterations_reason', None)
                # Update delegated state
                self.delegated = True
                state.extra_data['delegated_state'] = True
                return AgentDelegateAction(
                    agent='CodeActAgent',
                    inputs=state.inputs,
                    thought="I'll delegate this task to CodeActAgent again with a fresh approach.",
                    clear_history=True,
                )

        # Check if history is less than 5 events or we haven't delegated yet
        if len(state.history) < 5 or not self.delegated:
            # First step: save the repository state before delegating
            logger.info('SupervisorAgent: Saving repository state before delegating')

            # If skip_git_commands is True, skip the git commands and directly delegate
            if self.skip_git_commands:
                logger.info('SupervisorAgent: Skipping git commands (for testing)')
                self.delegated = True
                state.extra_data['delegated_state'] = True
                return AgentDelegateAction(
                    agent='CodeActAgent',
                    inputs=state.inputs,
                    thought="I'll delegate this task to CodeActAgent to handle it.",
                    clear_history=True,
                )

            # If we're in the middle of the git command sequence
            last_cmd = None
            for event in reversed(state.history):
                if isinstance(event, CmdRunAction):
                    last_cmd = event.command
                    break
                elif isinstance(event, CmdOutputObservation):
                    last_cmd = event.command
                    break

            if last_cmd is not None:
                # After git status, commit any changes
                if 'git status' in last_cmd:
                    return CmdRunAction(
                        command='git diff-index --quiet HEAD || git commit -a -m "SUPERVISOR_AGENT_CHECKPOINT: Saving state before delegation"',
                        thought='Committing any changes before delegation',
                    )
                # After commit, get the commit hash
                elif 'git commit' in last_cmd or 'git diff-index' in last_cmd:
                    return CmdRunAction(
                        command='git rev-parse HEAD',
                        thought='Getting the commit hash to save for potential reset',
                    )
                # After getting commit hash, delegate to CodeActAgent
                elif 'git rev-parse HEAD' in last_cmd:
                    logger.info('SupervisorAgent: Delegating to CodeActAgent with clear_history=True')
                    state.extra_data['delegated_state'] = True
                    return AgentDelegateAction(
                        agent='CodeActAgent',
                        inputs=state.inputs,
                        thought="I'll delegate this task to CodeActAgent to handle it.",
                        clear_history=True,
                    )
            
            # Start the git command sequence
            self.delegated = True
            state.extra_data['delegated_state'] = True
            return CmdRunAction(
                command='git status --porcelain',
                thought='Checking if there are any changes to commit before delegation',
            )

        # Check if the delegated agent has finished
        delegate_observation_found = False
        for event in reversed(state.history):
            if (isinstance(event, AgentDelegateObservation) or 
                (hasattr(event, 'observation') and event.observation == ObservationType.DELEGATE)):
                delegate_observation_found = True
                break

        # Process history and run overthinking analysis if there are at least 5 events in the history
        overthinking_detected = False
        if len(state.history) >= 5:
            # Process the history of actions and observations
            processed_history = self.process_history_with_observations(state)
            state.extra_data['processed_history'] = processed_history
            
            # Analyze the trajectory for overthinking
            logger.info('SupervisorAgent: Analyzing trajectory for overthinking')
            overthinking_analysis = self.analyze_trajectory(processed_history)
            
            # Store the overthinking analysis in the state's extra_data
            if overthinking_analysis:
                state.extra_data['overthinking_analysis'] = overthinking_analysis
                logger.info(f'SupervisorAgent: Overthinking analysis: {overthinking_analysis}')
                
                # Check if the trajectory shows overthinking
                if overthinking_analysis['pattern_observed'] is not None:
                    overthinking_detected = True
                    logger.info('SupervisorAgent: Detected overthinking, restarting task with CodeActAgent')
                    
                    # When overthinking is detected, we don't collect the git patch
                    # as requested by the user
                    
                    # Reset the agent state
                    self.delegated = False
                    self.finished = False
                    
                    # Store the overthinking info for the restart sequence
                    state.extra_data['restart_reason'] = {
                        'score': overthinking_analysis['overthinking_score'],
                        'patterns': overthinking_analysis['pattern_observed'],
                    }
                    state.extra_data['delegated_state'] = False
                    
                    # If skip_git_commands is True, skip the message and directly redelegate
                    if self.skip_git_commands:
                        logger.info('SupervisorAgent: Skipping git commands (for testing)')
                        state.extra_data.pop('restart_reason', None)
                        state.extra_data.pop('max_iterations_reached', None)
                        state.extra_data.pop('max_iterations_reason', None)
                        self.delegated = True
                        state.extra_data['delegated_state'] = True
                        return AgentDelegateAction(
                            agent='CodeActAgent',
                            inputs=state.inputs,
                            thought="I'll delegate this task to CodeActAgent again with a fresh approach.",
                            clear_history=True,
                        )
                    
                    # Return a message action explaining the restart without git patch in outputs
                    return MessageAction(
                        content=(
                            f"I've detected overthinking in the CodeActAgent's approach "
                            f"(score: {overthinking_analysis['overthinking_score']}, "
                            f"patterns: {overthinking_analysis['pattern_observed']}). "
                            f"Restarting the task with a fresh approach."
                        )
                    )

        # If delegate observation was found, no overthinking was detected, and history >= 5, finish normally
        if delegate_observation_found and not overthinking_detected and len(state.history) >= 5:
            self.finished = True
            
            # Collect git patch before finishing
            git_patch = ""
            if not self.skip_git_commands:
                logger.info('SupervisorAgent: Collecting git patch before finishing')
                
                # Configure git to not use a pager
                self.pending_actions.append(
                    CmdRunAction(
                        command='git config --global core.pager ""',
                        thought='Configuring git to not use a pager',
                    )
                )
                
                # Add all files to git staging
                self.pending_actions.append(
                    CmdRunAction(
                        command='git add -A',
                        thought='Adding all files to git staging to prepare for diff',
                    )
                )
                
                # Get the base commit from state.inputs if available
                base_commit = ""
                if hasattr(state, 'inputs') and 'base_commit' in state.inputs:
                    base_commit = state.inputs['base_commit']
                
                # Get the diff with retries
                max_retries = 3
                for retry in range(max_retries):
                    # Get the diff
                    self.pending_actions.append(
                        CmdRunAction(
                            command=f'git diff --no-color --cached {base_commit}',
                            thought=f'Getting git diff to include in the final output (attempt {retry+1}/{max_retries})',
                        )
                    )
                    
                    # Process the pending actions to get the git patch
                    while self.pending_actions:
                        action = self.pending_actions.popleft()
                        observation = state.runtime.run_action(action)
                        
                        # If this is the git diff command output, store the patch
                        if (isinstance(observation, CmdOutputObservation) and 
                            'git diff --no-color --cached' in observation.command):
                            if observation.exit_code == 0:
                                git_patch = observation.content.strip()
                                logger.info(f'SupervisorAgent: Collected git patch: {git_patch[:100]}...')
                                break  # Break out of the while loop
                            else:
                                logger.warning(f'SupervisorAgent: Failed to get git diff (attempt {retry+1}/{max_retries}): {observation.content}')
                    
                    # If we got the git patch, break out of the retry loop
                    if git_patch:
                        break
            
            return AgentFinishAction(
                final_thought=(
                    "The CodeActAgent has completed the task. I've supervised the execution, "
                    'processed the history of actions and observations, and verified the solution.'
                ),
                task_completed=AgentFinishTaskCompleted.TRUE,
                outputs={'git_patch': git_patch}
            )

        # Check if we've already delegated to CodeActAgent
        delegation_found = False
        for event in reversed(state.history):
            if (isinstance(event, AgentDelegateAction) and 
                event.agent == 'CodeActAgent' and 
                event.source == EventSource.AGENT):
                delegation_found = True
                break

        # If we've already delegated, return NullAction to avoid taking steps while delegate is active
        if delegation_found:
            logger.info('SupervisorAgent: Already delegated to CodeActAgent, returning NullAction')
            return NullAction()

        # If we haven't delegated yet, return a ThinkAction
        return AgentThinkAction(
            thought="I've delegated this task to CodeActAgent. I'm waiting for it to complete."
        )
