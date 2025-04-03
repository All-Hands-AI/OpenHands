# Supervisor Agent

The Supervisor Agent is designed to delegate tasks to other agents, monitor their execution, verify the correctness of the solution, and detect overthinking in the agent's approach.

## Current Implementation

In its current implementation, the Supervisor Agent:

1. If history has less than 5 events, saves repository state and delegates to CodeActAgent
2. If history has 5 or more events, analyzes the trajectory for overthinking
3. If overthinking is detected OR history has less than 5 events, delegates to CodeActAgent
4. If no overthinking is detected AND history has 5 or more events, finishes the interaction

## History Processing

The Supervisor Agent processes the history of actions and observations from the CodeActAgent and formats it as a string with:

- Initial issue (the first user message)
- Interactions (pairs of agent responses and user observations)
- Final response
- Final finish reason

The formatted history is stored in `state.extra_data['processed_history']` and can be used for:

- Verifying the correctness of the solution
- Debugging the agent's behavior
- Analyzing the agent's performance
- Generating reports

## Overthinking Detection

The Supervisor Agent analyzes the trajectory for overthinking using an LLM. It detects three patterns of overthinking:

1. **Analysis Paralysis**: The model focuses on heavy planning instead of interacting with the environment.
2. **Rogue Actions**: After facing setbacks, the model generates multiple actions without waiting for the environment to process the previous action.
3. **Premature Disengagement**: The model concludes the task without checking with the environment, either because it is overconfident in the solution or because it thinks it can't solve the problem.

The overthinking analysis is stored in `state.extra_data['overthinking_analysis']` and includes:

- `overthinking_score`: A score from 0 to 10, where 0-3 indicates good interaction with the environment, 4-7 indicates some overthinking, and 8-10 indicates severe overthinking.
- `pattern_observed`: A list of patterns observed, or `null` for good trajectories.
- `reasoning`: An explanation of the reasoning behind the score.

If any pattern of overthinking is detected, the Supervisor Agent restarts the task with CodeActAgent, providing a fresh approach.

## Future Enhancements

The Supervisor Agent could be extended to:

- Monitor the progress of delegated tasks in real-time
- Provide feedback or corrections during execution
- Delegate to different agents based on the task type
- Handle multiple delegations in sequence or parallel
- Implement retry mechanisms for failed tasks
- Optimize resource usage across multiple agents
- Generate summaries and insights from the execution history
- Provide more detailed feedback on overthinking patterns
- Implement more sophisticated overthinking detection algorithms

## Usage

To use the Supervisor Agent, select it as your agent in the OpenHands interface or specify it in your configuration.

```python
from openhands.agenthub.supervisor_agent import SupervisorAgent
```

To access the processed history after execution:

```python
processed_history = state.extra_data.get('processed_history', '')
```
