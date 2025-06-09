# Memory Component

- Short Term History
- Memory Condenser

## Short Term History
- Short term history filters the event stream and computes the messages that are injected into the context
- It filters out certain events of no interest for the Agent, such as AgentChangeStateObservation or NullAction/NullObservation
- When the context window or the token limit set by the user is exceeded, history starts condensing: chunks of messages into summaries.
- Each summary is then injected into the context, in the place of the respective chunk it summarizes

## Memory Condenser
- Memory condenser is responsible for summarizing the chunks of events
- It summarizes the earlier events first
- It starts with the earliest agent actions and observations between two user messages
- Then it does the same for later chunks of events between user messages
- If there are no more agent events, it summarizes the user messages, this time one by one, if they're large enough and not immediately after an AgentFinishAction event (we assume those are tasks, potentially important)
- Summaries are retrieved from the LLM as AgentSummarizeAction, and are saved in State.
