# Supervisor Agent

The Supervisor Agent is designed to delegate tasks to other agents and monitor their execution.

## Current Implementation

In its current implementation, the Supervisor Agent:

1. Delegates all tasks to the CodeActAgent
2. Waits for the CodeActAgent to complete
3. Finishes when the CodeActAgent is done

## Future Enhancements

The Supervisor Agent could be extended to:

- Monitor the progress of delegated tasks
- Provide feedback or corrections
- Delegate to different agents based on the task type
- Handle multiple delegations in sequence or parallel
- Implement retry mechanisms for failed tasks
- Optimize resource usage across multiple agents

## Usage

To use the Supervisor Agent, select it as your agent in the OpenHands interface or specify it in your configuration.

```python
from openhands.agenthub.supervisor_agent import SupervisorAgent
```
