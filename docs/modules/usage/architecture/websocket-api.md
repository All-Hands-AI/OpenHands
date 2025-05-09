---
sidebar_position: 5
---

# WebSocket API Reference

This document provides a technical reference for the OpenHands WebSocket API, including detailed information about the connection protocol, event types, and message formats.

## Socket.IO Implementation

OpenHands uses Socket.IO for WebSocket communication. The server is configured with the following options:

```python
sio = socketio.AsyncServer(
    async_mode='asgi', 
    cors_allowed_origins='*', 
    client_manager=client_manager  # Redis client manager if configured
)
```

## Connection Endpoint

The WebSocket connection endpoint is available at:

```
ws://your-openhands-server/socket.io/
```

or with TLS:

```
wss://your-openhands-server/socket.io/
```

## Connection Parameters

The following query parameters are required when connecting to the WebSocket:

| Parameter | Type | Description |
|-----------|------|-------------|
| `conversation_id` | string | The ID of the conversation to join |
| `latest_event_id` | integer | The ID of the latest event received (use `-1` for a new connection) |
| `providers_set` | string | (Optional) Comma-separated list of provider types (e.g., "github,gitlab") |

## Events

### Server Events

Events emitted by the server to clients:

| Event Name | Description |
|------------|-------------|
| `oh_event` | Emitted when an event occurs in the conversation |

### Client Events

Events that clients can emit to the server:

| Event Name | Description |
|------------|-------------|
| `oh_user_action` | Send a user action to the agent |

## Event Types

### User Message

A message from the user to the agent:

```json
{
  "type": "message",
  "source": "user",
  "message": "Hello, can you help me with my project?"
}
```

### Agent Message

A message from the agent to the user:

```json
{
  "id": "123",
  "type": "message",
  "source": "agent",
  "message": "I'd be happy to help with your project. What do you need assistance with?",
  "timestamp": "2025-05-09T12:34:56.789Z"
}
```

### Command Execution

An event representing a command execution:

```json
{
  "id": "124",
  "action": "run",
  "source": "agent",
  "args": {
    "command": "ls -la",
    "is_input": false
  },
  "result": {
    "output": "total 16\ndrwxr-xr-x  4 user  group  128 May  9 12:34 .\ndrwxr-xr-x  3 user  group   96 May  9 12:34 ..\n-rw-r--r--  1 user  group  123 May  9 12:34 file.txt\n",
    "exit_code": 0
  },
  "timestamp": "2025-05-09T12:35:00.000Z"
}
```

### File Edit

An event representing a file edit:

```json
{
  "id": "125",
  "action": "edit",
  "source": "agent",
  "args": {
    "path": "/workspace/project/file.txt",
    "old_str": "Original content",
    "new_str": "Updated content"
  },
  "timestamp": "2025-05-09T12:36:00.000Z"
}
```

### File Write

An event representing a file write:

```json
{
  "id": "126",
  "action": "write",
  "source": "agent",
  "args": {
    "path": "/workspace/project/new-file.txt",
    "content": "This is a new file"
  },
  "timestamp": "2025-05-09T12:37:00.000Z"
}
```

## Connection Lifecycle

### Connection

1. Client initiates a WebSocket connection with required query parameters
2. Server validates the conversation ID and user permissions
3. If validation succeeds, the server accepts the connection
4. Server replays events from the conversation starting from `latest_event_id + 1`

### Disconnection

The server handles disconnection in the following cases:

1. Client explicitly disconnects
2. Connection validation fails
3. Network issues cause the connection to drop

## Error Handling

The server may emit error events in the following cases:

1. Connection validation fails
2. Invalid action format
3. Server-side errors

Example error response:

```json
{
  "message": "Invalid action format",
  "data": {
    "msg_id": "ERROR$INVALID_ACTION_FORMAT"
  }
}
```

## Implementation Examples

### Python Client

```python
import socketio

# Create a Socket.IO client
sio = socketio.Client()

@sio.event
def connect():
    print("Connected to OpenHands WebSocket")

@sio.event
def disconnect():
    print("Disconnected from OpenHands WebSocket")

@sio.on("oh_event")
def on_event(data):
    print(f"Received event: {data}")

# Connect to the server
sio.connect(
    "http://your-openhands-server",
    transports=["websocket"],
    query={
        "conversation_id": "your-conversation-id",
        "latest_event_id": -1,
        "providers_set": "github,gitlab"
    }
)

# Send a user message
sio.emit("oh_user_action", {
    "type": "message",
    "source": "user",
    "message": "Hello, can you help me with my project?"
})

# Keep the connection alive
sio.wait()
```

### JavaScript Client

```javascript
import { io } from "socket.io-client";

// Create a Socket.IO client
const socket = io("http://your-openhands-server", {
  transports: ["websocket"],
  query: {
    conversation_id: "your-conversation-id",
    latest_event_id: -1,
    providers_set: "github,gitlab"
  }
});

// Connection events
socket.on("connect", () => {
  console.log("Connected to OpenHands WebSocket");
});

socket.on("disconnect", (reason) => {
  console.log("Disconnected:", reason);
});

socket.on("connect_error", (error) => {
  console.error("Connection error:", error);
});

// Receive events
socket.on("oh_event", (event) => {
  console.log("Received event:", event);
});

// Send a user message
socket.emit("oh_user_action", {
  type: "message",
  source: "user",
  message: "Hello, can you help me with my project?"
});
```

## Security Considerations

1. **Authentication**: Ensure that proper authentication is implemented to prevent unauthorized access to conversations.
2. **Input Validation**: Validate all user inputs to prevent injection attacks.
3. **Rate Limiting**: Implement rate limiting to prevent abuse of the WebSocket API.
4. **TLS**: Use TLS (wss://) in production environments to encrypt WebSocket traffic.

## Performance Considerations

1. **Event Batching**: Consider batching events when replaying large event streams to improve performance.
2. **Redis Integration**: For multi-server deployments, use Redis for Socket.IO client management.
3. **Connection Pooling**: Implement connection pooling to manage multiple client connections efficiently.