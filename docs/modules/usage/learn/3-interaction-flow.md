# OpenHands Backend Interaction



### 1. Client Connection Flow
```plaintext
Client Connection Request
    │
    ▼
Socket.IO connect event (listen_socket.py)
    │
    ├─► Parse query parameters
    │   - Get conversation_id
    │   - Get latest_event_id
    │
    ├─► Validate user (if not OSS mode)
    │   - Check github_auth cookie
    │   - Decode JWT token
    │   - Verify user permissions
    │
    ├─► Load user settings
    │   - Get settings store
    │   - Load settings
    │
    └─► Join conversation
        │
        ├─► Create/Get Runtime
        │   - Initialize event stream
        │   - Setup runtime environment
        │   - Register event handlers
        │
        ├─► Initialize Agent
        │   - Create agent instance
        │   - Setup LLM
        │   - Register with event stream
        │
        └─► Start Processing
            - Begin event handling
            - Process messages
            - Execute actions
```

### 2. Event Processing Flow
```plaintext
Event Received
    │
    ▼
EventStream._process_queue
    │
    ├─► Get event from queue
    │
    └─► For each subscriber:
        │
        ├─► Get subscriber callbacks
        │
        ├─► Execute in thread pool
        │   - Run callback
        │   - Handle errors
        │
        └─► Process results
            - Update state
            - Generate responses
            - Store events
```

### 3. Runtime Action Flow
```plaintext
Action Event Received
    │
    ▼
Runtime.on_event
    │
    ├─► Validate action
    │   - Check runnable
    │   - Verify confirmation
    │   - Check capabilities
    │
    ├─► Execute action
    │   - Get handler
    │   - Run action
    │   - Generate observation
    │
    └─► Process result
        - Create observation
        - Add to event stream
        - Update state
```

### 4. Cleanup and Maintenance
```plaintext
Cleanup and Maintenance
   │
   ├─► Periodic Cleanup (_cleanup_stale)
   │   │
   │   ├─► Clean Detached Conversations
   │   │   └── Disconnect and remove
   │   │
   │   ├─► Check Inactive Sessions
   │   │   ├── Find sessions past close_delay
   │   │   └── Mark for closure
   │   │
   │   └─► Close Marked Sessions
   │       ├── Remove connection mappings
   │       ├── Close agent sessions
   │       └── Clear from storage
   │
   └─► Resource Management
       ├── Monitor active sessions
       ├── Track connection counts
       └── Manage memory usage
```