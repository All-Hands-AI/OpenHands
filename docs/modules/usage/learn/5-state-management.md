

## OpenHands State Management

### 1. Connection State
- Managed by StandaloneConversationManager
- Maps connection IDs to session IDs
- Tracks active and detached conversations
- Handles session cleanup

### 2. Conversation State
- Managed by Conversation class
- Maintains event stream
- Handles agent sessions
- Manages file storage

### 3. Session State
- Managed by Session class
- Tracks last active timestamp
- Manages agent initialization
- Handles message dispatch

### 4. Agent State
- Managed by agent session
- Processes actions
- Maintains conversation context
- Generates responses