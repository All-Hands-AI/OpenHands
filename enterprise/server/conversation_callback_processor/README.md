# Conversation Callback Processor

This module provides a framework for processing conversation events and sending summaries or notifications to external platforms like Slack and GitLab.

## Overview

The conversation callback processor system consists of two main components:

1. **ConversationCallback**: A database model that stores information about callbacks to be executed when specific conversation events occur.
2. **ConversationCallbackProcessor**: An abstract base class that defines the interface for processors that handle conversation events.

## How It Works

### ConversationCallback

The `ConversationCallback` class is a database model that stores:

- A reference to a conversation (`conversation_id`)
- The current status of the callback (`ACTIVE`, `COMPLETED`, or `ERROR`)
- The type of processor to use (`processor_type`)
- Serialized processor configuration (`processor_json`)
- Timestamps for creation and updates

This model provides methods to:
- `get_processor()`: Dynamically instantiate the processor from the stored type and JSON data
- `set_processor()`: Store a processor instance by serializing its type and data

### ConversationCallbackProcessor

The `ConversationCallbackProcessor` is an abstract base class that defines the interface for all callback processors. It:

- Is a Pydantic model that can be serialized to/from JSON
- Requires implementing the `__call__` method to process conversation events
- Receives the callback instance and an `AgentStateChangedObservation` when called

## Implemented Processors

### SlackCallbackProcessor

The `SlackCallbackProcessor` sends conversation summaries to Slack channels when specific agent state changes occur. It:

1. Monitors for agent state changes to `AWAITING_USER_INPUT` or `FINISHED`
2. Sends a summary instruction to the conversation if needed
3. Extracts a summary from the conversation
4. Sends the summary to the appropriate Slack channel
5. Marks the callback as completed

### GithubCallbackProcessor and GitlabCallbackProcessor

The `GithubCallbackProcessor` and `GitlabCallbackProcessor` send conversation summaries to GitHub / GitLab issues when specific agent state changes occur. They:

1. Monitors for agent state changes to `AWAITING_USER_INPUT` or `FINISHED`
2. Sends a summary instruction to the conversation if needed
3. Extracts a summary from the conversation
4. Sends the summary to the appropriate Github or GitLab issue
5. Marks the callback as completed
