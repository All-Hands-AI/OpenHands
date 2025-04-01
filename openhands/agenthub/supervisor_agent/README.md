# Supervisor Agent

The Supervisor Agent is designed to delegate tasks to other agents, monitor their execution, and verify the correctness of the solution.

## Current Implementation

In its current implementation, the Supervisor Agent:

1. Delegates all tasks to the CodeActAgent
2. Waits for the CodeActAgent to complete
3. Processes the history of actions and observations from the CodeActAgent
4. Stores the processed history in `state.extra_data['processed_history']`
5. Finishes when the CodeActAgent is done

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

## Future Enhancements

The Supervisor Agent could be extended to:

- Monitor the progress of delegated tasks in real-time
- Provide feedback or corrections during execution
- Delegate to different agents based on the task type
- Handle multiple delegations in sequence or parallel
- Implement retry mechanisms for failed tasks
- Optimize resource usage across multiple agents
- Analyze the processed history to verify correctness
- Generate summaries and insights from the execution history

## Usage

To use the Supervisor Agent, select it as your agent in the OpenHands interface or specify it in your configuration.

```python
from openhands.agenthub.supervisor_agent import SupervisorAgent
```

To access the processed history after execution:

```python
processed_history = state.extra_data.get('processed_history', '')
```
